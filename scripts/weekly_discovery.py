"""Fetch research metadata candidates for human review; never auto-publish.

Do not replace a previously useful queue when every upstream request fails.
"""
import csv
import argparse
import json
import pathlib
import time
import sys
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
COLUMNS = ["id", "title", "year", "doi", "cited_by_count", "source_query", "review_status"]


def discover(queries, get=requests.get, delay=0.2):
    rows = {}
    failures = []
    successful_requests = 0
    for query in queries:
        try:
            response = get("https://api.openalex.org/works", params={
                "search": query, "per-page": 20,
                "filter": "from_publication_date:2020-01-01",
            }, timeout=30, headers={"User-Agent": "EnglishLearningAtlas/0.5 (research metadata discovery; GitHub: WaleedTa/english-learning-atlas-cloud)"})
            response.raise_for_status()
            for work in response.json().get("results", []):
                wid = work.get("id", "")
                if not wid or not work.get("title"):
                    continue
                rows[wid] = {
                    "id": wid, "title": work["title"],
                    "year": work.get("publication_year", ""),
                    "doi": work.get("doi") or "",
                    "cited_by_count": work.get("cited_by_count", 0),
                    "source_query": query, "review_status": "pending",
                }
            successful_requests += 1
        except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
            failures.append(f"{query}: {exc}")
        if delay:
            time.sleep(delay)
    return rows, successful_requests, failures


def main(output=None, delay=0.2):
    policy = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))
    rows, successful_requests, failures = discover(policy["research_queries"], delay=delay)
    for failure in failures:
        print("Warning:", failure, file=sys.stderr)
    if not successful_requests or not rows:
        print("Discovery produced no usable records; preserving existing queue.", file=sys.stderr)
        return 1
    out = pathlib.Path(output) if output is not None else ROOT / "review_queue/openalex_candidates.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    temporary = out.with_suffix(".csv.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(sorted(rows.values(), key=lambda r: r["id"]))
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(rows)} candidate records to {out}; {len(failures)} request failures")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", help="Optional CSV destination for diagnostics")
    parser.add_argument("--delay", type=float, default=0.2)
    args = parser.parse_args()
    raise SystemExit(main(args.output, max(0, args.delay)))
