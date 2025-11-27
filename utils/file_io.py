"""Helpers for persisting PM Co-Pilot output."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from mavric_pm_copilot.utils.logger import get_logger


logger = get_logger(__name__)


def save_json_to_file(payload: Mapping[str, Any], destination: Path) -> None:
    """
    Persist JSON data to disk.

    Args:
        payload: Serializable mapping object.
        destination: Target file path.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
        f.write("\n")

    logger.info("Saved PM Co-Pilot output to %s", destination)


__all__ = ["save_json_to_file"]

