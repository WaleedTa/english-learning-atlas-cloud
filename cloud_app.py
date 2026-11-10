"""Public catalog and private Supabase moderation console."""
import csv
import io
import json
import zipfile
import streamlit as st
from atlas_supabase import AtlasClient, AtlasAPIError
from research_taxonomy import tag_inventory, tags_for, label as taxonomy_label, compare_review_groups

st.set_page_config(page_title="English Learning Atlas Cloud", page_icon="🌐", layout="wide")

LANGUAGE_OPTIONS = {"العربية": "ar", "English": "en"}
language_choice = st.sidebar.selectbox("اللغة / Language", list(LANGUAGE_OPTIONS), key="atlas_language")
LANG = LANGUAGE_OPTIONS[language_choice]

def tr(ar, en):
    return ar if LANG == "ar" else en

LABELS = {
    "not_assessed": ("غير مقيم", "Not assessed"),
    "randomized_trial": ("تجربة عشوائية", "Randomized trial"),
    "quasi_experiment": ("شبه تجريبية", "Quasi-experimental"),
    "observational": ("رصدية", "Observational"),
    "systematic_review": ("مراجعة منهجية", "Systematic review"),
    "meta_analysis": ("تحليل تلوي", "Meta-analysis"),
    "qualitative": ("نوعية", "Qualitative"),
    "descriptive": ("وصفية", "Descriptive"),
    "not_applicable": ("لا ينطبق", "Not applicable"),
    "other": ("أخرى", "Other"),
    "very_low": ("منخفضة جداً", "Very low"),
    "low": ("منخفضة", "Low"),
    "medium": ("متوسطة", "Medium"),
    "moderate": ("متوسطة", "Moderate"),
    "high": ("عالية", "High"),
    "positive": ("إيجابية", "Positive"),
    "negative": ("سلبية", "Negative"),
    "mixed": ("مختلطة", "Mixed"),
    "null": ("لا أثر", "Null effect"),
    "inconclusive": ("غير حاسمة", "Inconclusive"),
    "pending": ("قيد الانتظار", "Pending"),
    "approved": ("معتمد", "Approved"),
    "rejected": ("مرفوض", "Rejected"),
    "needs_full_text": ("يحتاج النص الكامل", "Needs full text"),
}
def display_code(value):
    pair = LABELS.get(value)
    return pair[0 if LANG == "ar" else 1] if pair else str(value or "")

st.title("🌐 English Learning Atlas Cloud")
st.caption(tr("أطلس عالمي لتعليم الإنجليزية | مكتبة عامة ومراجعة بشرية خاصة", "Global English-learning research atlas | Public library and private review"))
st.info(tr("المصادر الآلية: OpenAlex وCrossref وEurope PMC. البيانات المكتشفة أولية وليست إثباتاً علمياً للفعالية.", "Automated sources: OpenAlex, Crossref and Europe PMC. Discovery metadata is preliminary and does not prove effectiveness."))

try:
    url = st.secrets.get("SUPABASE_URL", "")
    key = st.secrets.get("SUPABASE_ANON_KEY", "")
except Exception:
    url, key = "", ""
if not url or not key:
    st.warning(tr("لم تُضبط قاعدة البيانات بعد. أكمل تعليمات PHASE3_SETUP.md في GitHub وأضف مفاتيح Supabase العامة إلى Streamlit Secrets.", "Database not configured. Follow PHASE3_SETUP.md and add the public Supabase keys to Streamlit Secrets."))
    st.stop()
try:
    api = AtlasClient(url, key)
except AtlasAPIError as exc:
    st.error(str(exc))
    st.stop()

public_tab, admin_tab = st.tabs([tr("📚 الأطلس العام", "📚 Public atlas"), tr("🔐 إدارة ومراجعة خاصة", "🔐 Private administration")])
with public_tab:
    st.subheader(tr("المصادر المعتمدة للنشر", "Approved publications"))
    try:
        published = api.list_resources(status="approved")
        query = st.text_input(tr("ابحث في المصادر المنشورة", "Search published resources"))
        visible = [r for r in published if query.casefold() in (r.get("title", "") + " " + (r.get("source_query") or "")).casefold()]
        st.metric(tr("مصادر منشورة", "Published resources"), len(published))
        st.dataframe(visible, width='stretch', hide_index=True,
                     column_config={"id": st.column_config.LinkColumn("OpenAlex"), "doi": st.column_config.LinkColumn("DOI")})
        if not published:
            st.info(tr("لا توجد أبحاث معتمدة للنشر حتى الآن. الأبحاث المرشحة لا تظهر للعامة.", "No approved publications yet. Pending records are not visible to the public."))
    except AtlasAPIError as exc:
        st.error(str(exc))

