"""Supabase REST client using publishable key and end-user JWT; no service-role key."""
import requests
from urllib.parse import urlparse

class AtlasAPIError(Exception):
    pass

class AtlasClient:
    def __init__(self, url, anon_key):
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".supabase.co"):
            raise AtlasAPIError("Invalid Supabase project URL")
        self.url = url.rstrip("/")
        self.key = anon_key

    def _request(self, method, path, token=None, params=None, payload=None, prefer=None):
        headers = {"apikey": self.key}
        if token:
            headers["Authorization"] = "Bearer " + token
        elif not self.key.startswith("sb_publishable_"):
            headers["Authorization"] = "Bearer " + self.key
        if prefer:
            headers["Prefer"] = prefer
        try:
            response = requests.request(method, self.url + path, headers=headers,
                                        params=params, json=payload, timeout=25)
        except requests.RequestException as exc:
            raise AtlasAPIError("Unable to reach Supabase") from exc
        if not response.ok:
            raise AtlasAPIError("Supabase request failed (HTTP %s): %s" % (response.status_code, response.text[:220]))
        return response.json() if response.content else []

    def login(self, email, password):
        return self._request("POST", "/auth/v1/token?grant_type=password",
                             payload={"email": email, "password": password})

    def list_resources(self, token=None, status=None, limit=500):
        params = {"select": "id,title,year,doi,source_query,cited_by_count,review_status,evidence_quality,relevance,reviewed_at",
                  "order": "created_at.desc", "limit": str(limit)}
        if status:
            params["review_status"] = "eq." + status
        rows = self._request("GET", "/rest/v1/atlas_resources", token=token, params=params)
        if token and rows:
            # Private notes live in a separate RLS-protected table.
            details = self._request("GET", "/rest/v1/atlas_review_details", token=token,
                                    params={"select": "resource_id,review_notes"})
            notes = {r["resource_id"]: r.get("review_notes", "") for r in details}
            for row in rows:
                row["review_notes"] = notes.get(row["id"], "")
        return rows

    def upsert_candidates(self, rows, token):
        existing = {r["id"] for r in self.list_resources(token=token, limit=10000)}
        payload = []
        for r in rows:
            if r.get("id") in existing or not r.get("id") or not r.get("title"):
                continue
            try:
                year = int(r["year"]) if r.get("year") else None
                citations = max(0, int(r.get("cited_by_count") or 0))
            except (ValueError, TypeError):
                continue
            payload.append({"id": r["id"], "title": r["title"][:1500],
                            "year": year, "doi": r.get("doi", ""),
                            "source_query": r.get("source_query", ""),
                            "cited_by_count": citations, "review_status": "pending"})
        count = 0
        for offset in range(0, len(payload), 100):
            batch = payload[offset:offset + 100]
            self._request("POST", "/rest/v1/atlas_resources", token=token,
                          payload=batch, prefer="return=minimal")
            count += len(batch)
        return count

    def review(self, resource_id, token, user_id, status, quality, relevance, notes):
        if status == "approved" and (quality == "not_assessed" or
                                     relevance == "not_assessed" or not notes.strip()):
            raise AtlasAPIError("Approval requires a documented human assessment")
        return self._request("POST", "/rest/v1/rpc/atlas_review_resource", token=token,
                             payload={"p_id": resource_id, "p_status": status,
                                      "p_quality": quality, "p_relevance": relevance,
                                      "p_notes": notes.strip()})

    def list_discoveries(self, token=None, limit=1000):
        return self._request("GET", "/rest/v1/atlas_discoveries", token=token,
                             params={"select": "id,title,source,kind,url,year,doi,skills,methods,frameworks,evidence_status,review_status,limitations",
                                     "order": "created_at.desc", "limit": str(limit)})

    def import_discoveries(self, records, token):
        if len(records) > 3000:
            raise AtlasAPIError("Maximum 3000 records per import")
        existing = {r["id"] for r in self._request("GET", "/rest/v1/atlas_discoveries",
                   token=token, params={"select": "id", "limit": "10000"})}
        pending = []
        for record in records:
            rid = record.get("record_id")
            if not isinstance(rid, str) or not rid or rid in existing:
                continue
            title, url = record.get("title"), record.get("url")
            if not isinstance(title, str) or not isinstance(url, str) or not url.startswith("https://"):
                continue
            classification = record.get("classification") or {}
            if not isinstance(classification, dict):
                classification = {}
            tags = {k: [str(v)[:100] for v in (classification.get(k) or [])[:20]]
                    for k in ("skills", "methods", "frameworks")}
            pending.append({
                "id": rid[:128], "source": str(record.get("source") or "unknown")[:100],
                "title": title[:1500], "url": url[:2000],
                "doi": str(record.get("doi") or "")[:500],
                "year": int(record["year"]) if str(record.get("year") or "").isdigit() else None,
                "kind": str(record.get("kind") or "research")[:100],
                "authors": str(record.get("authors") or "")[:1200],
                "abstract": str(record.get("abstract") or "")[:4000],
                "citation_count": int(record["citations"]) if str(record.get("citations") or "").isdigit() else None,
                "search_query": str(record.get("query") or "")[:500],
                "skills": tags["skills"], "methods": tags["methods"], "frameworks": tags["frameworks"],
                "evidence_status": "unassessed", "review_status": "pending",
                "limitations": str(record.get("limitations") or "Metadata only")[:1000],
            })
            existing.add(rid)
        for start in range(0, len(pending), 50):
            self._request("POST", "/rest/v1/atlas_discoveries", token=token,
                          payload=pending[start:start + 50], prefer="return=minimal")
        return len(pending)

    def get_evidence_review(self, discovery_id, token):
        rows = self._request("GET", "/rest/v1/atlas_evidence_reviews", token=token,
                             params={"select": "*", "discovery_id": "eq." + discovery_id, "limit": "1"})
        return rows[0] if rows else None

    def save_evidence_review(self, discovery_id, reviewer_id, token, fields):
        allowed = ("study_design", "evidence_quality", "outcome_direction", "learner_population",
                   "intervention", "comparator", "outcomes", "effect_size", "limitations",
                   "source_checked", "review_notes")
        payload = {"discovery_id": discovery_id, "reviewer_id": reviewer_id}
        for field in allowed:
            if field in fields:
                payload[field] = fields[field] if field == "source_checked" else str(fields[field])[:4000]
        return self._request("POST", "/rest/v1/atlas_evidence_reviews", token=token,
                             params={"on_conflict": "discovery_id"}, payload=payload,
                             prefer="resolution=merge-duplicates,return=minimal")

    def list_evidence_reviews(self, token, limit=2000):
        """Private reviewed evidence only; Supabase RLS enforces admin access."""
        return self._request("GET", "/rest/v1/atlas_evidence_reviews", token=token,
                             params={"select": "discovery_id,study_design,evidence_quality,outcome_direction,learner_population,intervention,comparator,outcomes,effect_size,limitations,source_checked,review_notes,updated_at",
                                     "order": "updated_at.desc", "limit": str(limit)})

    def list_source_registry(self, token, limit=1000):
        """Private registry; Supabase RLS checks admin privileges."""
        return self._request("GET", "/rest/v1/atlas_source_registry", token=token,
                             params={"select": "id,name,url,category,language,access_status,collection_method,evidence_class,notes,approved_for_automation,created_at",
                                     "order": "created_at.desc", "limit": str(limit)})

    def create_registry_source(self, token, user_id, fields):
        """Register a candidate source. No automated collection is enabled."""
        from urllib.parse import urlparse
        name = str(fields.get("name") or "").strip()
        url = str(fields.get("url") or "").strip()
        parsed = urlparse(url)
        if not 2 <= len(name) <= 200 or parsed.scheme != "https" or not parsed.hostname:
            raise AtlasAPIError("A source name and valid HTTPS URL are required")
        allowed = ("category", "language", "access_status", "collection_method",
                   "evidence_class", "notes")
        payload = {"name": name, "url": url, "created_by": user_id,
                   "approved_for_automation": False}
        for key in allowed:
            if key in fields:
                payload[key] = str(fields[key])[:1500 if key == "notes" else 100]
        return self._request("POST", "/rest/v1/atlas_source_registry", token=token,
                             payload=payload, prefer="return=minimal")
