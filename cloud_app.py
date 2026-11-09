"""Public catalog and private Supabase moderation console."""
import csv
import io
import streamlit as st
from atlas_supabase import AtlasClient, AtlasAPIError

st.set_page_config(page_title="English Learning Atlas Cloud", page_icon="🌐", layout="wide")
st.title("🌐 English Learning Atlas Cloud")
st.caption("أطلس عالمي لتعليم الإنجليزية | مكتبة عامة ومراجعة بشرية خاصة")
st.info("المصدر الآلي الحالي OpenAlex فقط. القبول يعني مراجعة بشرية مسجلة، وليس إثبات فعالية علمية تلقائياً.")

try:
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")
except Exception:
    url, key = "", ""
if not url or not key:
    st.warning("لم تُضبط قاعدة البيانات بعد. أكمل تعليمات PHASE3_SETUP.md في GitHub وأضف مفاتيح Supabase العامة إلى Streamlit Secrets.")
    st.stop()
try:
    api = AtlasClient(url, key)
except AtlasAPIError as exc:
    st.error(str(exc))
    st.stop()

public_tab, admin_tab = st.tabs(["📚 الأطلس العام", "🔐 إدارة ومراجعة خاصة"])
with public_tab:
    st.subheader("المصادر المعتمدة للنشر")
    try:
        published = api.list_resources(status="approved")
        query = st.text_input("ابحث في المصادر المنشورة")
        visible = [r for r in published if query.casefold() in (r.get("title", "") + " " + (r.get("source_query") or "")).casefold()]
        st.metric("مصادر منشورة", len(published))
        st.dataframe(visible, width='stretch', hide_index=True,
                     column_config={"id": st.column_config.LinkColumn("OpenAlex"), "doi": st.column_config.LinkColumn("DOI")})
        if not published:
            st.info("لا توجد أبحاث معتمدة للنشر حتى الآن. الأبحاث المرشحة لا تظهر للعامة.")
    except AtlasAPIError as exc:
        st.error(str(exc))

with admin_tab:
    if "atlas_session" not in st.session_state:
        st.session_state.atlas_session = None
    if not st.session_state.atlas_session:
        with st.form("admin_login"):
            email = st.text_input("البريد الإلكتروني للمدير")
            password = st.text_input("كلمة المرور", type="password")
            sign_in = st.form_submit_button("تسجيل الدخول")
        if sign_in:
            try:
                session = api.login(email, password)
                if not session.get("access_token") or not session.get("user", {}).get("id"):
                    raise AtlasAPIError("No valid user session returned")
                st.session_state.atlas_session = session
                st.rerun()
            except AtlasAPIError as exc:
                st.error(str(exc))
        st.caption("لا يكفي امتلاك حساب Supabase للدخول إلى بيانات الإدارة؛ يجب إدراج UUID في atlas_admins.")
    else:
        session = st.session_state.atlas_session
        token = session["access_token"]
        user_id = session["user"]["id"]
        if st.button("تسجيل الخروج"):
            st.session_state.atlas_session = None
            st.rerun()
        try:
            all_rows = api.list_resources(token=token, limit=10000)
            st.metric("جميع السجلات المتاحة لهذا الحساب", len(all_rows))
            st.caption("إذا لم تكن مديرا مسجلاً فسترى السجلات العامة فقط، ولن تتمكن من تعديلها.")
            st.subheader("استيراد مرشحات البحث")
            upload = st.file_uploader("ارفع ملف CSV الناتج من GitHub Actions", type=["csv"])
            if upload is not None and st.button("استيراد كمرشحات غير منشورة"):
                try:
                    candidate_rows = list(csv.DictReader(io.StringIO(upload.getvalue().decode("utf-8-sig"))))
                    count = api.upsert_candidates(candidate_rows, token)
                    st.success(f"تم استيراد {count} سجلاً بحالة pending، دون نشر تلقائي.")
                    st.rerun()
                except (UnicodeDecodeError, csv.Error, AtlasAPIError) as exc:
                    st.error(str(exc))
            st.subheader("مراجعة سجل")
            if all_rows:
                options = {r["id"]: r for r in all_rows}
                selected = st.selectbox("الدراسة", list(options), format_func=lambda k: (options[k].get("title") or k)[:110])
                item = options[selected]
                st.write("**العنوان:**", item["title"])
                st.write("**الحالة:**", item["review_status"])
                if item.get("doi"):
                    st.write("**DOI:**", item["doi"])
                statuses = ["pending", "needs_full_text", "approved", "rejected"]
                qualities = ["not_assessed", "low", "moderate", "high"]
                relevances = ["not_assessed", "low", "medium", "high"]
                with st.form("review_record"):
                    status = st.selectbox("القرار", statuses, index=statuses.index(item["review_status"]))
                    quality = st.selectbox("قوة الأدلة", qualities, index=qualities.index(item["evidence_quality"]))
                    relevance = st.selectbox("صلة الدراسة", relevances, index=relevances.index(item["relevance"]))
                    notes = st.text_area("مبررات القرار والمنهج والقيود", value=item.get("review_notes") or "")
                    save = st.form_submit_button("حفظ المراجعة في قاعدة البيانات")
                if save:
                    try:
                        api.review(selected, token, user_id, status, quality, relevance, notes)
                        st.success("تم حفظ المراجعة بصورة دائمة.")
                        st.rerun()
                    except AtlasAPIError as exc:
                        st.error(str(exc))
        except AtlasAPIError as exc:
            st.error("تعذر تحميل البيانات أو انتهت صلاحية الجلسة: " + str(exc))
            st.caption("سجل الخروج وأعد الدخول إذا انتهت صلاحية الرمز.")
