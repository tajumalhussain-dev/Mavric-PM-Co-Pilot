"""Automated Jira MCP synchronization using Atlassian Cloud REST APIs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence

import requests
from requests.auth import HTTPBasicAuth

from mavric_pm_copilot.config import AppConfig


logger = logging.getLogger(__name__)


@dataclass
class JiraAction:
    key: str
    summary: str


@dataclass
class JiraUpdateAction:
    key: str
    comments_added: List[str] = field(default_factory=list)
    new_status: Optional[str] = None
    fields_updated: List[str] = field(default_factory=list)


@dataclass
class JiraSyncResult:
    created: List[JiraAction] = field(default_factory=list)
    updated: List[JiraUpdateAction] = field(default_factory=list)
    unresolved_assignees: List[str] = field(default_factory=list)


class JiraMcpAgent:
    """Synchronize PM Co-Pilot JSON instructions with Jira via REST APIs."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._session = requests.Session()
        self._session.auth = HTTPBasicAuth(config.jira_email, config.jira_api_token)
        self._session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        self._account_cache: Dict[str, Optional[str]] = {}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def sync_from_payload(self, jira_payload: Mapping[str, Sequence[Mapping[str, object]]]) -> JiraSyncResult:
        """Apply create/update instructions and return a summary."""

        tickets_to_create = jira_payload.get("tickets_to_create", [])
        tickets_to_update = jira_payload.get("tickets_to_update", [])

        if not isinstance(tickets_to_create, Sequence) or not isinstance(tickets_to_update, Sequence):
            raise ValueError("Jira payload must include 'tickets_to_create' and 'tickets_to_update' arrays.")

        result = JiraSyncResult()

        for ticket in tickets_to_create:
            action = self._create_issue(ticket)
            if action:
                result.created.append(action)

        for ticket in tickets_to_update:
            update_action = self._update_issue(ticket)
            if update_action:
                result.updated.append(update_action)

        unresolved = [name for name, account_id in self._account_cache.items() if not account_id]
        result.unresolved_assignees.extend(unresolved)

        return result

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _create_issue(self, ticket: Mapping[str, object]) -> Optional[JiraAction]:
        project_key = ticket.get("project_key")
        summary = ticket.get("summary")
        description = ticket.get("description")

        if not all([project_key, summary, description]):
            logger.warning("Skipping ticket with missing required fields: %s", ticket)
            return None

        issue_type = ticket.get("issue_type", "Task")
        priority = ticket.get("priority", "Medium")
        labels = ticket.get("labels") or ["pm-copilot"]
        due_date = ticket.get("due_date")
        assignee_name = ticket.get("assignee")

        fields: Dict[str, object] = {
            "project": {"key": project_key},
            "summary": summary,
            "description": self._to_adf(str(description)),
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
            "labels": labels,
        }

        if due_date:
            fields["duedate"] = due_date

        if assignee_name:
            account_id = self._lookup_account_id(str(assignee_name))
            if account_id:
                fields["assignee"] = {"id": account_id}

        response = self._session.post(
            f"{self._config.jira_api_base}/issue",
            json={"fields": fields},
            timeout=60,
        )

        if response.status_code >= 300:
            logger.error("Failed to create Jira issue (%s): %s", response.status_code, response.text)
            return None

        data = response.json()
        issue_key = data.get("key")
        logger.info("Created Jira issue %s (%s)", issue_key, summary)
        return JiraAction(key=issue_key, summary=str(summary))

    def _update_issue(self, ticket: Mapping[str, object]) -> Optional[JiraUpdateAction]:
        issue_key = ticket.get("issue_key")
        if not issue_key:
            logger.warning("Skipping update with missing issue_key: %s", ticket)
            return None

        action = JiraUpdateAction(key=str(issue_key))

        comment = ticket.get("comment")
        if comment:
            if self._add_comment(issue_key, str(comment)):
                action.comments_added.append("comment")

        new_status = ticket.get("new_status")
        if new_status:
            if self._transition_issue(issue_key, str(new_status)):
                action.new_status = str(new_status)

        fields = ticket.get("fields") or {}
        if isinstance(fields, Mapping) and fields:
            if self._update_fields(issue_key, fields):
                action.fields_updated.extend(list(fields.keys()))

        if any([action.comments_added, action.new_status, action.fields_updated]):
            return action

        return None

    def _add_comment(self, issue_key: str, comment: str) -> bool:
        response = self._session.post(
            f"{self._config.jira_api_base}/issue/{issue_key}/comment",
            json={"body": self._to_adf(comment)},
            timeout=30,
        )
        if response.status_code >= 300:
            logger.error("Failed to add comment to %s: %s", issue_key, response.text)
            return False
        return True

    def _transition_issue(self, issue_key: str, new_status: str) -> bool:
        transitions = self._session.get(
            f"{self._config.jira_api_base}/issue/{issue_key}/transitions",
            timeout=30,
        )
        if transitions.status_code >= 300:
            logger.error("Failed to fetch transitions for %s: %s", issue_key, transitions.text)
            return False

        transition_id = None
        for transition in transitions.json().get("transitions", []):
            to_status = transition.get("to", {}).get("name", "")
            if to_status.lower() == new_status.lower():
                transition_id = transition.get("id")
                break

        if not transition_id:
            logger.error("No transition found from %s to status '%s'", issue_key, new_status)
            return False

        response = self._session.post(
            f"{self._config.jira_api_base}/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
            timeout=30,
        )
        if response.status_code >= 300:
            logger.error("Failed to transition %s: %s", issue_key, response.text)
            return False

        return True

    def _update_fields(self, issue_key: str, fields: Mapping[str, object]) -> bool:
        payload_fields = dict(fields)
        description_value = payload_fields.get("description")
        if isinstance(description_value, str):
            payload_fields["description"] = self._to_adf(description_value)

        response = self._session.put(
            f"{self._config.jira_api_base}/issue/{issue_key}",
            json={"fields": payload_fields},
            timeout=30,
        )
        if response.status_code >= 300:
            logger.error("Failed to update fields for %s: %s", issue_key, response.text)
            return False
        return True

    def _lookup_account_id(self, name: str) -> Optional[str]:
        if name in self._account_cache:
            return self._account_cache[name]

        response = self._session.get(
            f"{self._config.jira_api_base}/user/search",
            params={"query": name},
            timeout=30,
        )
        if response.status_code >= 300:
            logger.error("Failed to search for Jira user '%s': %s", name, response.text)
            self._account_cache[name] = None
            return None

        users = response.json()
        account_id = users[0]["accountId"] if users else None
        if not account_id:
            logger.warning("Unable to resolve Jira account for '%s'", name)

        self._account_cache[name] = account_id
        return account_id

    @staticmethod
    def _to_adf(text: str) -> Dict[str, object]:
        """Convert plain text into a minimal Atlassian Document Format structure."""

        paragraphs = []
        lines = text.splitlines() or [text]
        for line in lines:
            if line.strip():
                paragraphs.append(
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": line}],
                    }
                )
            else:
                paragraphs.append({"type": "paragraph", "content": []})

        if not paragraphs:
            paragraphs.append({"type": "paragraph", "content": []})

        return {
            "type": "doc",
            "version": 1,
            "content": paragraphs,
        }


__all__ = ["JiraMcpAgent", "JiraSyncResult"]

