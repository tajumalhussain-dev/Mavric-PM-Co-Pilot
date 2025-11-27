"""Configuration loading for the PM Co-Pilot application."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    """Namespace for environment-driven settings."""

    gemini_api_key: str
    meetgeek_api_key: str
    meetgeek_meeting_id: str
    jira_cloud_id: str
    jira_email: str
    jira_api_token: str
    slack_webhook_url: str
    model_name: str = "models/gemini-flash-latest"
    output_path: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent / "pm_copilot_output.json"
    )

    @property
    def jira_api_base(self) -> str:
        """Base REST URL for Atlassian Cloud API access."""

        return f"https://api.atlassian.com/ex/jira/{self.jira_cloud_id}/rest/api/3"


def load_config() -> AppConfig:
    """Load environment variables, validating that required values exist."""

    load_dotenv()

    gemini_key = os.getenv("GEMINI_API_KEY")
    meetgeek_key = os.getenv("MEETGEEK_API_KEY")
    meeting_id = os.getenv("MEETGEEK_MEETING_ID")
    jira_cloud_id = os.getenv("JIRA_CLOUD_ID")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")
    slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")

    missing = {
        name: value
        for name, value in {
            "GEMINI_API_KEY": gemini_key,
            "MEETGEEK_API_KEY": meetgeek_key,
            "MEETGEEK_MEETING_ID": meeting_id,
            "JIRA_CLOUD_ID": jira_cloud_id,
            "JIRA_EMAIL": jira_email,
            "JIRA_API_TOKEN": jira_api_token,
            "SLACK_WEBHOOK_URL": slack_webhook_url,
        }.items()
        if not value
    }

    if missing:
        missing_keys = ", ".join(sorted(missing.keys()))
        raise ValueError(f"Missing required environment variables: {missing_keys}")

    return AppConfig(
        gemini_api_key=gemini_key,
        meetgeek_api_key=meetgeek_key,
        meetgeek_meeting_id=meeting_id,
        jira_cloud_id=jira_cloud_id,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
        slack_webhook_url=slack_webhook_url,
    )


__all__ = ["AppConfig", "load_config"]

