"""Regression tests for the database client; do not use live credentials."""
import unittest
from unittest.mock import patch

from atlas_supabase import AtlasClient


class AtlasClientTests(unittest.TestCase):
    def setUp(self):
        self.client = AtlasClient("https://example.supabase.co", "sb_publishable_test")

    def test_evidence_review_lookup_uses_discovery_id(self):
        with patch.object(self.client, "_request", return_value=[{"discovery_id": "abc"}]) as request:
            self.assertEqual(self.client.get_evidence_review("abc", "jwt")["discovery_id"], "abc")
        self.assertEqual(request.call_args.kwargs["params"]["discovery_id"], "eq.abc")

    def test_missing_evidence_review_returns_none(self):
        with patch.object(self.client, "_request", return_value=[]):
            self.assertIsNone(self.client.get_evidence_review("missing", "jwt"))

    def test_import_discovery_handles_untrusted_classification_values(self):
        record = {"record_id": "item1", "title": "An English study", "url": "https://example.org/study",
                  "classification": {"skills": "speaking", "methods": ["task_based", 42], "frameworks": None}}
        calls = []

        def fake_request(method, path, **kwargs):
            calls.append((method, path, kwargs))
            return []

        with patch.object(self.client, "_request", side_effect=fake_request):
            self.assertEqual(self.client.import_discoveries([record], "jwt"), 1)
        payload = calls[-1][2]["payload"][0]
        self.assertEqual(payload["skills"], [])
        self.assertEqual(payload["methods"], ["task_based"])
        self.assertEqual(payload["frameworks"], [])
        self.assertEqual(payload["review_status"], "pending")


if __name__ == "__main__":
    unittest.main()
