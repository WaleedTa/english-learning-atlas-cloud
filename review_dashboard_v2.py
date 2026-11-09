"""Research review workspace. Decisions stay in the browser session until exported."""
import csv
import io
import json
from pathlib import Path
from urllib.parse import urlparse
import streamlit as st

ROOT = Path(__file__).resolve().parent
policy = json.loads((ROOT / "config/policy.json").read_text(encoding="utf-8"))
st.set_page_config(page_title="English Learning Atlas Cloud", page_icon="🌐", layout="wide")
st.title("🌐 English Learning Atlas Cloud")
st.caption("مساحة اكتشاف الأبحاث ومراجعتها | Research discovery and human review")
st.warning("النتائج بيانات وصفية مرشحة، وليست أدلة مثبتة على فعالية أي أسلوب تعليمي. قرارات المراجعة مؤقتة حتى تصدّرها وتحفظها.")
a, b, c = st.columns(3)
a.metric("دورية البحث", "أسبوعياً")
b.metric("نطاق المصادر المستهدف", "جميع الفئات")
c.metric("سياسة الاعتماد", "مراجعة بشرية")
st.info("المصدر الآلي المتصل حالياً: OpenAlex فقط. بقية المصادر ضمن خطة التوسع.")

@st.cache_data
def load_candidates():
    path = ROOT / "review_queue/openalex_candidates.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

rows = load_candidates()
if "reviews" not in st.session_state:
    st.session_state.reviews = {}

def valid_url(url):
    parsed = urlparse(url or "")
    return parsed.scheme == "https" and parsed.netloc.lower() in {"doi.org", "www.doi.org", "openalex.org"}

def export_reviews():
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=["id", "decision", "evidence_quality", "relevance", "notes"])
    writer.writeheader()
    for key, value in sorted(st.session_state.reviews.items()):
        writer.writerow({"id": key, **value})
    return buffer.getvalue().encode("utf-8-sig")

tab1, tab2, tab3 = st.tabs(["🔎 البحث والفهرسة", "🧪 المراجعة العلمية", "⚙️ الإدارة"])
with tab1:
    if not rows:
        st.warning("لم تصل بيانات البحث بعد. شغّل GitHub Actions وادمج طلب النتائج بعد فحصه.")
    else:
        years = sorted({str(r.get("year", "")) for r in rows if r.get("year")}, reverse=True)
        col1, col2, col3 = st.columns([3, 1, 1])
        q = col1.text_input("ابحث في العنوان أو DOI أو موضوع البحث")
        year = col2.selectbox("السنة", ["الكل"] + years)
        order = col3.selectbox("الترتيب", ["الأحدث", "الأكثر استشهاداً", "العنوان"])
        filtered = [r for r in rows if q.casefold() in " ".join([r.get("title", ""), r.get("doi", ""), r.get("source_query", "")]).casefold() and (year == "الكل" or r.get("year") == year)]
        if order == "الأحدث":
            filtered.sort(key=lambda r: int(r.get("year") or 0), reverse=True)
        elif order == "الأكثر استشهاداً":
            filtered.sort(key=lambda r: int(r.get("cited_by_count") or 0), reverse=True)
        else:
            filtered.sort(key=lambda r: r.get("title", "").casefold())
        st.metric("نتائج البحث", len(filtered))
        st.dataframe(filtered, use_container_width=True, hide_index=True)
        st.caption("عدد الاستشهادات مؤشر انتشار فقط، وليس تقييماً لجودة الدراسة أو فعاليتها.")

