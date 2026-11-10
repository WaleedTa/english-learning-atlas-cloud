# Community, user and institutional evidence — research engine scope

Status: approved architectural requirement, **not yet implemented as automated collection or validation**.
Context: English Learning Atlas Cloud autonomous research institute vision.

## Mission
Automatically discover, retrieve where permitted, evaluate and monitor not just peer-reviewed academic research but real-world experience and measurable use of English-learning resources. Cover Arabic and international sources; preserve original language and apply separate multilingual analysis.

## Source families
1. Scientific studies, registered trials, systematic reviews and institutional research.
2. Public user reviews, star ratings and written experiences from application stores, product directories, forums and communities; provider APIs/exports only where access is authorized.
3. Learning platforms and project repositories: documented methodologies, versions, tests, issue trackers, changelogs and disclosed outcomes.
4. Universities, language schools and institutes: audited course descriptions, independent evaluations, published completion and proficiency results.
5. Opt-in user study data and anonymized/aggregate learning analytics: pre/post language tests, retention, course completion, time spent, engagement and subgroup information, with consent, lawful basis and safeguards.
6. Public reports, independent audits, standardized assessments and external evaluations.

## Automated process
Discover -> permission/access check -> source provenance and timestamp -> fetch -> language detection -> deduplication -> spam/bot/affiliate and conflict-of-interest checks -> separate first-hand report from marketing and hearsay -> extract structured claims and metrics -> independently cross-check -> categorize by learning method, skill, learner population, learning level, geography and time -> identify convergences, contradictions and missing evidence -> human governance -> versioned archive -> periodic monitoring.

## Evidence hierarchy and pitfalls
- Keep verified outcome metrics, participant-reported experience, unverified online sentiment, official provider claims and academic findings in **separate columns and evidence classes**.
- Reviews and ratings are useful experience/satisfaction signals, **not proof of learning efficacy**.
- Account for selection bias, bots, incentives, sample sizes, language, geography, time, platform differences and duplicated syndication.
- A 4.8-star product cannot be declared better educationally than a 4.2-star competitor without defensible learning-outcome comparisons.
- Do not equate study counts, mentions or citation numbers with strength of evidence.
- Trace every reported claim to retrievable source, observed timestamp and collection method; clearly label inaccessible, unverifiable or synthetic claims.
- Never fabricate real reviews, testimonials, user outcomes or institute endorsements.

## Privacy, access and governance
- Respect robots.txt where applicable, provider terms, rate limits, copyright, applicable data-protection laws, and account/API access restrictions.
- Never bypass login, paywalls, private groups or anti-bot controls.
- Do not collect personal data from nonconsenting private users; minimize identifiers, redact sensitive details, aggregate wherever possible, and set retention/deletion policies.
- Private institutional data requires explicit permission/contract; no automatic access to private student records.
- Require owner authorization for creating data connectors, installing agents, modifying source code, changing schema, publishing consequential findings or making network-wide high-volume requests.
- Budget, start/pause/stop, source allowlist/denylist, audits, rollback and alert thresholds.

## Future implementation milestones
A. Define source registry and permitted ingestion metadata (provider, category, license/access status, URL, language, last_checked).
B. Add consent-aware review and experience evidence schema with source provenance and quality flags.
C. Create source-specific permission-aware adapters, starting with stable official/public APIs and openly licensed datasets.
D. Add bilingual review summarization with citations, duplicate/spam screening and quantitative aggregation with uncertainty.
E. Build side-by-side multidimensional comparisons separating outcomes, satisfaction, accessibility, cost, design quality and research evidence.
F. Add scheduled change detection and human approval gates to autonomous research workflows.

No existing 310 discoveries or private human evidence reviews should be modified by this scope document.
