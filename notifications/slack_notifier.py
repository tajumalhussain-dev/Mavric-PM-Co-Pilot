"""Slack notification helpers."""

from __future__ import annotations

import json
from typing import Iterable, List, Optional

import requests

from mavric_pm_copilot.jira.mcp_agent import JiraAction, JiraSyncResult
from mavric_pm_copilot.utils.logger import get_logger


logger = get_logger(__name__)


def extract_blockers(ai_insights: Optional[str]) -> List[str]:
    """Return lines mentioning blockers."""

    if not ai_insights:
        return []

    blockers = []
    for line in ai_insights.splitlines():
        lower = line.lower()
        if "blocker" in lower or "blocked" in lower:
            blockers.append(line.strip())
    return blockers


def _format_issue_list(issues: Iterable[JiraAction], limit: int = 5) -> str:
    items = list(issues)
    if not items:
        return "None"

    display = items[:limit]
    text = "\n".join(f"• {issue.key}: {issue.summary}" for issue in display)
    if len(items) > limit:
        text += f"\n…and {len(items) - limit} more"
    return text


def send_slack_summary(
    webhook_url: str,
    meeting_id: str,
    ai_insights: Optional[str],
    jira_result: JiraSyncResult,
    fallback_summary: Optional[str] = None,
) -> None:
    """Send a structured summary message to Slack."""

    blockers = extract_blockers(ai_insights)
    created_section = _format_issue_list(jira_result.created)
    updated_section = (
        "\n".join(
            f"• {action.key}: "
            f"{'comment ' if action.comments_added else ''}"
            f"{'status→' + action.new_status if action.new_status else ''}"
            f"{' fields(' + ', '.join(action.fields_updated) + ')' if action.fields_updated else ''}"
        )
        if jira_result.updated
        else "None"
    )

    summary_text = ai_insights or fallback_summary or "N/A"

    text = (
        f"*PM Co-Pilot Automation*\n"
        f"Meeting ID: `{meeting_id}`\n"
        f"Created: {len(jira_result.created)} | Updated: {len(jira_result.updated)}\n"
        f"*AI Insights Summary:*\n{summary_text[:600]}\n\n"
        f"*Created Issues:*\n{created_section}\n\n"
        f"*Updated Issues:*\n{updated_section}\n\n"
        f"*Blockers:*\n"
    )

    if blockers:
        text += "\n".join(f"• {line}" for line in blockers)
    else:
        text += "None detected"

    if jira_result.unresolved_assignees:
        text += (
            "\n\n_Assignee lookups failed for:_ "
            + ", ".join(sorted(set(jira_result.unresolved_assignees)))
        )

    response = requests.post(
        webhook_url,
        data=json.dumps({"text": text}),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if response.status_code >= 300:
        logger.error("Failed to send Slack notification: %s", response.text)


__all__ = ["send_slack_summary"]

