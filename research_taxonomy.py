"""Bilingual, deterministic taxonomy for preliminary research discovery tags.

Discovery tags come from metadata heuristics, not independent verification.
Unknown terms remain visible and are never silently assigned to a category.
No external network calls or model inference.
"""
from collections import Counter, defaultdict

TAXONOMY = {
    "skills": {
        "listening": ("الاستماع", "Listening"),
        "speaking": ("التحدث", "Speaking"),
        "reading": ("القراءة", "Reading"),
        "writing": ("الكتابة", "Writing"),
        "grammar": ("القواعد", "Grammar"),
        "vocabulary": ("المفردات", "Vocabulary"),
        "pronunciation": ("النطق", "Pronunciation"),
        "assessment": ("التقييم والاختبارات", "Assessment"),
    },
    "methods": {
        "computer_assisted": ("التعلم بمساعدة الحاسوب", "Computer-assisted learning"),
        "mobile_assisted": ("التعلم بمساعدة الهاتف", "Mobile-assisted learning"),
        "spaced_repetition": ("التكرار المتباعد", "Spaced repetition"),
        "task_based": ("التعلم القائم على المهام", "Task-based learning"),
        "communicative": ("التعلم التواصلي", "Communicative learning"),
        "gamification": ("التلعيب", "Gamification"),
        "immersive": ("التعلم الغامر", "Immersive learning"),
        "blended": ("التعلم المدمج", "Blended learning"),
        "flipped": ("الصف المعكوس", "Flipped classroom"),
        "ai_assisted": ("التعلم بمساعدة الذكاء الاصطناعي", "AI-assisted learning"),
    },
    "frameworks": {
        "CEFR": ("الإطار الأوروبي المرجعي المشترك", "Common European Framework (CEFR)"),
        "ACTFL": ("إطار ACTFL", "ACTFL proficiency guidelines"),
    },
}

ALIASES = {
    "skills": {"oral": "speaking", "lexical": "vocabulary"},
    "methods": {"mall": "mobile_assisted", "call": "computer_assisted",
                "task_based_learning": "task_based", "flipped_classroom": "flipped"},
    "frameworks": {"cefr": "CEFR", "actfl": "ACTFL"},
}

def normalize_tag(kind, tag):
    if not isinstance(tag, str):
        return ""
    raw = tag.strip()
    lookup = raw.casefold().replace("-", "_").replace(" ", "_")
    keys = {key.casefold(): key for key in TAXONOMY.get(kind, {})}
    return ALIASES.get(kind, {}).get(lookup, keys.get(lookup, raw))

def tags_for(discovery, kind):
    values = discovery.get(kind) or []
    if not isinstance(values, list):
        return []
    return list(dict.fromkeys(normalize_tag(kind, value)
                              for value in values if isinstance(value, str) and value.strip()))

def label(kind, tag, lang="ar"):
    pair = TAXONOMY.get(kind, {}).get(tag)
    return pair[0 if lang == "ar" else 1] if pair else tag

def tag_inventory(discoveries, kind):
    counts = Counter(tag for discovery in discoveries for tag in tags_for(discovery, kind))
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))

def compare_review_groups(discoveries, reviews):
    """Group human assessments by shared preliminary skill/method tags.

    Diverging outcome directions trigger a review signal, never a causal claim.
    Each review is counted once per group, even if it has multiple source tags.
    """
    indexed = {d.get("id"): d for d in discoveries}
    groups = defaultdict(list)
    for review in reviews:
        discovery = indexed.get(review.get("discovery_id"))
        if not discovery:
            continue
        skills = tags_for(discovery, "skills") or ["unclassified"]
        methods = tags_for(discovery, "methods") or ["unclassified"]
        for method in methods:
            for skill in skills:
                groups[(method, skill)].append(review)
    output = []
    for (method, skill), entries in groups.items():
        directions = {e.get("outcome_direction", "not_assessed") for e in entries}
        assessed = directions - {"not_assessed", "not_applicable"}
        output.append({
            "method": method,
            "skill": skill,
            "count": len(entries),
            "quality_high": sum(e.get("evidence_quality") == "high" for e in entries),
            "verified": sum(bool(e.get("source_checked")) for e in entries),
            "signal": ("insufficient" if len(entries) < 2 else
                       "divergent" if len(assessed) > 1 else
                       "insufficient" if not assessed else "consistent_recorded"),
        })
    return sorted(output, key=lambda x: (-x["count"], x["method"], x["skill"]))
