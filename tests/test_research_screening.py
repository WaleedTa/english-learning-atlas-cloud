import unittest

from research_screening import (ScreeningDecision, ScreeningProtocol, canonical_doi,
                                deduplicate, reconcile, screening_metrics, prisma_counts)


class ScreeningTests(unittest.TestCase):
    def test_doi_normalization(self):
        self.assertEqual(canonical_doi("https://doi.org/10.1234/ABC"), "10.1234/abc")

    def test_deduplicate_doi(self):
        rows = [{"doi": "10.1234/ABC", "title": "A"}, {"doi": "https://doi.org/10.1234/abc", "title": "B"}]
        unique, dup = deduplicate(rows)
        self.assertEqual((len(unique), len(dup)), (1, 1))

    def test_ambiguous_records_not_auto_merged(self):
        unique, dup = deduplicate([{"title": "Untitled"}, {"title": "Untitled"}])
        self.assertEqual((len(unique), len(dup)), (2, 0))

    def test_protocol_requires_explicit_criteria(self):
        with self.assertRaises(ValueError):
            ScreeningProtocol("Q1", (), ("wrong population",), "2026-11-10").validate()

    def test_second_reviewer_needed(self):
        item = ScreeningDecision("W1", "alice", "include", "matches population")
        self.assertEqual(reconcile([item])[("W1", "title_abstract")], "awaiting_second_reviewer")

    def test_disagreement_requires_adjudication(self):
        items = [ScreeningDecision("W1", "alice", "include", "fits"), ScreeningDecision("W1", "bob", "exclude", "design differs")]
        self.assertEqual(reconcile(items)[("W1", "title_abstract")], "requires_adjudication")

    def test_agreement_is_recorded(self):
        items = [ScreeningDecision("W1", "alice", "exclude", "wrong group"), ScreeningDecision("W1", "bob", "exclude", "wrong group")]
        self.assertEqual(reconcile(items)[("W1", "title_abstract")], "exclude")

    def test_metrics_not_invented(self):
        metrics = screening_metrics({"a": True, "b": True, "c": False}, {"a": True, "b": False, "c": True})
        self.assertAlmostEqual(metrics["precision"], .5)
        self.assertAlmostEqual(metrics["recall"], .5)

    def test_metrics_reject_mismatched_set(self):
        with self.assertRaises(ValueError):
            screening_metrics({"a": True}, {"b": True})

    def test_prisma_counts_reconcile(self):
        self.assertEqual(prisma_counts(12, 2, 10, 4, 6, 1, 2, 3)["included"], 3)

    def test_prisma_counts_reject_inconsistency(self):
        with self.assertRaises(ValueError):
            prisma_counts(12, 2, 10, 4, 6, 1, 2, 5)


if __name__ == "__main__":
    unittest.main()
