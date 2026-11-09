"""Fetch research metadata candidates for human review; never auto-publish."""
import csv
import json
import pathlib
import time
import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
policy = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))
out = ROOT / "review_queue/openalex_candidates.csv"
out.parent.mkdir(parents=True, exist_ok=True)
rows = {}
for query in policy["research_queries"]:
    try:
        response = requests.get("https://api.openalex.org/works", params={
            "search": query, "per-page": 20,
            "filter": "from_publication_date:2020-01-01",
        }, timeout=30, headers={"User-Agent": "EnglishLearningAtlas/0.2 (research metadata discovery)"})
        response.raise_for_status()
        for work in response.json().get("results", []):
            wid = work.get("id", "")
            if not wid:
                continue
            rows[wid] = {
                "id": wid, "title": work.get("title", ""),
                "year": work.get("publication_year", ""),
                "doi": work.get("doi") or "",
                "cited_by_count": work.get("cited_by_count", 0),
                "source_query": query, "review_status": "pending",
            }
    except (requests.RequestException, ValueError) as exc:
        print(f"Warning: {query}: {exc}")
    time.sleep(0.2)
columns = ["id", "title", "year", "doi", "cited_by_count", "source_query", "review_status"]
with out.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=columns)
    writer.writeheader()
    writer.writerows(sorted(rows.values(), key=lambda r: r["id"]))
print(f"Wrote {len(rows)} candidate records to {out}")
