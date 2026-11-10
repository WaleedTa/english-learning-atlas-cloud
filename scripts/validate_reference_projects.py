"""Validate an offline candidate catalog. Never publishes or imports records."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


DEFAULT = Path(__file__).resolve().parents[1] / "data" / "reference_projects.json"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_catalog(payload):
    errors = []
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return ["Unsupported catalog schema"]
    if payload.get("catalog_status") != "research_candidates_not_endorsed":
        errors.append("Catalog must explicitly remain unendorsed")
    records = payload.get("projects")
    if not isinstance(records, list):
        return errors + ["projects must be a list"]
    seen_slugs, seen_urls = set(), set()
    for i, row in enumerate(records):
        if not isinstance(row, dict):
            errors.append(f"projects[{i}] must be an object")
            continue
        slug, url = row.get("slug"), row.get("url")
        if not isinstance(slug, str) or not SLUG.fullmatch(slug):
            errors.append(f"projects[{i}]: invalid slug")
        elif slug in seen_slugs:
            errors.append(f"projects[{i}]: duplicate slug")
        seen_slugs.add(slug)
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != "https" or parsed.hostname != "github.com" or len(parsed.path.strip('/').split('/')) != 2:
            errors.append(f"projects[{i}]: expected HTTPS GitHub repository URL")
        elif url.lower() in seen_urls:
            errors.append(f"projects[{i}]: duplicate URL")
        if isinstance(url, str):
            seen_urls.add(url.lower())
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            errors.append(f"projects[{i}]: missing name")
        if not isinstance(row.get("focus"), list) or not row["focus"] or not all(isinstance(x, str) and x for x in row["focus"]):
            errors.append(f"projects[{i}]: invalid focus tags")
        if not isinstance(row.get("license"), str) or not row["license"]:
            errors.append(f"projects[{i}]: missing license status")
        if "rating" in row or "learning_effectiveness" in row or "approved" in row:
            errors.append(f"projects[{i}]: unreviewed catalog cannot claim outcomes/approval")
    return errors


def main(path=DEFAULT):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate_catalog(payload)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Validated {len(payload['projects'])} candidate projects (not published)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT))
