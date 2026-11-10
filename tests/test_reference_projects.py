"""Catalog safety and integrity checks without Supabase or network dependencies."""
import copy
import json
from pathlib import Path
import unittest

from scripts.validate_reference_projects import validate_catalog

CATALOG = Path(__file__).resolve().parents[1] / "data" / "reference_projects.json"


class ReferenceCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CATALOG.read_text(encoding="utf-8"))

    def test_catalog_has_fifteen_valid_citations(self):
        self.assertEqual(validate_catalog(self.data), [])
        self.assertEqual(len(self.data["projects"]), 15)

    def test_duplicate_project_is_rejected(self):
        altered = copy.deepcopy(self.data)
        altered["projects"].append(copy.deepcopy(altered["projects"][0]))
        self.assertTrue(any("duplicate" in e for e in validate_catalog(altered)))

    def test_insecure_source_is_rejected(self):
        altered = copy.deepcopy(self.data)
        altered["projects"][0]["url"] = "http://malicious.example/test"
        self.assertTrue(any("URL" in e for e in validate_catalog(altered)))

    def test_unreviewed_outcome_is_rejected(self):
        altered = copy.deepcopy(self.data)
        altered["projects"][0]["learning_effectiveness"] = 99
        self.assertTrue(any("outcomes" in e for e in validate_catalog(altered)))

    def test_explicit_non_endorsement_required(self):
        altered = copy.deepcopy(self.data)
        altered["catalog_status"] = "approved"
        self.assertTrue(validate_catalog(altered))


if __name__ == "__main__":
    unittest.main()