with admin_tab:
    if "atlas_session" not in st.session_state:
        st.session_state.atlas_session = None
    if not st.session_state.atlas_session:
        with st.form("admin_login"):
            email = st.text_input(tr("البريد الإلكتروني للمدير", "Administrator email"))
            password = st.text_input(tr("كلمة المرور", "Password"), type="password")
            sign_in = st.form_submit_button(tr("تسجيل الدخول", "Sign in"))
        if sign_in:
            try:
                session = api.login(email, password)
                if not session.get("access_token") or not session.get("user", {}).get("id"):
                    raise AtlasAPIError("No valid user session returned")
                st.session_state.atlas_session = session
                st.rerun()
            except AtlasAPIError as exc:
                st.error(str(exc))
        st.caption(tr("لا يكفي امتلاك حساب Supabase للدخول إلى بيانات الإدارة؛ يجب إدراج UUID في atlas_admins.", "A Supabase account alone does not grant administrator access; the UUID must be in atlas_admins."))
    else:
        session = st.session_state.atlas_session
        token = session["access_token"]
        user_id = session["user"]["id"]
        if st.button(tr("تسجيل الخروج", "Sign out")):
            st.session_state.atlas_session = None
            st.rerun()
        try:
            all_rows = api.list_resources(token=token, limit=10000)
            st.metric(tr("جميع السجلات المتاحة لهذا الحساب", "Resources available to this account"), len(all_rows))
            st.caption(tr("إذا لم تكن مديرا مسجلاً فسترى السجلات العامة فقط، ولن تتمكن من تعديلها.", "Only registered administrators can access and modify private records."))
            st.subheader(tr("استيراد مرشحات البحث", "Import research candidates"))
            upload = st.file_uploader(tr("ارفع ملف CSV الناتج من GitHub Actions", "Upload CSV from GitHub Actions"), type=["csv"])
            if upload is not None and st.button(tr("استيراد كمرشحات غير منشورة", "Import as unpublished candidates")):
                try:
                    candidate_rows = list(csv.DictReader(io.StringIO(upload.getvalue().decode("utf-8-sig"))))
                    count = api.upsert_candidates(candidate_rows, token)
                    st.success(f"تم استيراد {count} سجلاً بحالة pending، دون نشر تلقائي.")
                    st.rerun()
                except (UnicodeDecodeError, csv.Error, AtlasAPIError) as exc:
                    st.error(str(exc))
            st.subheader(tr("اكتشافات المرحلة الرابعة", "Phase 4 discoveries"))
            st.caption(tr("ارفع ZIP الناتج من GitHub Actions، وستُحفظ السجلات بحالة pending فقط.", "Upload the ZIP from GitHub Actions; records remain pending."))
            discovery_zip = st.file_uploader(tr("ملف phase4-research-candidates.zip", "phase4-research-candidates.zip file"), type=["zip"], key="phase4_zip")
            if discovery_zip is not None and st.button(tr("استيراد اكتشافات المرحلة الرابعة دون نشر", "Import Phase 4 discoveries without publishing")):
                try:
                    if discovery_zip.size > 15 * 1024 * 1024:
                        raise ValueError(tr("الملف أكبر من الحد المسموح", "File exceeds size limit"))
                    with zipfile.ZipFile(io.BytesIO(discovery_zip.getvalue())) as archive:
                        files = [n for n in archive.namelist() if n.split("/")[-1] == "candidates.jsonl"]
                        if len(files) != 1:
                            raise ValueError(tr("لم يُعثر على candidates.jsonl واحد داخل الأرشيف", "Expected exactly one candidates.jsonl in the archive"))
                        info = archive.getinfo(files[0])
                        if info.file_size > 12 * 1024 * 1024:
                            raise ValueError(tr("حجم بيانات الأرشيف غير مسموح", "Archive data exceeds size limit"))
                        records = [json.loads(line) for line in archive.read(files[0]).decode("utf-8").splitlines() if line.strip()]
                    count = api.import_discoveries(records, token)
                    st.success(f"تم حفظ {count} اكتشافاً جديداً بانتظار المراجعة البشرية.")
                    st.rerun()
                except (ValueError, UnicodeDecodeError, zipfile.BadZipFile, json.JSONDecodeError, AtlasAPIError) as exc:
                    st.error(tr("تعذر الاستيراد: ", "Import failed: ") + str(exc))
            discoveries = api.list_discoveries(token=token)
            st.metric(tr("اكتشافات المرحلة الرابعة المتاحة", "Available Phase 4 discoveries"), len(discoveries))
            if discoveries:
                st.dataframe(discoveries, width="stretch", hide_index=True)
            st.caption(tr("التصنيف أولي؛ لا يُسمح باعتبار هذه السجلات أدلة مثبتة على الفعالية دون مراجعة علمية.", "Classification is preliminary; these records are not validated effectiveness evidence."))
            with st.expander(tr("قاموس التصنيف العلمي الموحد — استكشاف الوسوم", "Unified scientific taxonomy — explore tags")):
                st.caption(tr("هذه وسوم مستخرجة أولياً من بيانات المصادر؛ لا تعني إثبات فعالية طريقة تعليمية.",
                              "These are preliminary discovery metadata tags; they do not establish teaching effectiveness."))
                for category, ar, en in (("skills", "المهارات", "Skills"),
                                          ("methods", "الطرق التعليمية", "Teaching methods"),
                                          ("frameworks", "الأطر المرجعية", "Reference frameworks")):
                    inventory = tag_inventory(discoveries, category)
                    st.markdown("**" + tr(ar, en) + "**")
                    st.dataframe([{
                        tr("الرمز", "Code"): code,
                        tr("الاسم", "Name"): taxonomy_label(category, code, LANG),
                        tr("عدد الاكتشافات", "Discoveries"): count,
                    } for code, count in inventory], width="stretch", hide_index=True)

            if discoveries:
                st.subheader(tr("التحليل العلمي المنظم", "Structured scientific assessment"))
                selected_discovery = st.selectbox(tr("اختر اكتشافاً لتحليل أدلته", "Select a discovery for evidence assessment"), discoveries,
                                                   format_func=lambda r: (r.get("title") or "")[:100],
                                                   key="evidence_selected")
                st.markdown(tr("**المصدر الأصلي:** ", "**Original source:** ") + selected_discovery.get("source", ""))
                st.link_button(tr("فتح المصدر والتحقق من محتواه", "Open and verify original source"), selected_discovery["url"])
                st.caption(tr("لا تعتمد على العنوان أو عدد الاستشهادات وحدهما لإثبات الفعالية.", "Titles and citation counts alone do not establish effectiveness."))
                saved_review = api.get_evidence_review(selected_discovery["id"], token) or {}
                design_options = ["not_assessed","randomized_trial","quasi_experiment","observational",
                                  "systematic_review","meta_analysis","qualitative","descriptive","not_applicable","other"]
                quality_options = ["not_assessed","very_low","low","moderate","high"]
                direction_options = ["not_assessed","positive","negative","mixed","null","inconclusive","not_applicable"]
                with st.form("structured_evidence_review"):
                    design = st.selectbox(tr("تصميم الدراسة", "Study design"), design_options,
                                         index=design_options.index(saved_review.get("study_design","not_assessed")), format_func=display_code)
                    quality = st.selectbox(tr("جودة الأدلة", "Evidence quality"), quality_options,
                                          index=quality_options.index(saved_review.get("evidence_quality","not_assessed")), format_func=display_code)
                    direction = st.selectbox(tr("اتجاه النتائج", "Outcome direction"), direction_options,
                                            index=direction_options.index(saved_review.get("outcome_direction","not_assessed")), format_func=display_code)
                    population = st.text_area(tr("الفئة التعليمية والسياق", "Learner population and context"), value=saved_review.get("learner_population",""))
                    intervention = st.text_area(tr("التدخل أو الطريقة التعليمية", "Intervention / teaching method"), value=saved_review.get("intervention",""))
                    comparator = st.text_area(tr("مجموعة المقارنة أو البديل", "Comparator / alternative"), value=saved_review.get("comparator",""))
                    outcomes = st.text_area(tr("المخرجات المقاسة والمدة", "Measured outcomes and duration"), value=saved_review.get("outcomes",""))
                    effect = st.text_input(tr("حجم الأثر وعدم اليقين (إن توفر)", "Effect size and uncertainty (if available)"), value=saved_review.get("effect_size",""))
                    limitations = st.text_area(tr("التحيز والقيود والتعارضات", "Bias, limitations and conflicting evidence"), value=saved_review.get("limitations",""))
                    checked = st.checkbox(tr("تحققت من النص أو المصدر الأصلي", "I verified the full text or original source"), value=saved_review.get("source_checked",False))
                    notes = st.text_area(tr("ملاحظات المراجع", "Reviewer notes"), value=saved_review.get("review_notes",""))
                    save_evidence = st.form_submit_button(tr("حفظ التقييم العلمي الخاص", "Save private scientific assessment"))
                if save_evidence:
                    try:
                        api.save_evidence_review(selected_discovery["id"], user_id, token, {
                            "study_design": design, "evidence_quality": quality, "outcome_direction": direction,
                            "learner_population": population, "intervention": intervention, "comparator": comparator,
                            "outcomes": outcomes, "effect_size": effect, "limitations": limitations,
                            "source_checked": checked, "review_notes": notes})
                        st.success(tr("حُفظ التقييم العلمي في قاعدة البيانات الخاصة.", "Scientific assessment saved in the private database."))
                        st.rerun()
                    except AtlasAPIError as exc:
                        st.error(str(exc))

            st.subheader(tr("مقارنة الأدلة العلمية — المرحلة الخامسة", "Evidence comparison — Phase 5"))
            st.caption(tr("مقارنة وصفية للتقييمات البشرية، وليست تحليلاً تلوياً أو حكماً آلياً بالفعالية.",
                          "Descriptive human assessments; not a meta-analysis or automated effectiveness verdict."))
            reviews = api.list_evidence_reviews(token)
            discovery_by_id = {d["id"]: d for d in discoveries}
            comparison_rows = []
            for review in reviews:
                d = discovery_by_id.get(review["discovery_id"], {})
                comparison_rows.append({
                    "discovery_id": review["discovery_id"],
                    "title": d.get("title") or review["discovery_id"],
                    "source": d.get("source") or "",
                    "year": d.get("year"),
                    "design": review.get("study_design") or "not_assessed",
                    "quality": review.get("evidence_quality") or "not_assessed",
                    "direction": review.get("outcome_direction") or "not_assessed",
                    "skills": ", ".join(d.get("skills") or []),
                    "methods": ", ".join(d.get("methods") or []),
                    "intervention": review.get("intervention") or "",
                    "population": review.get("learner_population") or "",
                    "comparator": review.get("comparator") or "",
                    "outcomes": review.get("outcomes") or "",
                    "effect": review.get("effect_size") or "",
                    "limitations": review.get("limitations") or "",
                    "verified": bool(review.get("source_checked")),
                    "url": d.get("url") or "",
                })
            if comparison_rows:
                st.caption(tr("الفلاتر اختيارية ومستقلة. عدم تحديد أي فلتر يعني عرض جميع السجلات.",
                              "Filters are optional and independent. With no filters selected, all records are shown."))
                search = st.text_input(tr("بحث شامل", "Search across studies"), key="compare_search")
                left, middle, right = st.columns(3)
                with left:
                    chosen_quality = st.multiselect(tr("جودة الأدلة", "Evidence quality"),
                        sorted({r["quality"] for r in comparison_rows}),
                        format_func=display_code, key="compare_quality")
                with middle:
                    chosen_direction = st.multiselect(tr("اتجاه النتائج", "Outcome direction"),
                        sorted({r["direction"] for r in comparison_rows}),
                        format_func=display_code, key="compare_direction")
                with right:
                    chosen_design = st.multiselect(tr("تصميم الدراسة", "Study design"),
                        sorted({r["design"] for r in comparison_rows}),
                        format_func=display_code, key="compare_design")
                skill_inventory = sorted({tag for d in discoveries for tag in tags_for(d, "skills")})
                method_inventory = sorted({tag for d in discoveries for tag in tags_for(d, "methods")})
                with st.expander(tr("فلاتر التصنيف المتقدمة", "Advanced taxonomy filters")):
                    selected_skills = st.multiselect(tr("المهارات التعليمية", "Learning skills"),
                        skill_inventory, format_func=lambda v: taxonomy_label("skills", v, LANG),
                        key="compare_skills")
                    selected_methods = st.multiselect(tr("طرق التعليم", "Teaching methods"),
                        method_inventory, format_func=lambda v: taxonomy_label("methods", v, LANG),
                        key="compare_methods")
                sources = sorted({r["source"] for r in comparison_rows if r["source"]})
                selected_sources = st.multiselect(tr("المصدر", "Source"), sources, key="compare_source")
                only_verified = st.checkbox(tr("المصادر المتحقق منها فقط", "Verified sources only"), key="compare_verified")
                sort_choice = st.selectbox(tr("ترتيب النتائج", "Sort results"),
                    ["recent", "title", "year"], format_func=lambda v: {
                        "recent": tr("حسب ترتيب التقييمات", "Review order"),
                        "title": tr("العنوان", "Title"),
                        "year": tr("السنة الأحدث", "Newest year")}[v], key="compare_sort")
                needle = search.casefold().strip()
                filtered = [r for r in comparison_rows
                    if (not chosen_quality or r["quality"] in chosen_quality)
                    and (not chosen_direction or r["direction"] in chosen_direction)
                    and (not chosen_design or r["design"] in chosen_design)
                    and (not selected_sources or r["source"] in selected_sources)
                    and (not selected_skills or any(tag in selected_skills for tag in
                        tags_for(discovery_by_id.get(r["discovery_id"], {}), "skills")))
                    and (not selected_methods or any(tag in selected_methods for tag in
                        tags_for(discovery_by_id.get(r["discovery_id"], {}), "methods")))
                    and (not only_verified or r["verified"])
                    and (not needle or needle in " ".join(str(r[k]) for k in
                        ("title","source","skills","methods","intervention","population","outcomes")).casefold())]
                if sort_choice == "title":
                    filtered.sort(key=lambda r: r["title"].casefold())
                elif sort_choice == "year":
                    filtered.sort(key=lambda r: r["year"] or 0, reverse=True)
                a, b, c = st.columns(3)
                a.metric(tr("جميع التقييمات", "All assessments"), len(comparison_rows))
                b.metric(tr("نتائج مطابقة", "Matching results"), len(filtered))
                c.metric(tr("مصادر متحقق منها", "Verified sources"), sum(r["verified"] for r in filtered))
                if filtered:
                    import pandas as pd
                    headings = {
                        "title": tr("العنوان", "Title"),
                        "source": tr("المصدر", "Source"),
                        "year": tr("السنة", "Year"),
                        "design": tr("المنهج", "Design"),
                        "quality": tr("جودة الأدلة", "Evidence quality"),
                        "direction": tr("اتجاه النتيجة", "Outcome direction"),
                        "skills": tr("المهارات", "Skills"),
                        "methods": tr("الطرق", "Methods"),
                        "intervention": tr("التدخل", "Intervention"),
                        "population": tr("الفئة المستهدفة", "Learner population"),
                        "comparator": tr("المقارنة", "Comparator"),
                        "outcomes": tr("المخرجات", "Outcomes"),
                        "effect": tr("حجم الأثر", "Effect size"),
                        "limitations": tr("القيود", "Limitations"),
                        "verified": tr("تم التحقق", "Verified"),
                        "url": tr("رابط المصدر", "Source link"),
                    }
                    translated = [{headings[k]: display_code(v) if k in ("design","quality","direction") else v
                                   for k, v in row.items()} for row in filtered]
                    frame = pd.DataFrame(translated)
                    st.dataframe(frame, width="stretch", hide_index=True,
                        column_config={headings["url"]: st.column_config.LinkColumn(headings["url"]),
                                       headings["verified"]: st.column_config.CheckboxColumn(headings["verified"])},
                        height=min(650, 100 + 38 * len(filtered)))
                    st.download_button(tr("تنزيل المقارنة CSV", "Export comparison CSV"),
                        frame.to_csv(index=False).encode("utf-8-sig"),
                        file_name="atlas-evidence-comparison.csv", mime="text/csv")
                    chart_left, chart_right = st.columns(2)
                    with chart_left:
                        st.markdown("**" + tr("توزيع اتجاه النتائج", "Outcome distribution") + "**")
                        counts = pd.Series([display_code(r["direction"]) for r in filtered]).value_counts()
                        st.bar_chart(counts.rename_axis(tr("النتيجة", "Outcome")).reset_index(name=tr("العدد", "Count")),
                            x=tr("النتيجة", "Outcome"), y=tr("العدد", "Count"))
                    with chart_right:
                        st.markdown("**" + tr("توزيع جودة الأدلة", "Evidence-quality distribution") + "**")
                        counts = pd.Series([display_code(r["quality"]) for r in filtered]).value_counts()
                        st.bar_chart(counts.rename_axis(tr("الجودة", "Quality")).reset_index(name=tr("العدد", "Count")),
                            x=tr("الجودة", "Quality"), y=tr("العدد", "Count"))
                else:
                    st.info(tr("لا توجد نتائج مطابقة. امسح الفلاتر أو غيّر البحث.",
                               "No matching records. Clear filters or adjust your search."))
                st.warning(tr("هذه رسوم لعدد التقييمات، وليست قياساً لحجم التأثير أو إثباتاً لفعالية طريقة تعليمية.",
                              "These charts count assessments; they do not measure effect sizes or establish teaching effectiveness."))
                st.subheader(tr("تجميع الدراسات حسب الطريقة والمهارة", "Study groups by teaching method and skill"))
                st.caption(tr("تجميع استكشافي بحسب وسوم المصادر الأولية. اختلاف النتائج إشارة للمراجعة، وليس تناقضاً مثبتاً.",
                              "Exploratory grouping by preliminary metadata tags. Different recorded outcomes flag review, not proven contradiction."))
                groups = compare_review_groups(discoveries, reviews)
                group_names = {"insufficient": tr("أدلة غير كافية", "Insufficient evidence"),
                               "divergent": tr("نتائج مختلفة — تتطلب مراجعة", "Different outcomes — review needed"),
                               "consistent_recorded": tr("اتجاهات مسجلة متفقة مبدئياً", "Recorded directions provisionally aligned")}
                if groups:
                    st.dataframe([{
                        tr("الطريقة", "Method"): taxonomy_label("methods", g["method"], LANG),
                        tr("المهارة", "Skill"): taxonomy_label("skills", g["skill"], LANG),
                        tr("عدد التقييمات", "Assessment count"): g["count"],
                        tr("تقييمات عالية الجودة", "High-quality assessments"): g["quality_high"],
                        tr("مصادر متحقق منها", "Verified sources"): g["verified"],
                        tr("إشارة التحليل", "Analysis signal"): group_names[g["signal"]],
                    } for g in groups], hide_index=True, width="stretch")
                else:
                    st.info(tr("لا توجد مجموعات قابلة للمقارنة حتى الآن.",
                               "No comparable groups yet."))
            else:
                st.info(tr("لا توجد تقييمات علمية محفوظة للمقارنة بعد.",
                           "No scientific assessments saved yet."))

            st.subheader(tr("مراجعة سجل", "Review a resource"))
            if all_rows:
                options = {r["id"]: r for r in all_rows}
                selected = st.selectbox(tr("الدراسة", "Study"), list(options), format_func=lambda k: (options[k].get("title") or k)[:110])
                item = options[selected]
                st.write(tr("**العنوان:**", "**Title:**"), item["title"])
                st.write(tr("**الحالة:**", "**Status:**"), item["review_status"])
                if item.get("doi"):
                    st.write("**DOI:**", item["doi"])
                statuses = ["pending", "needs_full_text", "approved", "rejected"]
                qualities = ["not_assessed", "low", "moderate", "high"]
                relevances = ["not_assessed", "low", "medium", "high"]
                with st.form("review_record"):
                    status = st.selectbox(tr("القرار", "Decision"), statuses, index=statuses.index(item["review_status"]), format_func=display_code)
                    quality = st.selectbox(tr("قوة الأدلة", "Strength of evidence"), qualities, index=qualities.index(item["evidence_quality"]), format_func=display_code)
                    relevance = st.selectbox(tr("صلة الدراسة", "Study relevance"), relevances, index=relevances.index(item["relevance"]), format_func=display_code)
                    notes = st.text_area(tr("مبررات القرار والمنهج والقيود", "Decision rationale, methodology and limitations"), value=item.get("review_notes") or "")
                    save = st.form_submit_button(tr("حفظ المراجعة في قاعدة البيانات", "Save review to database"))
                if save:
                    try:
                        api.review(selected, token, user_id, status, quality, relevance, notes)
                        st.success(tr("تم حفظ المراجعة بصورة دائمة.", "Review saved permanently."))
                        st.rerun()
                    except AtlasAPIError as exc:
                        st.error(str(exc))
        except AtlasAPIError as exc:
            st.error(tr("تعذر تحميل البيانات أو انتهت صلاحية الجلسة: ", "Unable to load data or session expired: ") + str(exc))
            st.caption(tr("سجل الخروج وأعد الدخول إذا انتهت صلاحية الرمز.", "Sign out and back in if the access token expired."))
