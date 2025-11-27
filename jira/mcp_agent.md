# Jira MCP Automation

`mcp_agent.py` contains the code that reads the structured Jira instructions
produced by the PM Co-Pilot pipeline and synchronizes them with Atlassian Cloud.

The sync process:

1. Parse the `jira` object in `pm_copilot_output.json`.
2. Create any new tickets using the REST API (`/issue`).
3. Apply updates (comments, transitions, field edits) to existing tickets.
4. Collect a summary that the Slack notifier uses downstream.

Environment variables required for this automation live in `.env`:

- `JIRA_CLOUD_ID`
- `JIRA_EMAIL`
- `JIRA_API_TOKEN`
- `SLACK_WEBHOOK_URL`

All requests use the Atlassian REST API via Basic Auth (email + token). If you
need to adapt this to an MCP-specific transport, replace the REST calls inside
`JiraMcpAgent` with the appropriate client implementation—the rest of the code
is already structured to pass validated payloads into a single sync method.