with tab2:
    if rows:
        lookup = {r["id"]: r for r in rows}
        options = list(lookup)
        selected = st.selectbox("اختر دراسة لمراجعتها", options, format_func=lambda key: (lookup[key].get("title") or key)[:130])
        record = lookup[selected]
        st.subheader(record.get("title") or "بدون عنوان")
        st.write(f"**السنة:** {record.get('year', '—')} · **الاستشهادات:** {record.get('cited_by_count', '—')}")
        st.write(f"**عبارة الاكتشاف:** {record.get('source_query', '—')}")
        doi = record.get("doi", "")
        if valid_url(doi):
            st.link_button("فتح DOI الأصلي", doi)
        if valid_url(selected):
            st.link_button("فتح سجل OpenAlex", selected)
        st.markdown("#### بطاقة تقييم الدراسة")
        current = st.session_state.reviews.get(selected, {})
        decision_options = ["pending", "needs_full_text", "accepted", "rejected"]
        quality_options = ["not_assessed", "low", "moderate", "high"]
        relevance_options = ["not_assessed", "low", "medium", "high"]
        with st.form("review_form"):
            decision = st.selectbox("قرار المراجعة", decision_options, index=decision_options.index(current.get("decision", "pending")))
            quality = st.selectbox("جودة الأدلة (تقييم بشري)", quality_options, index=quality_options.index(current.get("evidence_quality", "not_assessed")))
            relevance = st.selectbox("صلة الدراسة بالمشروع", relevance_options, index=relevance_options.index(current.get("relevance", "not_assessed")))
            notes = st.text_area("ملاحظات ومبررات القرار، المنهج، العينة، النتائج والقيود", value=current.get("notes", ""))
            submitted = st.form_submit_button("حفظ القرار في الجلسة")
        if submitted:
            if decision == "accepted" and (quality == "not_assessed" or relevance == "not_assessed" or not notes.strip()):
                st.error("للقبول، قيّم جودة الأدلة والصلة بالمشروع وأضف مبرراً مكتوباً.")
            else:
                st.session_state.reviews[selected] = {
                    "decision": decision, "evidence_quality": quality,
                    "relevance": relevance, "notes": notes.strip()
                }
                st.success("حُفظ القرار مؤقتاً في هذه الجلسة. صدّر ملف المراجعات للاحتفاظ به.")
        st.caption("القبول هنا قرار مراجعة بشرية أولي، ولا ينشر ادعاء علمياً أو يعدّل قاعدة البيانات تلقائياً.")

with tab3:
    st.subheader("إدارة قرارات المراجعة")
    st.metric("القرارات المحفوظة في هذه الجلسة", len(st.session_state.reviews))
    st.download_button("⬇️ تنزيل ملف قرارات المراجعة CSV", data=export_reviews(), file_name="atlas_review_decisions.csv", mime="text/csv", disabled=not st.session_state.reviews)
    uploaded = st.file_uploader("استيراد قرارات سابقة (CSV)", type=["csv"])
    if uploaded is not None and st.button("استيراد القرارات"):
        try:
            content = uploaded.getvalue().decode("utf-8-sig")
            parsed = list(csv.DictReader(io.StringIO(content)))
            known = {r["id"] for r in rows}
            allowed = {"pending", "needs_full_text", "accepted", "rejected"}
            count = 0
            for item in parsed:
                if item.get("id") not in known or item.get("decision") not in allowed:
                    continue
                st.session_state.reviews[item["id"]] = {
                    "decision": item["decision"],
                    "evidence_quality": item.get("evidence_quality", "not_assessed"),
                    "relevance": item.get("relevance", "not_assessed"),
                    "notes": item.get("notes", ""),
                }
                count += 1
            st.success(f"تم استيراد {count} قراراً.")
        except (UnicodeDecodeError, csv.Error) as exc:
            st.error(f"تعذر قراءة الملف: {exc}")
    st.divider()
    st.markdown("**تخزين القرارات:** لا توجد حالياً قاعدة بيانات دائمة أو تسجيل دخول. لا تدخل معلومات شخصية حساسة. احفظ ملف CSV قبل مغادرة الصفحة.")
    st.markdown("**التحديثات:** كل يوم اثنين 09:00 بتوقيت بغداد، أو يدوياً عبر GitHub Actions.")
    st.json(policy)
