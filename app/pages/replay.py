
"""MANTIQ historical replay page."""

import streamlit as st
import pandas as pd

from app.components.header import data_source_banner, page_header
from app.config import REPLAY_LABEL
from app.services import auth_service, replay_service
from app.services import condition_service as cs
from app.services.pipeline import get_pipeline_or_stop


@st.fragment(run_every=1.0)
def _replay_controls(p):
    total = len(p.conditions)

    if total == 0:
        st.error("No replay recordings are available.")
        return

    st.markdown("### Replay controls")

    current_status = replay_service.status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button(
            "Start",
            disabled=current_status != replay_service.STATUS_IDLE,
            use_container_width=True,
        ):
            replay_service.start(p)

    with col2:
        if st.button(
            "Pause",
            disabled=current_status != replay_service.STATUS_RUNNING,
            use_container_width=True,
        ):
            replay_service.pause()

    with col3:
        if st.button(
            "Resume",
            disabled=current_status != replay_service.STATUS_PAUSED,
            use_container_width=True,
        ):
            replay_service.resume()

    with col4:
        if st.button(
            "Reset",
            disabled=current_status == replay_service.STATUS_IDLE,
            use_container_width=True,
        ):
            replay_service.reset()

    selected_speed = st.select_slider(
        "Playback speed (recordings per second)",
        options=[1, 2, 5, 10, 20],
        value=replay_service.speed(),
        key="replay_speed_selector",
    )

    replay_service.set_speed(selected_speed)

    # Automatically advance while replay is running.
    if replay_service.status() == replay_service.STATUS_RUNNING:
        replay_service.advance(p, replay_service.speed())

    idx = replay_service.view_index(p)
    row = p.conditions.iloc[idx]

    recording = int(row["recording"])

    st.divider()

    st.markdown("### Playback status")

    c1, c2, c3 = st.columns(3)

    c1.metric("Status", replay_service.status_label())
    c2.metric("Recording", f"{recording:,} / {total:,}")
    c3.metric("Historical timestamp", str(row["timestamp"]))

    if replay_service.status() != replay_service.STATUS_IDLE:
        st.progress((idx + 1) / total)
    else:
        st.info("Replay has not started. Press Start to begin from recording 1.")

    st.caption(REPLAY_LABEL)

    st.divider()

    st.markdown("### Current machine condition")

    snapshot = cs.snapshot(p.conditions, p.scored, idx)

    c1, c2, c3 = st.columns(3)

    c1.metric("Overall condition", snapshot["overall"])

    warning_count = sum(
        item["condition"] == "WARNING"
        for item in snapshot["bearings"].values()
    )

    critical_count = sum(
        item["condition"] == "CRITICAL"
        for item in snapshot["bearings"].values()
    )

    c2.metric("Warning bearings", warning_count)
    c3.metric("Critical bearings", critical_count)

    st.markdown("#### Bearing-level readings")

    bearing_rows = []

    for bearing, info in snapshot["bearings"].items():
        bearing_rows.append({
            "Bearing": f"Bearing {bearing}",
            "Condition": info["condition"],
            "Anomaly rate": f"{info['anomaly_rate'] * 100:.1f}%",
            "Average anomaly score": f"{info['avg_score']:+.4f}",
            "Consecutive flags": info["streak"],
            "Suggested action": info["action"],
        })

    st.dataframe(
        pd.DataFrame(bearing_rows),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "The displayed values are calculated from historical NASA IMS "
        "recordings. They are not live sensor readings."
    )

    if replay_service.status() == replay_service.STATUS_FINISHED:
        st.success("Historical replay completed.")


def render():
    user = auth_service.current_user()

    if user is None:
        st.warning("Please sign in.")
        return

    page_header(
        "Historical Replay",
        "Run historical bearing recordings through the trained models",
    )

    data_source_banner(show_replay_label=True)

    p = get_pipeline_or_stop()

    if not p.integrity.ok:
        st.warning(p.integrity.message)

    _replay_controls(p)