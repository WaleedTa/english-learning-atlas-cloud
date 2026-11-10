"""Conservative evidence map for Phase 9C; no unsupervised certainty or effect estimates."""
from dataclasses import dataclass
from urllib.parse import urlsplit


@dataclass(frozen=True)
class StudyFinding:
    study_id: str
    source_url: str
    source_locator: str
    outcome: str
    direction: str
    population: str
    level: str
    skill: str
    limitations: str
    review_status: str
    reviewer_id: str
    applicability: str = "not_assessed"
    applicability_reason: str = ""

    def errors(self):
        issues = []
        if not self.study_id.strip():
            issues.append("study ID required")
        url = urlsplit(self.source_url)
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            issues.append("valid HTTPS evidence URL required")
        for field in ("source_locator", "outcome", "population", "level", "skill", "limitations"):
            if not getattr(self, field).strip():
                issues.append(field + " required")
        if self.direction not in {"positive", "negative", "neutral", "mixed", "unclear"}:
            issues.append("invalid direction")
        if self.review_status not in {"pending", "verified", "disputed", "rejected"}:
            issues.append("invalid review status")
        if self.review_status == "verified" and not self.reviewer_id.strip():
            issues.append("human reviewer required")
        if self.applicability not in {"direct", "partial", "unclear", "not_applicable", "not_assessed"}:
            issues.append("invalid applicability")
        if self.applicability != "not_assessed" and not self.applicability_reason.strip():
            issues.append("applicability requires explanation")
        return issues


def map_evidence(question, studies):
    """Build a traceable descriptive map, not a pooled treatment-effect estimate."""
    problems = question.errors()
    if problems:
        return {"status": "invalid_question", "reasons": problems}
    accepted, excluded = [], []
    seen = set()
    for study in studies:
        errors = study.errors()
        if study.study_id in seen:
            excluded.append({"id": study.study_id, "reason": "duplicate study ID; manual reconciliation required"})
        elif errors:
            excluded.append({"id": study.study_id, "reason": "; ".join(errors)})
        elif study.review_status != "verified":
            excluded.append({"id": study.study_id, "reason": "not human-verified"})
        elif study.skill != question.skill or study.level != question.level or study.outcome.casefold().strip() != question.outcome.casefold().strip():
            excluded.append({"id": study.study_id, "reason": "question mismatch; applicability requires review"})
        else:
            accepted.append(study)
        seen.add(study.study_id)

    directions = {label: sum(s.direction == label for s in accepted) for label in ("positive", "negative", "neutral", "mixed", "unclear")}
    conflicting = directions["mixed"] > 0 or directions["unclear"] > 0 or (directions["positive"] > 0 and directions["negative"] > 0)
    applicability = {label: sum(s.applicability == label for s in accepted) for label in ("direct", "partial", "unclear", "not_applicable", "not_assessed")}
    status = "no_eligible_verified_evidence" if not accepted else ("conflicting_or_uncertain" if conflicting else "expert_synthesis_required")
    return {
        "status": status, "question": {"population": question.population, "level": question.level, "skill": question.skill, "outcome": question.outcome},
        "included_studies": [{"id": s.study_id, "url": s.source_url, "locator": s.source_locator, "direction": s.direction,
                               "population": s.population, "limitations": s.limitations, "applicability": s.applicability,
                               "applicability_reason": s.applicability_reason} for s in accepted],
        "excluded_studies": excluded, "direction_counts": directions, "applicability_counts": applicability,
        "certainty": "not_assessed", "effect_estimate": None,
        "decision": "not_authorized", "caveat": "Direction counts are descriptive; they cannot establish effectiveness or causal impact."
    }


@dataclass(frozen=True)
class DecisionRecord:
    question_id: str
    synthesis_version: str
    recommendation: str
    rationale: str
    counterevidence: str
    reviewer_id: str
    reviewed_at: str
    status: str = "draft"

    def validate(self):
        issues = []
        for field in ("question_id", "synthesis_version", "rationale", "counterevidence"):
            if not getattr(self, field).strip():
                issues.append(field + " required")
        if self.status not in {"draft", "approved", "rejected", "superseded"}:
            issues.append("invalid decision status")
        if self.recommendation not in {"adopt", "pilot", "defer", "reject"}:
            issues.append("invalid recommendation")
        if self.status == "approved" and (not self.reviewer_id.strip() or not self.reviewed_at.strip()):
            issues.append("approved decision requires identified human reviewer and date")
        return issues


def draft_decision(question_id, synthesis_version, recommendation, rationale, counterevidence):
    """Automation can only create a draft; approval must occur in reviewed workflow."""
    record = DecisionRecord(question_id, synthesis_version, recommendation, rationale, counterevidence, "", "")
    errors = record.validate()
    if errors:
        raise ValueError("; ".join(errors))
    return record
