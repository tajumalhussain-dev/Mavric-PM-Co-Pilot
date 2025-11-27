"""Utility helpers for configuring application logging."""

from __future__ import annotations

import logging
from typing import Optional


_CONFIGURED = False


def _configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a logger instance with consistent configuration."""

    _configure_logging()
    return logging.getLogger(name or "mavric_pm_copilot")


__all__ = ["get_logger"]

