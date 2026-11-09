import csv
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
policy = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))
st.set_page_config(page_title="English Learning Atlas Cloud", page_icon="🌐", layout="wide")
st.title("🌐 English Learning Atlas Cloud")
st.caption("Research discovery and review dashboard · Initial cloud edition")
a, b, c = st.columns(3)
a.metric("Update cadence", "Weekly")
b.metric("Source scope", "Global / All categories")
c.metric("Approval policy", "Human review")
st.info("OpenAlex is the only automated source currently implemented. Other sources are planned; results are not verified scientific conclusions.")
st.subheader("Research candidates awaiting review")
path = ROOT / "review_queue/openalex_candidates.csv"
if path.exists():
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    query = st.text_input("Search title or DOI")
    filtered = [r for r in rows if query.lower() in (r["title"] + " " + r["doi"]).lower()]
    st.write(f"{len(filtered)} candidates")
    st.dataframe(filtered, use_container_width=True, hide_index=True)
else:
    st.warning("No discovery queue yet. Run the GitHub Actions workflow manually or wait for the scheduled run.")
st.subheader("Configuration")
st.json(policy)
st.markdown("**Review workflow:** Open the GitHub pull request created by weekly discovery, verify each source, and merge only after review.")
