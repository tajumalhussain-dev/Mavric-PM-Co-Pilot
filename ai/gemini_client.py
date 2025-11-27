"""Gemini client used for meeting analysis."""

from __future__ import annotations

import json
from typing import Any, Dict

import google.generativeai as genai

from mavric_pm_copilot.utils.logger import get_logger


SYSTEM_PROMPT = r"""
You must always include a "jira" object with this exact structure:

"jira": {
  "tickets_to_create": [
    {
      "project_key": "string, e.g. SCRUM. If unknown, use SCRUM",
      "summary": "short ticket title (string, required)",
      "description": "2–4 sentence description of the work (string, required)",
      "issue_type": "Task | Story | Bug (string, default to Task if not clear)",
      "assignee": "person name (string) or null if unknown",
      "priority": "High | Medium | Low (string, default Medium)",
      "labels": ["array", "of", "strings"],
      "due_date": "YYYY-MM-DD or null"
    }
  ],
  "tickets_to_update": [
    {
      "issue_key": "e.g. SCRUM-210 (string, required)",
      "comment": "comment to add (string) or null",
      "new_status": "In Progress | Blocked | Done | null",
      "fields": {
        "optional_field_key": "optional_field_value"
      }
    }
  ]
}

Rules for Jira JSON:
- Always include both arrays: "tickets_to_create" and "tickets_to_update".
- If nothing to create/update → return [].
- project_key, summary, description MUST be non-empty strings.
- If missing, defaults:
  - project_key = "SCRUM"
  - issue_type = "Task"
  - priority = "Medium"
  - assignee = null
  - due_date = null
  - labels = ["pm-copilot"]

VERY IMPORTANT:
- Final output must be a **single valid JSON object**.
- No markdown, no backticks, no trailing commas.
- Must be directly parseable by Python json.loads.
"""


class GeminiClient:
    """Thin wrapper around the Gemini GenerativeModel."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self._logger = get_logger(self.__class__.__name__)
        genai.configure(api_key=api_key)
        self._model = genai.GenerativeModel(model_name)

    def analyze_transcript(self, transcript: str) -> Dict[str, Any]:
        """
        Call Gemini with the provided transcript and return parsed JSON.

        Raises:
            json.JSONDecodeError: if the model response is not valid JSON.
            Exception: bubbles up errors from the Gemini SDK.
        """

        self._logger.info("Invoking Gemini analysis")
        prompt = f"{SYSTEM_PROMPT}\n\nTranscript:\n{transcript}"

        try:
            response = self._model.generate_content(prompt)
        except Exception:
            self._logger.exception("Error calling Gemini")
            raise

        text = response.text.strip()
        self._logger.debug("Gemini raw response: %s", text)

        try:
            parsed: Dict[str, Any] = json.loads(text)
        except json.JSONDecodeError:
            self._logger.error("Failed to parse Gemini output as JSON")
            raise

        return parsed


__all__ = ["GeminiClient", "SYSTEM_PROMPT"]

