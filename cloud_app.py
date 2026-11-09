"""Public catalog and private Supabase moderation console."""
import csv
import io
import json
import zipfile
import streamlit as st
from atlas_supabase import AtlasClient, AtlasAPIError

st.set_page_config(page_title="English Learning Atlas Cloud", page_icon="🌐", layout="wide")
st.title("🌐 English Learning Atlas Cloud")
st.caption("أطلس عالمي لتعليم الإنجليزية | مكتبة عامة ومراجعة بشرية خاصة")
st.info("المصادر الآلية: OpenAlex وCrossref وEurope PMC. البيانات المكتشفة أولية وليست إثباتاً علمياً للفعالية.")

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
            st.subheader("اكتشافات المرحلة الرابعة")
            st.caption("ارفع ZIP الناتج من GitHub Actions، وستُحفظ السجلات بحالة pending فقط.")
            discovery_zip = st.file_uploader("ملف phase4-research-candidates.zip", type=["zip"], key="phase4_zip")
            if discovery_zip is not None and st.button("استيراد اكتشافات المرحلة الرابعة دون نشر"):
                try:
                    if discovery_zip.size > 15 * 1024 * 1024:
                        raise ValueError("الملف أكبر من الحد المسموح")
                    with zipfile.ZipFile(io.BytesIO(discovery_zip.getvalue())) as archive:
                        files = [n for n in archive.namelist() if n.split("/")[-1] == "candidates.jsonl"]
                        if len(files) != 1:
                            raise ValueError("لم يُعثر على candidates.jsonl واحد داخل الأرشيف")
                        info = archive.getinfo(files[0])
                        if info.file_size > 12 * 1024 * 1024:
                            raise ValueError("حجم بيانات الأرشيف غير مسموح")
                        records = [json.loads(line) for line in archive.read(files[0]).decode("utf-8").splitlines() if line.strip()]
                    count = api.import_discoveries(records, token)
                    st.success(f"تم حفظ {count} اكتشافاً جديداً بانتظار المراجعة البشرية.")
                    st.rerun()
                except (ValueError, UnicodeDecodeError, zipfile.BadZipFile, json.JSONDecodeError, AtlasAPIError) as exc:
                    st.error("تعذر الاستيراد: " + str(exc))
            discoveries = api.list_discoveries(token=token)
            st.metric("اكتشافات المرحلة الرابعة المتاحة", len(discoveries))
            if discoveries:
                st.dataframe(discoveries, width="stretch", hide_index=True)
            st.caption("التصنيف أولي؛ لا يُسمح باعتبار هذه السجلات أدلة مثبتة على الفعالية دون مراجعة علمية.")
            if discoveries:
                st.subheader("التحليل العلمي المنظم")
                selected_discovery = st.selectbox("اختر اكتشافاً لتحليل أدلته", discoveries,
                                                   format_func=lambda r: (r.get("title") or "")[:100],
                                                   key="evidence_selected")
                st.markdown("**المصدر الأصلي:** " + selected_discovery.get("source", ""))
                st.link_button("فتح المصدر والتحقق من محتواه", selected_discovery["url"])
                st.caption("لا تعتمد على العنوان أو عدد الاستشهادات وحدهما لإثبات الفعالية.")
                saved_review = api.get_evidence_review(selected_discovery["id"], token) or {}
                design_options = ["not_assessed","randomized_trial","quasi_experiment","observational",
                                  "systematic_review","meta_analysis","qualitative","descriptive","not_applicable","other"]
                quality_options = ["not_assessed","very_low","low","moderate","high"]
                direction_options = ["not_assessed","positive","negative","mixed","null","inconclusive","not_applicable"]
                with st.form("structured_evidence_review"):
                    design = st.selectbox("تصميم الدراسة", design_options,
                                         index=design_options.index(saved_review.get("study_design","not_assessed")))
                    quality = st.selectbox("جودة الأدلة", quality_options,
                                          index=quality_options.index(saved_review.get("evidence_quality","not_assessed")))
                    direction = st.selectbox("اتجاه النتائج", direction_options,
                                            index=direction_options.index(saved_review.get("outcome_direction","not_assessed")))
                    population = st.text_area("الفئة التعليمية والسياق", value=saved_review.get("learner_population",""))
                    intervention = st.text_area("التدخل أو الطريقة التعليمية", value=saved_review.get("intervention",""))
                    comparator = st.text_area("مجموعة المقارنة أو البديل", value=saved_review.get("comparator",""))
                    outcomes = st.text_area("المخرجات المقاسة والمدة", value=saved_review.get("outcomes",""))
                    effect = st.text_input("حجم الأثر وعدم اليقين (إن توفر)", value=saved_review.get("effect_size",""))
                    limitations = st.text_area("التحيز والقيود والتعارضات", value=saved_review.get("limitations",""))
                    checked = st.checkbox("تحققت من النص أو المصدر الأصلي", value=saved_review.get("source_checked",False))
                    notes = st.text_area("ملاحظات المراجع", value=saved_review.get("review_notes",""))
                    save_evidence = st.form_submit_button("حفظ التقييم العلمي الخاص")
                if save_evidence:
                    try:
                        api.save_evidence_review(selected_discovery["id"], user_id, token, {
                            "study_design": design, "evidence_quality": quality, "outcome_direction": direction,
                            "learner_population": population, "intervention": intervention, "comparator": comparator,
                            "outcomes": outcomes, "effect_size": effect, "limitations": limitations,
                            "source_checked": checked, "review_notes": notes})
                        st.success("حُفظ التقييم العلمي في قاعدة البيانات الخاصة.")
                        st.rerun()
                    except AtlasAPIError as exc:
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
