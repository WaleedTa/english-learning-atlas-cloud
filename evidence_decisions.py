"""Offline decision gate for research recommendations; no model-generated scores.

This module deliberately refuses conclusions unsupported by inspected evidence.
It is a foundation for review workflows, not a validated systematic review engine.
"""
from dataclasses import dataclass
from urllib.parse import urlparse


SKILLS = frozenset({"listening", "speaking", "reading", "writing", "grammar", "vocabulary", "pronunciation", "assessment"})
LEVELS = frozenset({"pre_a1", "a1", "a2", "b1", "b2", "c1", "c2"})
DESIGNS = frozenset({"randomized_trial", "quasi_experiment", "observational", "systematic_review", "meta_analysis", "qualitative", "descriptive", "other"})


@dataclass(frozen=True)
class ResearchQuestion:
    population: str
    level: str
    skill: str
    intervention: str
    comparator: str
    outcome: str

    def errors(self):
        issues = []
        for field in ("population", "intervention", "comparator", "outcome"):
            if len(getattr(self, field).strip()) < 5:
                issues.append(f"{field} must be specific")
        if self.level not in LEVELS:
            issues.append("unsupported CEFR level")
        if self.skill not in SKILLS:
            issues.append("unsupported skill")
        return issues


@dataclass(frozen=True)
class EvidenceItem:
    source_url: str
    source_locator: str
    study_design: str
    population: str
    outcome: str
    direction: str
    limitations: str
    reviewed_by: str
    review_status: str

    def errors(self):
        issues = []
        parsed = urlparse(self.source_url)
        if parsed.scheme != "https" or not parsed.hostname:
            issues.append("source must be HTTPS")
        if not self.source_locator.strip():
            issues.append("source location or page required")
        if self.study_design not in DESIGNS:
            issues.append("unknown study design")
        if self.direction not in {"positive", "neutral", "negative", "mixed", "unclear"}:
            issues.append("unknown outcome direction")
        if not self.population.strip() or not self.outcome.strip():
            issues.append("population and outcome required")
        if not self.limitations.strip():
            issues.append("limitations must be documented")
        if self.review_status not in {"pending", "verified", "disputed", "rejected"}:
            issues.append("invalid review status")
        if self.review_status == "verified" and not self.reviewed_by.strip():
            issues.append("verified evidence requires a human reviewer")
        return issues


def evaluate_decision(question, evidence):
    """Return a transparent gate, not a ranking or scientific effect estimate."""
    problems = question.errors()
    if problems:
        return {"status": "invalid_question", "reasons": problems, "verified_sources": 0}
    accepted = [item for item in evidence if not item.errors() and item.review_status == "verified"]
    rejected = len(evidence) - len(accepted)
    if not accepted:
        return {"status": "insufficient_evidence", "reasons": ["no human-verified cited studies"], "verified_sources": 0, "unusable_sources": rejected}
    directions = {item.direction for item in accepted}
    if "mixed" in directions or "unclear" in directions or ("positive" in directions and "negative" in directions):
        return {"status": "conflicting_evidence", "reasons": ["outcome directions conflict or remain uncertain; expert synthesis required"], "verified_sources": len(accepted), "unusable_sources": rejected}
    return {"status": "requires_expert_synthesis", "reasons": ["verified sources exist, but causality, bias and effect sizes have not been synthesized"], "verified_sources": len(accepted), "unusable_sources": rejected}
