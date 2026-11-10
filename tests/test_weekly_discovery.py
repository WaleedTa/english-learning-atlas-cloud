"""Offline tests for weekly discovery safeguards."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

import requests

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "weekly_discovery.py"
spec = importlib.util.spec_from_file_location("weekly_discovery", SCRIPT)
weekly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weekly)


class FakeResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"results": [{"id": "https://openalex.org/W123", "title": "Pronunciation learning",
                             "publication_year": 2024, "cited_by_count": 12}]}


class WeeklyDiscoveryTests(unittest.TestCase):
    def test_successful_discovery_keeps_pending_records(self):
        records, successes, failures = weekly.discover(["pronunciation"], get=lambda *a, **kw: FakeResponse(), delay=0)
        self.assertEqual((successes, failures), (1, []))
        self.assertEqual(records["https://openalex.org/W123"]["review_status"], "pending")

    def test_total_upstream_failure_does_not_overwrite_queue(self):
        def fail(*args, **kwargs):
            raise requests.ConnectionError("offline")
        records, successes, failures = weekly.discover(["pronunciation"], get=fail, delay=0)
        self.assertEqual(records, {})
        self.assertEqual(successes, 0)
        self.assertEqual(len(failures), 1)
        with patch.object(weekly, "discover", return_value=(records, successes, failures)):
            self.assertEqual(weekly.main(), 1)


if __name__ == "__main__":
    unittest.main()
