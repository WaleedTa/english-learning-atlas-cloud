import unittest

from evidence_decisions import ResearchQuestion
from evidence_synthesis import StudyFinding, DecisionRecord, map_evidence, draft_decision


def q():
    return ResearchQuestion("Arabic-speaking adults", "a2", "speaking", "AI guided dialogue", "teacher conversation", "speaking fluency test")


def finding(study_id="w1", direction="positive", status="verified", **kw):
    values = dict(study_id=study_id, source_url="https://example.edu/paper", source_locator="p. 7", outcome="speaking fluency test", direction=direction,
                  population="Arabic-speaking adults", level="a2", skill="speaking", limitations="small sample", review_status=status,
                  reviewer_id="reviewer-1", applicability="direct", applicability_reason="matching language and proficiency")
    values.update(kw)
    return StudyFinding(**values)


class SynthesisTests(unittest.TestCase):
    def test_verified_positive_is_not_a_conclusion(self):
        result = map_evidence(q(), [finding()])
        self.assertEqual(result["status"], "expert_synthesis_required")
        self.assertEqual((result["certainty"], result["effect_estimate"], result["decision"]), ("not_assessed", None, "not_authorized"))

    def test_opposing_directions_flagged(self):
        result = map_evidence(q(), [finding(), finding("w2", "negative")])
        self.assertEqual(result["status"], "conflicting_or_uncertain")
        self.assertEqual(result["direction_counts"]["negative"], 1)

    def test_unreviewed_source_excluded(self):
        result = map_evidence(q(), [finding(status="pending")])
        self.assertEqual(result["status"], "no_eligible_verified_evidence")
        self.assertEqual(len(result["excluded_studies"]), 1)

    def test_mismatched_outcome_is_excluded(self):
        result = map_evidence(q(), [finding(outcome="vocabulary quiz")])
        self.assertEqual(len(result["included_studies"]), 0)

    def test_duplicate_id_not_double_counted(self):
        result = map_evidence(q(), [finding(), finding()])
        self.assertEqual(len(result["included_studies"]), 1)
        self.assertEqual(len(result["excluded_studies"]), 1)

    def test_applicability_reason_mandatory(self):
        self.assertIn("applicability requires explanation", finding(applicability_reason="").errors())

    def test_pending_unknown_applicability_retained_but_visible(self):
        result = map_evidence(q(), [finding(applicability="not_assessed", applicability_reason="")])
        self.assertEqual(result["applicability_counts"]["not_assessed"], 1)

    def test_decision_draft_has_no_approval(self):
        decision = draft_decision("Q1", "v1", "pilot", "limited evidence", "small sample and opposite study")
        self.assertEqual(decision.status, "draft")

    def test_approved_decision_requires_review(self):
        item = DecisionRecord("Q1", "v1", "adopt", "some rationale", "some counterevidence", "", "", "approved")
        self.assertIn("approved decision requires identified human reviewer and date", item.validate())

    def test_missing_counterevidence_reason_rejected(self):
        with self.assertRaises(ValueError):
            draft_decision("Q1", "v1", "pilot", "positive studies", "")


if __name__ == "__main__":
    unittest.main()
