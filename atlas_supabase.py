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
