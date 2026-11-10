# Atlas research-to-learning strategy — decision record v1

Date: 2026-11-10. Owner: Waleed. Status: proposed implementation strategy; **not a claim of uniqueness or efficacy**.

## North star

Build an independently assessable English-learning product, initially Arabic/English, from absolute beginner to advanced competency. Atlas is its internal, evidence-traceable research and decision system, not the learner product. A future learner platform and an outcomes/experiment feedback loop are separate components.

**Primary success metric:** independently assessed improvement in transferable English competence by level, skill, learner population and study period. Retention, engagement, app ratings and vocabulary recall are secondary measures; none substitutes for demonstrated language improvement.

## Direct design comparisons and adopted ideas

| Reference | Evidence-backed observed capability | Atlas adaptation | Caution |
| --- | --- | --- | --- |
| Elicit | Screen papers and extract cited answers | Per-claim source location and manual verification | Extraction errors require audits |
| EPPI-Reviewer | End-to-end systematic evidence review | Search, screen, extract, appraise, synthesize workflow | Not every Atlas question warrants full systematic review |
| ASReview | Open-source active-learning screening | Prioritized human screening queue | Estimate missed relevant studies before automating |
| OpenAlex | Connected scholarly metadata | DOI and source graph with deduplication | Metadata is not effectiveness evidence |
| EEF Toolkit | Cost, effect and certainty reported separately | Explain method applicability and evidence strength separately | School evidence may not generalize to adult L2 learners |
| Evidence for ESSA | Programs considered against defined study standards | Published eligibility criteria before ranking | Ratings are context-dependent |
| What Works Clearinghouse | Intervention reports and practice guides | Separate intervention result from recommendation | Do not declare causality from anecdotes |
| LearnSphere | Educational data + repeatable analyses | Consent-based event schema and repeatable analyses | Protect personal learning data |
| CMU Open Learning Initiative | Research-grounded courseware and feedback loops | Connect content improvements to measured outcomes | Product still requires real field trials |
| Duolingo Research | Language learning studies and shared datasets | Skill-specific learning experiments and reporting | Vendor studies need conflict-of-interest notation |
| Khanmigo | AI-supported guided tutoring | AI practice with correction and learner control | Fluent-sounding AI is not necessarily correct |
| CEFR Companion Volume | Proficiency descriptors across modalities | Traceable level/skill objectives, including interaction and mediation | CEFR label alone does not validate a test |
| LEVI | Learning engineering and student outcome focus | Hypothesis → prototype → experiment → iteration | Promising approach is not proof of success |

Primary sources: https://support.elicit.com/en/articles/14759154-systematic-reviews-in-elicit ; https://eppi.ioe.ac.uk/cms/er4/Working/HOME2 ; https://github.com/asreview/asreview ; https://help.openalex.org/api/ ; https://educationendowmentfoundation.org.uk/education-evidence/teaching-learning-toolkit/ ; https://education.jhu.edu/crre/evidence-based-education/evidence-solutions/evidence-for-essa/ ; https://ies.ed.gov/ncee/WWC/FWW ; https://www.cs.cmu.edu/~learnsphere/ ; https://oli.cmu.edu/about/ ; https://research.duolingo.com/ ; https://www.khanacademy.org/khanmigo ; https://www.coe.int/en/web/common-european-framework-reference-languages/cefr-descriptors ; https://learning-engineering-virtual-institute.org/

## Evidence distinctions: must never be merged into one score

1. **Identity**: project/source exists; link and revision verified.
2. **Feature claim**: project documents or source code suggest a capability. Not proof it works.
3. **Experience**: user/teacher feedback with provenance, context and sampling uncertainty. Not causal proof.
4. **Outcome evidence**: measured learner outcomes, full text, comparison group, statistical uncertainty and limitations.
5. **Synthesis**: reviewer-assessed certainty, consistency, applicability and conflicts for a defined question.
6. **Decision**: explicit, dated recommendation/hypothesis with trade-offs, reviewer and reversibility.

No overall application rating can replace these dimensions. Ratings never automatically convert into pedagogical effectiveness.

## Priority implementation stages

| Phase | Build | Exit criteria |
| --- | --- | --- |
| 8 — candidate knowledge registry | Admin-only project/claim data model, source validation | PR reviewed; licenses verified; RLS tested before any production migration |
| 9A — research questions and evidence gate | Question = population, CEFR, skill, intervention, comparator, outcome; evidence item = citation location, design, direction, caveats, review | Offline deterministic tests cover missing citations, unreviewed evidence, conflicts and prohibited auto-recommendation |
| 9B — scientific screening workflow | Protocol, deduplication, inclusion/exclusion, reviewer disagreement, PRISMA reporting | Reproducible small reference set; documented recall and disagreement rates |
| 9C — synthesis and decision log | Competing claims, effect sizes with uncertainty, applicability, decision owner/version/expiry | Each recommendation links to human-approved, inspectable evidence and counterevidence |
| 10 — CEFR learning design | Objective → task → feedback → assessment map for skills incl. mediation | Subject expert validates sample A0/A1 pathway and assessments |
| 11 — learner prototype | Consent-first diagnostic, adaptive practice, guided speech and feedback | Usability and accessibility trial; failure logging; no unvalidated proficiency claims |
| 12 — controlled evaluation | Pre/post delayed assessment and comparator where feasible | Independent results, limitations, subgroup analysis and privacy review |
| 13 — continuous improvement | Measure and monitor; re-evaluate evidence as new sources appear | Audit trail and rollback; proposals require human approval |

## Concrete evaluation instrumentation

- Discovery: precision at screening, recall against a curated known-relevant corpus, duplicate rate.
- Extraction: field-level accuracy and citation-location correctness versus blinded expert annotation.
- Synthesis: agreement with reviewers, disagreements, missed counterevidence, unsupported-claim rate.
- Learning: skill-specific externally assessed gain, delayed retention, transfer to authentic tasks, subgroup fairness.
- Operations: permissions tests (anon/non-admin/admin), update freshness, source rights, accessibility, translation parity, response reliability and cost.
- Every metric starts **unmeasured** until benchmark data exists; never fabricate baselines or thresholds achieved.

## Explicit governance rules

- Public Atlas users can read only approved material; administrative data is private and protected by RLS.
- AI may draft screening/extraction/recommendations. Humans authorize promotion to verified status and educational decisions.
- No hidden self-modification, no production schema/permissions changes, no scraping or data reuse without scoped source approval.
- Store only minimum necessary learner data with consent, deletion paths and purpose limits; avoid sending raw personal records to third-party models by default.
- Arabic/English are parity requirements for user-facing navigation, categories and comparisons; original-language evidence remains attributed.
- The unresolved leaked-password-protection setting is plan-gated at Supabase Pro and does not justify a silent plan upgrade.

## Phase 9A implementation snapshot

`evidence_decisions.py` introduces a minimal offline question/evidence validation and a decision gate. Even a favorable verified paper yields `requires_expert_synthesis`; contradictory results yield `conflicting_evidence`. This is deliberately **not** an automated effect estimation or validated scientific judgment system. The next step is source-specific verification, reviewed data and a benchmark dataset.

## Decision record

- **Adopt**: evidence-to-decision architecture and eventual closed-loop learning engineering.
- **Reject**: ranking by GitHub stars, community sentiment, engagement or vendor claims as proxies for learning outcomes.
- **Defer**: autonomous publishing, personal learner data ingestion, AI speech grading and an all-in-one student platform until reliability, validity and permissions are established.
- **Revisit**: any recommendation when contrary evidence emerges or the target learner population changes.
