# PM Co-Pilot Automation

This project ingests MeetGeek meeting summaries, asks Gemini to produce PM-ready
Jira instructions, applies them to Jira Cloud, and posts a Slack digest.

## Architecture

- `main.py` orchestrates the pipeline end-to-end.
- `config.py` loads required environment variables via `.env`.
- `meetgeek/client.py` fetches meeting summaries.
- `ai/gemini_client.py` sends the summary plus the fixed Jira prompt to Gemini.
- `jira/mcp_agent.py` calls Jira Cloud REST APIs to create/update issues.
- `notifications/slack_notifier.py` posts a summary (created/updated issues,
  blockers, unresolved assignees) to Slack.
- `utils/logger.py` and `utils/file_io.py` provide logging and JSON persistence.

## Prerequisites

1. Python 3.10+
2. `pip install -r requirements.txt`
3. `.env` with:
   ```
   GEMINI_API_KEY=...
   MEETGEEK_API_KEY=...
   MEETGEEK_MEETING_ID=...

   JIRA_EMAIL=...
   JIRA_API_TOKEN=...
   JIRA_CLOUD_ID=...  # e.g. 87d1dd9d-e088-4722-8ffc-04db0c38cb8a

   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
   ```
   (Optional) `JIRA_PROJECT_KEY` if you want a default in custom scripts.

## Running the pipeline

From the repository root:

```bash
python mavric_pm_copilot/main.py
```

Steps performed:
1. Load config from `.env`.
2. Fetch MeetGeek summary for `MEETGEEK_MEETING_ID`.
3. Send the text to Gemini using the hard-coded Jira prompt.
4. Persist the AI JSON to `mavric_pm_copilot/pm_copilot_output.json`.
5. Create/update Jira issues via REST (`jira/mcp_agent.py`).
6. Send a Slack digest (fallback to MeetGeek text if Gemini omitted `ai_insights`).

If Jira returns errors (e.g., missing ADF descriptions, unresolved assignees),
logs are emitted in the console and also summarized in Slack.

## Automation ideas

- Use Windows Task Scheduler or cron to run `python mavric_pm_copilot/main.py`
  after each meeting. The script is idempotent if the MeetGeek meeting ID
  changes per run.
- Future extension: replace `jira/mcp_agent.py` with MCP tool calls if preferred.

## Troubleshooting

- **Description ADF errors**: Already handled—`mcp_agent.py` converts plain text
  to Atlassian Document Format automatically.
- **Assignee lookups**: Provide real Jira account names or IDs; otherwise issues
  remain unassigned and a Slack note lists the unresolved names.
- **Slack summary missing**: If Gemini omits `ai_insights`, we fall back to the
  MeetGeek transcript snippet so the Slack message always contains context.

