PM Co-Pilot Automation <br>
MeetGeek → Gemini → Jira → Slack | Fully Automated PM Workflow

The PM Co-Pilot is an AI-driven automation system that converts meeting summaries into structured insights, Jira tickets, and Slack updates. It eliminates manual PM effort by transforming raw meeting notes into actionable work.

🚀 Architecture Overview
MeetGeek → Gemini AI → Python Pipeline → Jira REST API → Slack Notification


<b>Key Features:</b><br>

Automated meeting summary extraction

AI-powered analysis (risks, blockers, decisions, next steps)

Jira ticket creation & updates

Slack meeting digest

JSON snapshots saved for audit/history

📁 Project Structure
mavric_pm_copilot/
│
├── main.py                     # Orchestrates end-to-end workflow (CLI)
├── config.py                   # Loads env variables from .env
│
├── meetgeek/
│   └── client.py               # Fetches meeting summary from MeetGeek API
│
├── ai/
│   └── gemini_client.py        # Sends text to Gemini with strict JSON prompt
│
├── jira/
│   └── mcp_agent.py            # Jira REST API integration and sync logic
│
├── notifications/
│   └── slack_notifier.py       # Slack digest message builder & sender
│
├── ui/
│   ├── app.py                  # Streamlit dashboard (make.com-style run view)
│   └── assets/                 # Optional logos for MeetGeek, Gemini, Jira, Slack
│
├── utils/
│   ├── logger.py               # Unified logging
│   └── file_io.py              # JSON save/load utilities
│
└── pm_copilot_output.json      # AI output (archived each run)

🧪 What Worked Well
✔ MeetGeek Integration

Successfully fetched meeting summaries via …/summary endpoint

Provides stable structure for AI processing

✔ Gemini AI Processing

Generates:

Meeting summary

Daily updates per person

Risks

Decisions & next steps

Jira ticket instructions (strict JSON schema)

Always produces parseable JSON

✔ Jira REST API Automation

Fully automatable

No Docker required

Handles:

Creating issues

Updating issues

Adding comments

Assignments

Priorities & labels

✔ Slack Notifications

Slack summary includes:

Meeting highlights

Risks

Daily updates

Jira issue creations & updates

Blockers

Unresolved assignee names

⚠️ What Didn’t Work / Challenges
❌ ChatGPT API (No Credits)

Forced migration to Google Gemini

❌ MeetGeek Transcript Endpoint Issues

Provided line-by-line transcript requiring manual line selection

Switched to stable summary endpoint, fixed issue

❌ Jira MCP Automation Not Practical

Although Jira MCP was:

Installed

Configured in Cursor

Successfully used manually

It was not usable for Python-based automation because:

MCP tools run only inside Cursor/Claude

No direct API for Python/CLI

No support for automated background execution

Decision: Use Jira REST API for production automation.

🔐 Requirements
Install Dependencies
pip install -r requirements.txt

Required .env Variables
GEMINI_API_KEY=
MEETGEEK_API_KEY=
MEETGEEK_MEETING_ID=

SLACK_WEBHOOK_URL=

JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_BASE_URL=
JIRA_PROJECT_KEY=SCRUM

▶ How to Run (CLI)

From project root:

python mavric_pm_copilot/main.py


Pipeline Steps (CLI & UI)

Load configuration

Fetch MeetGeek meeting summary

Run Gemini analysis with strict JSON schema

Save pm_copilot_output.json

Create/update Jira issues via REST API

Post summary to Slack

Log outcomes

▶ How to Run (Streamlit UI Dashboard)

From project root:

# install dependencies
pip install -r requirements.txt

# launch dashboard (Windows example using Python launcher)
py -m streamlit run mavric_pm_copilot/ui/app.py

The UI will open in your browser (by default at http://localhost:8501) and provide:

- A **Run Pipeline** CTA that executes the full workflow
- A workflow header showing the services in the chain (Config → MeetGeek → Gemini → Jira → Slack)
- A step-by-step view with progress for:
  - Config load
  - MeetGeek summary fetch
  - Gemini JSON analysis
  - Jira sync
  - Slack notification & JSON persistence
- An expander with the raw MeetGeek transcript/summary
- An expander with the Gemini JSON output
- A summarized view of Jira actions (created/updated issues and unresolved assignees)
- A **Download last JSON output** button for the most recent run

🔧 UI Logos (Optional)

To display real logos in the workflow header instead of emojis:

- Place PNG files in `mavric_pm_copilot/ui/assets/` with the following names:
  - config.png   – generic configuration icon (optional)
  - meetgeek.png – MeetGeek logo
  - gemini.png   – Google Gemini logo
  - jira.png     – Jira logo
  - slack.png    – Slack logo

If a file is missing, the UI automatically falls back to an emoji for that service, so the dashboard works even without any custom assets.

📌 Output Example (Slack Digest)
PM Co-Pilot Automation
Meeting ID: 39323ad6-c916...
Created: 8 | Updated: 0

Meeting Summary:
• Navigation redesign approved
• Email UX fix assigned
• Refactoring planned

Risks:
• Delay risk in schema refactor (High)

Daily Updates:
Arslan – Completed SCRUM-203, working on SCRUM-204
Bilal – Blocked on payment API
…

Created Issues:
• SCRUM-54: Finalize PRDs
• SCRUM-55: Refactoring plan
…

Updated Issues:
None

Blockers:
None detected

Unresolved Assignees:
Matt, Muhammad, Osama, Shiraz

⌛ Automation Ideas
🕒 Windows Task Scheduler / Cron

Trigger the pipeline automatically after each meeting.

🧵 Multi-Meeting Support

Loop through multiple MeetGeek meeting IDs.

💾 Historical Storage

Save every run in a history/ folder.

🌐 Dashboard UI

A Streamlit-based frontend exists under `mavric_pm_copilot/ui/app.py`. It provides:

- A make.com-style run view that shows each pipeline step
- Service-level visualization (MeetGeek, Gemini, Jira, Slack)
- Downloadable JSON output for the last run
- Detailed inspection of model output, risks, and Jira actions

🛠 Troubleshooting
❌ JSON Parsing Error

Occurs if Gemini adds commentary.
Fixed with strict JSON-only enforcement.

❌ Assignee Lookup Failure

Happens when Jira names don’t match.
Add email → accountId mapping.

❌ Slack Message Missing Sections

Use updated slack_notifier.py (supports new schema).

📦 MCP vs REST — Final Decision
MCP
Feature	Status
Docker installed	✔
MCP server configured in Cursor	✔
Manual ticket creation inside Cursor	✔
Automation from Python	❌ Not possible
Headless execution	❌
REST API
Feature	Status
Supported by Python	✔
Fully automatable	✔
No Docker needed	✔
Used in final system	✔

Final Choice: Jira REST API (production)
MCP (Cursor Only) is optional and manual.

🏁 Final Summary

The PM Co-Pilot successfully automates:

Meeting understanding

Daily updates

Risk detection

Jira ticket creation/update

Slack reporting

JSON archival

The system is now production-ready, reliable, and extendable.