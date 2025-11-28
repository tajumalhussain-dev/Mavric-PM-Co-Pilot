"""Slack notification helpers."""

from __future__ import annotations

import json
from typing import Iterable, List, Dict, Any

import requests

from mavric_pm_copilot.jira.mcp_agent import JiraAction, JiraSyncResult
from mavric_pm_copilot.utils.logger import get_logger

logger = get_logger(__name__)


def _format_issue_list(issues: Iterable[JiraAction], limit: int = 5) -> str:
    """
    Format a short bullet list of Jira issues for Slack.

    Shows up to `limit` issues, then adds "…and X more" if there are more.
    """
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
    model_output: Dict[str, Any],
    jira_result: JiraSyncResult,
) -> None:
    """Send a structured PM Co-Pilot summary to Slack based on full JSON output."""

    meeting_summary: Dict[str, Any] = model_output.get("meeting_summary", {}) or {}
    risks: List[Dict[str, Any]] = model_output.get("risks", []) or []
    daily_updates: Dict[str, Dict[str, Any]] = model_output.get("daily_updates", {}) or {}

    # === Build Slack text ===
    text_lines: List[str] = []

    # Header
    text_lines.append("*PM Co-Pilot — Standup Summary*")
    text_lines.append(f"Meeting ID: `{meeting_id}`\n")

    # --- Meeting Summary ---
    text_lines.append("*Meeting Summary*")
    status = meeting_summary.get("overall_status", "N/A")
    text_lines.append(f"- *Status:* {status}")

    highlights = meeting_summary.get("highlights", []) or []
    if highlights:
        text_lines.append("*Highlights:*")
        text_lines.extend(f"• {h}" for h in highlights)

    blockers_overall = meeting_summary.get("blockers_overall", []) or []
    if blockers_overall:
        text_lines.append("*Team Blockers:*")
        text_lines.extend(f"• {b}" for b in blockers_overall)

    decisions = meeting_summary.get("decisions", []) or []
    if decisions:
        text_lines.append("*Decisions:*")
        text_lines.extend(f"• {d}" for d in decisions)

    next_steps = meeting_summary.get("next_steps", []) or []
    if next_steps:
        text_lines.append("*Next Steps:*")
        text_lines.extend(f"• {n}" for n in next_steps)

    # --- Risks ---
    text_lines.append("\n*Risks*")
    if risks:
        for r in risks:
            area = r.get("area", "Unknown area")
            desc = r.get("description", "")
            impact = r.get("impact", "Unknown")
            likelihood = r.get("likelihood", "Unknown")
            text_lines.append(
                f"• *{area}* — {desc} (Impact: {impact}, Likelihood: {likelihood})"
            )
    else:
        text_lines.append("No major risks identified.")

    # --- Daily Updates ---
    text_lines.append("\n*Daily Updates*")
    if daily_updates:
        for person, details in daily_updates.items():
            yesterday = details.get("yesterday", "N/A")
            today = details.get("today", "N/A")
            completed = details.get("completed_tickets", []) or []
            blockers = details.get("blockers", []) or []

            text_lines.append(f"*{person}:*")
            text_lines.append(f"• Yesterday: {yesterday}")
            text_lines.append(f"• Today: {today}")
            text_lines.append(
                "• Completed: " + (", ".join(completed) if completed else "None")
            )
            text_lines.append(
                "• Blockers: " + (", ".join(blockers) if blockers else "None")
            )
            text_lines.append("")  # blank line between people
    else:
        text_lines.append("No individual updates parsed.")

    # --- Jira summary ---
    text_lines.append("*Created Issues*")
    text_lines.append(_format_issue_list(jira_result.created))

    text_lines.append("\n*Updated Issues*")
    if jira_result.updated:
        updated_lines: List[str] = []
        for action in jira_result.updated:
            parts: List[str] = []
            if action.comments_added:
                parts.append("comment")
            if action.new_status:
                parts.append(f"status→{action.new_status}")
            if action.fields_updated:
                parts.append("fields(" + ", ".join(action.fields_updated) + ")")
            suffix = " ".join(parts) if parts else ""
            updated_lines.append(f"• {action.key}: {suffix}".rstrip())
        text_lines.extend(updated_lines)
    else:
        text_lines.append("None")

    # Assignee lookup failures
    if jira_result.unresolved_assignees:
        missing = ", ".join(sorted(set(jira_result.unresolved_assignees)))
        text_lines.append(f"\n_Assignee lookups failed for:_ {missing}")

    # Join all lines
    text = "\n".join(text_lines)

    # Send Slack message
    response = requests.post(
        webhook_url,
        data=json.dumps({"text": text}),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if response.status_code >= 300:
        logger.error("Failed to send Slack notification: %s", response.text)


__all__ = ["send_slack_summary"]
