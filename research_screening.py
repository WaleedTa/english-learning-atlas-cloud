"""Deterministic, auditable screening primitives; not an automated systematic review."""
from dataclasses import dataclass
import re
from urllib.parse import urlsplit, urlunsplit


def _norm(value):
    return " ".join((value or "").casefold().split())


def canonical_doi(doi):
    value = _norm(doi).removeprefix("https://doi.org/").removeprefix("http://dx.doi.org/").removeprefix("doi:").strip()
    return value if re.fullmatch(r"10\.\d{4,9}/\S+", value) else None


def record_key(row):
    """Conservative keys: DOI first, else source URL, else title + publication year."""
    doi = canonical_doi(row.get("doi"))
    if doi:
        return "doi:" + doi
    url = row.get("url") or ""
    parsed = urlsplit(url)
    if parsed.scheme == "https" and parsed.hostname:
        return "url:" + urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/") or "/", "", ""))
    title = _norm(row.get("title"))
    year = row.get("year")
    if title and isinstance(year, int) and 1900 <= year <= 2100:
        return f"title-year:{title}:{year}"
    return None  # Ambiguous metadata should not be merged automatically.


def deduplicate(records):
    unique, duplicates, seen = [], [], {}
    for index, row in enumerate(records):
        key = record_key(row)
        if key is not None and key in seen:
            duplicates.append({"index": index, "duplicate_of": seen[key], "key": key})
        else:
            unique.append(row)
            if key is not None:
                seen[key] = index
    return unique, duplicates


@dataclass(frozen=True)
class ScreeningProtocol:
    question_id: str
    inclusion_criteria: tuple
    exclusion_criteria: tuple
    registered_at: str

    def validate(self):
        if not self.question_id.strip() or not self.registered_at.strip():
            raise ValueError("question identifier and protocol registration required")
        if not self.inclusion_criteria or not self.exclusion_criteria:
            raise ValueError("predefined inclusion and exclusion criteria required")


@dataclass(frozen=True)
class ScreeningDecision:
    record_id: str
    reviewer_id: str
    decision: str
    reason: str
    stage: str = "title_abstract"

    def validate(self):
        if self.decision not in {"include", "exclude", "uncertain"}:
            raise ValueError("invalid screening decision")
        if self.stage not in {"title_abstract", "full_text"}:
            raise ValueError("invalid screening stage")
        if not self.record_id.strip() or not self.reviewer_id.strip() or not self.reason.strip():
            raise ValueError("record, reviewer, and reason required")


def reconcile(decisions):
    """Never auto-resolve conflicts; missing a second reviewer is explicitly flagged."""
    by_record = {}
    for item in decisions:
        item.validate()
        key = (item.record_id, item.stage)
        by_record.setdefault(key, {})
        if item.reviewer_id in by_record[key]:
            raise ValueError("duplicate reviewer decision")
        by_record[key][item.reviewer_id] = item.decision
    output = {}
    for key, votes in by_record.items():
        if len(votes) < 2:
            status = "awaiting_second_reviewer"
        elif len(set(votes.values())) > 1 or "uncertain" in votes.values():
            status = "requires_adjudication"
        else:
            status = next(iter(votes.values()))
        output[key] = status
    return output


def screening_metrics(gold, predictions):
    """Benchmark on a fixed adjudicated binary set; not evidence of real-world recall."""
    if not gold or set(gold) != set(predictions):
        raise ValueError("nonempty identical reference and prediction IDs required")
    if any(value not in (True, False) for value in list(gold.values()) + list(predictions.values())):
        raise ValueError("binary labels required")
    tp = sum(gold[k] and predictions[k] for k in gold)
    fp = sum(not gold[k] and predictions[k] for k in gold)
    fn = sum(gold[k] and not predictions[k] for k in gold)
    return {"true_positive": tp, "false_positive": fp, "false_negative": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "n": len(gold)}


def prisma_counts(identified, duplicates, screened, excluded, full_text_sought,
                 full_text_not_retrieved, full_text_excluded, included):
    """Validate a subset of PRISMA counts; does not claim PRISMA compliance."""
    values = locals()
    if any(type(value) is not int or value < 0 for value in values.values()):
        raise ValueError("all counts must be nonnegative integers")
    if identified - duplicates != screened:
        raise ValueError("identified minus duplicates must equal screened")
    if screened - excluded != full_text_sought:
        raise ValueError("screened minus excluded must equal reports sought")
    if full_text_sought - full_text_not_retrieved - full_text_excluded != included:
        raise ValueError("reports sought must reconcile to included")
    return values
