"""Streamlit dashboard for running the MeetGeek → Gemini PM Co-Pilot pipeline."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import streamlit as st

from mavric_pm_copilot.ai.gemini_client import GeminiClient
from mavric_pm_copilot.config import load_config
from mavric_pm_copilot.jira.mcp_agent import JiraMcpAgent, JiraSyncResult
from mavric_pm_copilot.meetgeek.client import MeetGeekClient
from mavric_pm_copilot.notifications.slack_notifier import send_slack_summary
from mavric_pm_copilot.utils.file_io import save_json_to_file
from mavric_pm_copilot.utils.logger import get_logger


logger = get_logger(__name__)
ASSETS_DIR = Path(__file__).resolve().parent / "assets"


def _service_logo(col, filename: str, title: str, subtitle: str, emoji: str) -> None:
    """
    Render a service logo if present in assets, otherwise fall back to an emoji.

    Expected filenames (placed under ui/assets/):
      - config.png
      - meetgeek.png
      - gemini.png
      - jira.png
      - slack.png
    """

    image_path = ASSETS_DIR / filename
    if image_path.is_file():
        col.image(str(image_path), width=56)
    else:
        col.markdown(
            f"<div style='font-size:40px; text-align:center;'>{emoji}</div>",
            unsafe_allow_html=True,
        )

    col.markdown(f"**{title}**  \n`{subtitle}`", unsafe_allow_html=False)


def _run_pipeline_with_progress() -> Dict[str, Any]:
    """Run the pipeline step-by-step, returning the final model output."""

    progress = st.progress(0, text="Initializing…")
    step_total = 5
    step = 0

    # Step 1: Load configuration
    st.subheader("Step 1 — Load configuration")
    try:
        config = load_config()
        st.success("Configuration loaded from environment.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to load configuration")
        st.error(f"Failed to load configuration: {exc}")
        progress.empty()
        raise
    step += 1
    progress.progress(step / step_total, text="Configuration loaded")

    # Step 2: Fetch MeetGeek summary
    st.subheader("Step 2 — Fetch MeetGeek summary")
    try:
        meetgeek_client = MeetGeekClient(config.meetgeek_api_key)
        transcript_text = meetgeek_client.fetch_summary(config.meetgeek_meeting_id)
        st.success("MeetGeek summary fetched successfully.")
        with st.expander("Raw MeetGeek transcript / summary", expanded=False):
            st.text_area(
                "Transcript",
                value=transcript_text,
                height=200,
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to fetch MeetGeek summary")
        st.error(f"Failed to fetch MeetGeek summary: {exc}")
        progress.empty()
        raise
    step += 1
    progress.progress(step / step_total, text="MeetGeek summary fetched")

    # Step 3: Analyze with Gemini
    st.subheader("Step 3 — Analyze with Gemini")
    try:
        gemini_client = GeminiClient(config.gemini_api_key, config.model_name)
        result: Dict[str, Any] = gemini_client.analyze_transcript(transcript_text)
        st.success("Gemini analysis completed.")
        with st.expander("Gemini JSON output", expanded=True):
            st.json(result)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Gemini analysis failed")
        st.error(f"Gemini analysis failed: {exc}")
        progress.empty()
        raise
    step += 1
    progress.progress(step / step_total, text="Gemini analysis complete")

    # Step 4: Sync Jira from payload
    st.subheader("Step 4 — Sync Jira")
    jira_result: JiraSyncResult | None = None
    try:
        jira_payload: Dict[str, Any] = result.get("jira")  # type: ignore[assignment]
        if not jira_payload:
            raise ValueError("Gemini output missing required 'jira' object.")

        jira_agent = JiraMcpAgent(config)
        jira_result = jira_agent.sync_from_payload(jira_payload)
        st.success("Jira synchronization completed.")

        with st.expander("Jira actions summary", expanded=False):
            created = [
                {"key": a.key, "summary": a.summary} for a in jira_result.created
            ]
            updated = [
                {
                    "key": a.key,
                    "new_status": a.new_status,
                    "comments_added": a.comments_added,
                    "fields_updated": a.fields_updated,
                }
                for a in jira_result.updated
            ]
            summary_view = {
                "created": created,
                "updated": updated,
                "unresolved_assignees": jira_result.unresolved_assignees,
            }
            st.json(summary_view)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Jira synchronization failed")
        st.error(f"Jira synchronization failed: {exc}")
        progress.empty()
        raise
    step += 1
    progress.progress(step / step_total, text="Jira sync complete")

    # Step 5: Save JSON + send Slack summary
    st.subheader("Step 5 — Persist output & notify Slack")
    try:
        save_json_to_file(result, config.output_path)
        st.success(f"JSON output saved to {Path(config.output_path).resolve()}")

        send_slack_summary(
            webhook_url=config.slack_webhook_url,
            meeting_id=config.meetgeek_meeting_id,
            model_output=result,
            jira_result=jira_result or JiraSyncResult(),
            jira_base_url=config.jira_base_url,
        )
        st.success("Slack summary sent.")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed during persistence / Slack notification")
        st.error(f"Failed during persistence / Slack notification: {exc}")
        progress.empty()
        raise
    step += 1
    progress.progress(step / step_total, text="Pipeline completed")

    return result


def main() -> None:
    """Render the Streamlit dashboard."""

    st.set_page_config(
        page_title="Mavric PM Co-Pilot",
        page_icon="🧠",
        layout="wide",
    )

    # Header
    st.title("Mavric PM Co-Pilot")
    st.caption("MeetGeek → Gemini → Jira → Slack")

    # Workflow map (like a make.com graph, but linear, with logos where available)
    with st.container(border=True):
        cols = st.columns(5)
        _service_logo(cols[0], "config.png", "Config", "ENV", "🛠️")
        _service_logo(cols[1], "meetgeek.png", "MeetGeek", "meetgeek.ai", "🎥")
        _service_logo(cols[2], "gemini.png", "Gemini", "google-generativeai", "✨")
        _service_logo(cols[3], "jira.png", "Jira", "atlassian.com", "📌")
        _service_logo(cols[4], "slack.png", "Slack", "slack.com", "💬")

    st.markdown(
        """
This dashboard runs the PM Co-Pilot pipeline and shows each stage as it executes.
Use **Run Pipeline** to execute once with the current environment configuration.
"""
    )

    # Layout: left = controls, right = step-by-step log
    col_left, col_right = st.columns([1, 3], gap="large")

    with col_left:
        st.subheader("Controls")
        run_clicked = st.button("Run Pipeline", type="primary", use_container_width=True)

        st.divider()
        st.markdown("#### Latest run")
        if "last_run_raw" in st.session_state:
            st.download_button(
                "Download last JSON output",
                data=st.session_state["last_run_raw"],
                file_name="pm_copilot_output.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.info("Run the pipeline once to enable JSON download.")

    with col_right:
        st.subheader("Workflow execution")
        st.markdown(
            "_Each step below will light up with status, similar to a workflow run in make.com._"
        )

        if run_clicked:
            try:
                result = _run_pipeline_with_progress()
                st.session_state["last_run_raw"] = json.dumps(result, indent=2)
                st.success("Pipeline finished successfully.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Pipeline failed: {exc}")


if __name__ == "__main__":
    main()

 