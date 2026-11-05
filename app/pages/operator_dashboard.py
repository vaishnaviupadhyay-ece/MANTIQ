"""
MANTIQ Operator dashboard.

Provides a focused view of machine condition,
condition trends and maintenance activity.
"""

import streamlit as st

from app.components import dashboard_parts as parts
from app.components import metrics
from app.components.header import data_source_banner, page_header
from app.services import auth_service, replay_service
from app.services import condition_service as cs
from app.services.pipeline import get_pipeline_or_stop


def render() -> None:
    user = auth_service.current_user()

    if user is None:
        st.warning("Please sign in.")
        return

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    page_header(
        "Overview",
        "Monitor bearing health and track maintenance actions."
    )

    data_source_banner(
        show_replay_label=replay_service.is_replaying()
    )

    # -----------------------------------------------------
    # PIPELINE DATA
    # -----------------------------------------------------

    p = get_pipeline_or_stop()
    idx = replay_service.view_index(p)

    snap = cs.snapshot(
        p.conditions,
        p.scored,
        idx,
    )

    # -----------------------------------------------------
    # MACHINE CONDITION
    # -----------------------------------------------------

    parts.pipeline_notices(p)
    parts.position_banner(p, idx)
    parts.condition_summary(snap)

    metrics.section_title("Bearing health")
    parts.bearing_cards(snap)

    # -----------------------------------------------------
    # CONDITION ANALYSIS
    # -----------------------------------------------------

    metrics.section_title("Condition trends")

    parts.score_trend(
        p,
        idx,
        key="operator_score_trend",
    )

    with st.expander("Understanding condition readings"):
        parts.score_explainer()

    # -----------------------------------------------------
    # MAINTENANCE OVERVIEW
    # -----------------------------------------------------

    metrics.section_title("Recent maintenance alerts")
    parts.recent_alerts(limit=5)

    # -----------------------------------------------------
    # RECENT CHANGES AND ACTIVITY
    # -----------------------------------------------------

    left, right = st.columns(2)

    with left:
        metrics.section_title("Condition changes")
        parts.recent_changes(
            p,
            idx,
            limit=5,
        )

    with right:
        metrics.section_title("Maintenance activity")
        parts.maintenance_activity(limit=5)

    # -----------------------------------------------------
    # REPLAY STATUS
    # -----------------------------------------------------

    with st.expander("Historical replay information"):
        parts.replay_status_card(p, idx)