"""MeetGeek API client."""

from __future__ import annotations

import json
from typing import Any, Dict

import requests

from mavric_pm_copilot.utils.logger import get_logger


class MeetGeekClient:
    """Lightweight wrapper around the MeetGeek summary endpoint."""

    BASE_URL = "https://api.meetgeek.ai/v1"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._logger = get_logger(self.__class__.__name__)

    def fetch_summary(self, meeting_id: str) -> str:
        """
        Retrieve AI insights and summary text for a meeting.

        Raises:
            requests.HTTPError: if the response status is not 2xx.
            ValueError: if no usable text is returned.
        """

        self._logger.info("Fetching summary for meeting '%s'", meeting_id)

        url = f"{self.BASE_URL}/meetings/{meeting_id}/summary"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        response = requests.get(url, headers=headers, timeout=30)
        try:
            response.raise_for_status()
        except requests.HTTPError:
            self._logger.error(
                "MeetGeek API error %s: %s", response.status_code, response.text
            )
            raise

        data: Dict[str, Any] = response.json()

        ai_insights = data.get("ai_insights", "")
        summary = data.get("summary", "")

        if not ai_insights and not summary:
            self._logger.warning("MeetGeek returned no usable text. Payload:\n%s", json.dumps(data, indent=2))
            raise ValueError("No usable text found in MeetGeek response.")

        self._logger.info("Summary fetched successfully.")
        return f"AI Insights: {ai_insights}\n\nSummary: {summary}"


__all__ = ["MeetGeekClient"]

