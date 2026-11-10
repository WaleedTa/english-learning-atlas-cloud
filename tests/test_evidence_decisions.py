import unittest

from evidence_decisions import EvidenceItem, ResearchQuestion, evaluate_decision


def question():
    return ResearchQuestion("Arabic-speaking adult learners", "a2", "speaking", "AI conversation practice", "teacher-led practice", "independent speaking fluency assessment")


def source(direction="positive", status="verified"):
    return EvidenceItem("https://example.edu/study", "p. 12, table 3", "randomized_trial", "adult language learners", "speaking fluency", direction, "small sample", "reviewer-1", status)


class DecisionGateTests(unittest.TestCase):
    def test_question_must_have_outcome_and_level(self):
        q = ResearchQuestion("adults", "a9", "speaking", "AI practice", "usual classes", "")
        self.assertEqual(evaluate_decision(q, [source()])["status"], "invalid_question")

    def test_unreviewed_cannot_support_decision(self):
        self.assertEqual(evaluate_decision(question(), [source(status="pending")])["status"], "insufficient_evidence")

    def test_missing_locator_cannot_support_decision(self):
        item = source()
        item = EvidenceItem(item.source_url, "", item.study_design, item.population, item.outcome, item.direction, item.limitations, item.reviewed_by, item.review_status)
        self.assertEqual(evaluate_decision(question(), [item])["verified_sources"], 0)

    def test_conflicting_findings_flagged(self):
        self.assertEqual(evaluate_decision(question(), [source("positive"), source("negative")])["status"], "conflicting_evidence")

    def test_even_positive_verified_studies_are_not_automatically_recommended(self):
        self.assertEqual(evaluate_decision(question(), [source()])["status"], "requires_expert_synthesis")

    def test_verified_without_reviewer_is_invalid(self):
        item = source()
        item = EvidenceItem(item.source_url, item.source_locator, item.study_design, item.population, item.outcome, item.direction, item.limitations, "", "verified")
        self.assertIn("verified evidence requires a human reviewer", item.errors())


if __name__ == "__main__":
    unittest.main()
