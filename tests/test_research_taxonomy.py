"""Deterministic taxonomy checks. Run: python -m unittest discover -s tests."""
import unittest
from research_taxonomy import normalize_tag, tags_for, label, tag_inventory, compare_review_groups

class ResearchTaxonomyTests(unittest.TestCase):
    def test_aliases_and_bilingual_labels(self):
        self.assertEqual(normalize_tag("methods", "MALL"), "mobile_assisted")
        self.assertEqual(normalize_tag("frameworks", "cefr"), "CEFR")
        self.assertEqual(label("skills", "reading", "ar"), "القراءة")
        self.assertEqual(label("skills", "reading", "en"), "Reading")

    def test_unknown_metadata_is_not_silently_classified(self):
        self.assertEqual(normalize_tag("methods", "new_method"), "new_method")
        self.assertEqual(tags_for({"skills": ["reading", "Reading", "vocabulary"]}, "skills"),
                         ["reading", "vocabulary"])

    def test_grouping_requires_multiple_reviews(self):
        discoveries = [{"id": "1", "skills": ["reading"], "methods": ["MALL"]}]
        reviews = [{"discovery_id": "1", "outcome_direction": "positive",
                    "evidence_quality": "moderate", "source_checked": True}]
        groups = compare_review_groups(discoveries, reviews)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["method"], "mobile_assisted")
        self.assertEqual(groups[0]["signal"], "insufficient")
        self.assertEqual(groups[0]["count"], 1)

    def test_different_recorded_directions_are_review_signal_only(self):
        discoveries = [{"id": i, "skills": ["reading"], "methods": ["MALL"]} for i in ("1", "2")]
        reviews = [{"discovery_id": "1", "outcome_direction": "positive"},
                   {"discovery_id": "2", "outcome_direction": "negative"}]
        groups = compare_review_groups(discoveries, reviews)
        self.assertEqual(groups[0]["signal"], "divergent")
        self.assertEqual(groups[0]["count"], 2)

    def test_inventory_deduplicates_aliases_per_discovery(self):
        data = [{"skills": ["reading", "Reading"]}, {"skills": ["reading"]}]
        self.assertEqual(tag_inventory(data, "skills"), [("reading", 2)])

if __name__ == "__main__":
    unittest.main()
