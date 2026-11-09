# Deployment and review

1. Review the PR and merge to main.
2. Open https://share.streamlit.io and choose **New app**, repository `WaleedTa/english-learning-atlas-cloud`, branch `main`, main file `cloud_app.py`.
3. Configure access controls if sensitive data is added. This GitHub repository is currently **public**.
4. In GitHub Settings → Actions → General, allow workflows to create pull requests if needed.
5. In Actions, select **Weekly discovery - review required** → **Run workflow**. Scheduled discovery runs Mondays at 06:00 UTC (09:00 Asia/Baghdad).
6. Review each candidate and its source before merging the generated PR. A candidate's citation count is not proof of effectiveness.
7. The automated collector currently queries OpenAlex only. The scope setting covers intended categories, not implemented crawler coverage.
8. Streamlit Community Cloud is not a durable writeable database. Use PostgreSQL and authenticated moderation before production use.

**Status:** initial code and workflow only; no live deployment or successful workflow run has yet been verified.
