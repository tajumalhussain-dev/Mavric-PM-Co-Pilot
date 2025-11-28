"""Entry point for the MeetGeek → Gemini PM Co-Pilot pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mavric_pm_copilot.ai.gemini_client import GeminiClient
from mavric_pm_copilot.config import load_config
from mavric_pm_copilot.jira.mcp_agent import JiraMcpAgent
from mavric_pm_copilot.meetgeek.client import MeetGeekClient
from mavric_pm_copilot.notifications.slack_notifier import send_slack_summary
from mavric_pm_copilot.utils.file_io import save_json_to_file
from mavric_pm_copilot.utils.logger import get_logger


logger = get_logger(__name__)


def run() -> None:
    """Execute the pipeline end-to-end."""

    config = load_config()
    meetgeek_client = MeetGeekClient(config.meetgeek_api_key)
    gemini_client = GeminiClient(config.gemini_api_key, config.model_name)
    jira_agent = JiraMcpAgent(config)

    logger.info("=== Running MeetGeek → Gemini PM Co-Pilot ===")

    transcript_text = meetgeek_client.fetch_summary(config.meetgeek_meeting_id)
    result = gemini_client.analyze_transcript(transcript_text)

    print("\n=== FINAL AI JSON OUTPUT ===")
    print(json.dumps(result, indent=2))

    save_json_to_file(result, config.output_path)

    jira_payload: Dict[str, Any] = result.get("jira")
    if not jira_payload:
        raise ValueError("Gemini output missing required 'jira' object.")

    jira_result = jira_agent.sync_from_payload(jira_payload)

    send_slack_summary(
    webhook_url=config.slack_webhook_url,
    meeting_id=config.meetgeek_meeting_id,
    model_output=result,
    jira_result=jira_result,
    )


if __name__ == "__main__":
    run()

