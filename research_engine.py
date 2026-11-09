"""Phase 4 discovery: metadata only, source provenance, no automatic efficacy claims.

Run: python research_engine.py --output research_output
No API credentials needed for public endpoints. Each source may rate-limit or change.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, time
from datetime import datetime, timezone
from urllib.parse import urlparse
import requests

USER_AGENT = "EnglishLearningAtlas/0.4 (research metadata; contact via GitHub WaleedTa/english-learning-atlas-cloud)"
S = requests.Session()
S.headers.update({"User-Agent": USER_AGENT, "Accept": "application/json"})
QUERIES = [
    "second language acquisition", "English language learning", "English pronunciation training",
    "spaced repetition vocabulary learning", "extensive reading English language",
    "computer assisted language learning", "English listening comprehension",
    "English speaking feedback", "English writing instruction",
    "English language assessment", "task based language teaching",
    "English language learning mobile apps", "English language learning motivation",
]
SKILLS = {
    "listening": ["listening", "audio", "comprehension"],
    "speaking": ["speaking", "oral", "conversation", "fluency"],
    "reading": ["reading", "literacy"],
    "writing": ["writing", "composition"],
    "vocabulary": ["vocabulary", "lexical", "word learning"],
    "grammar": ["grammar", "syntax"],
    "pronunciation": ["pronunciation", "phonetic", "accent"],
    "assessment": ["assessment", "testing", "proficiency"],
}
METHODS = {
    "spaced_repetition": ["spaced repetition", "retrieval practice"],
    "extensive_reading": ["extensive reading"],
    "task_based": ["task based", "task-based"],
    "communicative": ["communicative language teaching"],
    "computer_assisted": ["computer assisted", "computer-assisted", "call"],
    "mobile_assisted": ["mobile assisted", "mobile-assisted", "mall"],
    "ai_feedback": ["artificial intelligence", "chatbot", "automated feedback"],
}
FRAMEWORKS = {
    "CEFR": ["cefr", "common european framework"],
    "ACTFL": ["actfl", "proficiency guidelines"],
    "ILR": ["interagency language roundtable", "ilr scale"],
    "GSE": ["global scale of english"],
    "CLB": ["canadian language benchmarks"],
    "IELTS": ["ielts"],
    "TOEFL": ["toefl"],
    "Cambridge English Scale": ["cambridge english scale"],
    "PTE": ["pte academic", "pearson test of english"],
}
SOURCE_CATALOG = [
    ("CEFR Companion Volume", "framework", "https://www.coe.int/en/web/common-european-framework-reference-languages", "Council of Europe"),
    ("ACTFL Proficiency Guidelines", "framework", "https://www.actfl.org/educator-resources/actfl-proficiency-guidelines", "ACTFL"),
    ("ILR Skill Level Descriptions", "framework", "https://www.govtilr.org/Skills/ILRscale1.htm", "ILR"),
    ("Global Scale of English", "framework", "https://www.pearson.com/languages/why-pearson/the-global-scale-of-english.html", "Pearson"),
    ("Canadian Language Benchmarks", "framework", "https://www.language.ca/resourcesexpertise/on-clb/", "CCLB"),
    ("ERIC", "research_index", "https://eric.ed.gov/", "US Department of Education"),
    ("OpenAlex", "research_index", "https://openalex.org/", "OpenAlex"),
    ("Crossref", "research_index", "https://www.crossref.org/", "Crossref"),
    ("Europe PMC", "research_index", "https://europepmc.org/", "Europe PMC"),
    ("British Council LearnEnglish", "learning_platform", "https://learnenglish.britishcouncil.org/", "British Council"),
    ("BBC Learning English", "learning_platform", "https://www.bbc.co.uk/learningenglish", "BBC"),
    ("Cambridge English", "learning_platform", "https://www.cambridgeenglish.org/", "Cambridge"),
    ("Duolingo", "learning_app", "https://www.duolingo.com/", "Duolingo"),
    ("Busuu", "learning_app", "https://www.busuu.com/", "Busuu"),
    ("Anki", "learning_software", "https://apps.ankiweb.net/", "Anki"),
    ("Language Learning Stack Exchange", "community", "https://languagelearning.stackexchange.com/", "Stack Exchange"),
    ("r/languagelearning", "community", "https://www.reddit.com/r/languagelearning/", "Reddit"),
    ("Hugging Face language models", "open_source", "https://huggingface.co/models", "Hugging Face"),
    ("GitHub language learning projects", "open_source", "https://github.com/topics/language-learning", "GitHub"),
]
def fetch(url, params):
    try:
        r = S.get(url, params=params, timeout=18)
        if r.status_code in (429, 500, 502, 503, 504):
            raise RuntimeError("HTTP " + str(r.status_code))
        r.raise_for_status()
        return r.json(), None
    except (requests.RequestException, ValueError, RuntimeError) as exc:
        return None, str(exc)[:220]

def clean(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()

def classify(title, abstract=""):
    t = (title + " " + abstract).lower()
    return {
        "skills": [k for k, terms in SKILLS.items() if any(term in t for term in terms)],
        "methods": [k for k, terms in METHODS.items() if any(term in t for term in terms)],
        "frameworks": [k for k, terms in FRAMEWORKS.items() if any(term in t for term in terms)],
    }

def make_record(source, title, url, year=None, doi=None, abstract="", authors="", citations=None, query=""):
    title = clean(title)
    doi = (doi or "").strip().lower().replace("https://doi.org/", "")
    if not title or not url or urlparse(url).scheme not in ("https", "http"):
        return None
    canonical = "doi:" + doi if doi else source + ":" + url.split("#")[0].rstrip("/")
    return {
        "record_id": hashlib.sha256(canonical.encode()).hexdigest()[:24],
        "source": source, "title": title[:1500], "url": url, "year": year,
        "doi": doi, "authors": clean(authors)[:1200], "abstract": clean(abstract)[:4000],
        "citations": citations, "query": query, "kind": "research",
        "classification": classify(title, abstract),
        "evidence_status": "unassessed", "review_status": "pending",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "limitations": "Metadata only; relevance and efficacy have not been verified.",
    }

def openalex(query, limit):
    data, err = fetch("https://api.openalex.org/works", {"search": query, "per-page": limit})
    if err: return [], err
    out = []
    for w in data.get("results", []):
        abstract = ""
        inverted = w.get("abstract_inverted_index") or {}
        if inverted:
            positions = [(p, word) for word, ps in inverted.items() for p in ps]
            abstract = " ".join(word for _, word in sorted(positions))
        authors = ", ".join(a.get("author", {}).get("display_name", "") for a in w.get("authorships", [])[:8])
        out.append(make_record("OpenAlex", w.get("display_name"), w.get("id"), w.get("publication_year"),
                               w.get("doi"), abstract, authors, w.get("cited_by_count"), query))
    return [x for x in out if x], None

def crossref(query, limit):
    data, err = fetch("https://api.crossref.org/works", {"query.bibliographic": query, "rows": limit,
                        "select": "DOI,title,URL,published,author,abstract,is-referenced-by-count"})
    if err: return [], err
    out = []
    for w in data.get("message", {}).get("items", []):
        parts = (w.get("published") or {}).get("date-parts", [[]])
        year = parts[0][0] if parts and parts[0] else None
        authors = ", ".join((a.get("given", "") + " " + a.get("family", "")).strip() for a in w.get("author", [])[:8])
        out.append(make_record("Crossref", " ".join(w.get("title") or []), w.get("URL"), year,
                               w.get("DOI"), w.get("abstract", ""), authors,
                               w.get("is-referenced-by-count"), query))
    return [x for x in out if x], None

def europe_pmc(query, limit):
    data, err = fetch("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                      {"query": query, "format": "json", "pageSize": limit, "resultType": "core"})
    if err: return [], err
    out = []
    for w in data.get("resultList", {}).get("result", []):
        url = "https://europepmc.org/article/" + str(w.get("source", "MED")) + "/" + str(w.get("id", ""))
        out.append(make_record("Europe PMC", w.get("title"), url, w.get("pubYear"),
                               w.get("doi"), w.get("abstractText", ""), w.get("authorString", ""), None, query))
    return [x for x in out if x], None

def catalog():
    result = []
    for name, kind, url, owner in SOURCE_CATALOG:
        result.append({"record_id": hashlib.sha256(url.encode()).hexdigest()[:24], "source": "Curated catalog",
                       "title": name, "url": url, "year": None, "doi": "", "authors": owner,
                       "abstract": "", "citations": None, "query": "", "kind": kind,
                       "classification": classify(name), "evidence_status": "unassessed",
                       "review_status": "pending", "retrieved_at": datetime.now(timezone.utc).isoformat(),
                       "limitations": "Directory entry, not independently verified or a claim of effectiveness."})
    return result

def run(output, per_query, delay):
    os.makedirs(output, exist_ok=True)
    records, errors, coverage = {}, [], []
    for query in QUERIES:
        for name, adapter in (("OpenAlex", openalex), ("Crossref", crossref), ("Europe PMC", europe_pmc)):
            found, error = adapter(query, per_query)
            coverage.append({"source": name, "query": query, "count": len(found), "error": error or ""})
            if error: errors.append({"source": name, "query": query, "error": error})
            for item in found:
                key = "doi:" + item["doi"] if item["doi"] else item["record_id"]
                if key not in records: records[key] = item
            time.sleep(delay)
    for item in catalog():
        records.setdefault(item["record_id"], item)
    with open(os.path.join(output, "candidates.jsonl"), "w", encoding="utf-8") as f:
        for item in records.values(): f.write(json.dumps(item, ensure_ascii=False) + "\n")
    with open(os.path.join(output, "coverage.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source", "query", "count", "error"])
        w.writeheader(); w.writerows(coverage)
    with open(os.path.join(output, "run_report.json"), "w", encoding="utf-8") as f:
        json.dump({"records": len(records), "requests": len(coverage), "failures": errors,
                   "disclaimer": "Automated discovery, not scientific validation"}, f, ensure_ascii=False, indent=2)
    print("Discovered", len(records), "candidates;", len(errors), "source failures")
    return 0 if len(errors) < len(coverage) else 2

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="research_output")
    p.add_argument("--per-query", type=int, default=8)
    p.add_argument("--delay", type=float, default=0.5)
    a = p.parse_args()
    raise SystemExit(run(a.output, max(1, min(a.per_query, 25)), max(a.delay, 0.2)))
