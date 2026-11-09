"""Supabase REST client using user JWT; never a service-role credential."""
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
        headers = {"apikey": self.key, "Authorization": "Bearer " + (token or self.key)}
        if prefer:
            headers["Prefer"] = prefer
        try:
            response = requests.request(method, self.url + path, headers=headers, params=params, json=payload, timeout=25)
        except requests.RequestException as exc:
            raise AtlasAPIError("Unable to reach Supabase") from exc
        if not response.ok:
            raise AtlasAPIError("Supabase request failed (HTTP %s): %s" % (response.status_code, response.text[:250]))
        return response.json() if response.content else []

    def login(self, email, password):
        return self._request("POST", "/auth/v1/token?grant_type=password", payload={"email": email, "password": password})

    def list_resources(self, token=None, status=None, limit=500):
        params = {"select": "id,title,year,doi,source_query,cited_by_count,review_status,evidence_quality,relevance,review_notes,reviewed_at", "order": "created_at.desc", "limit": str(limit)}
        if status:
            params["review_status"] = "eq." + status
        return self._request("GET", "/rest/v1/atlas_resources", token=token, params=params)

    def upsert_candidates(self, rows, token):
        # Existing reviewed records must never be overwritten by a CSV import.
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
            payload.append({"id": r["id"], "title": r["title"][:1500], "year": year, "doi": r.get("doi", ""),
                            "source_query": r.get("source_query", ""), "cited_by_count": citations,
                            "review_status": "pending"})
        count = 0
        for offset in range(0, len(payload), 100):
            batch = payload[offset:offset + 100]
            self._request("POST", "/rest/v1/atlas_resources", token=token, payload=batch, prefer="return=minimal")
            count += len(batch)
        return count

    def review(self, resource_id, token, user_id, status, quality, relevance, notes):
        if status == "approved" and (quality == "not_assessed" or relevance == "not_assessed" or not notes.strip()):
            raise AtlasAPIError("Approval requires evidence assessment, relevance, and written justification")
        payload = {"review_status": status, "evidence_quality": quality, "relevance": relevance,
                   "review_notes": notes.strip(), "reviewed_by": user_id, "reviewed_at": "now()"}
        # PostgREST does not evaluate now() as a SQL function in JSON: use UTC timestamp.
        from datetime import datetime, timezone
        payload["reviewed_at"] = datetime.now(timezone.utc).isoformat()
        return self._request("PATCH", "/rest/v1/atlas_resources", token=token,
                             params={"id": "eq." + resource_id}, payload=payload, prefer="return=representation")
