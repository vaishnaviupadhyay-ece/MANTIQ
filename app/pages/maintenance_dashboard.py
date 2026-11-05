"""
MANTIQ Maintenance Head dashboard.

Focuses on maintenance workload, machine priorities
and completion of maintenance actions.
"""

import streamlit as st

from app.components import dashboard_parts as parts
from app.components import metrics
from app.components.header import data_source_banner, page_header
from app.config import ROLE_HEAD
from app.services import auth_service, replay_service
from app.services import condition_service as cs
from app.services.pipeline import get_pipeline_or_stop


def render() -> None:
    user = auth_service.current_user()

    try:
        auth_service.require_role(user, ROLE_HEAD)
    except PermissionError as exc:
        st.error(str(exc))
        return

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    page_header(
        "Overview",
        "Maintenance priorities, active work and verification."
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

    parts.pipeline_notices(p)
    parts.position_banner(p, idx)
    parts.condition_summary(snap)

    # -----------------------------------------------------
    # MAINTENANCE WORKLOAD
    # -----------------------------------------------------

    metrics.section_title("Maintenance workload")

    parts.workflow_cards([
        "Pending acknowledgements",
        "Unassigned maintenance work",
        "Active maintenance tasks",
        "Pending verification",
    ])

    # -----------------------------------------------------
    # PRIORITY COMPONENTS
    # -----------------------------------------------------

    metrics.section_title("Components requiring attention")
    parts.attention_table(snap)

    # -----------------------------------------------------
    # ALERT MANAGEMENT
    # -----------------------------------------------------

    metrics.section_title("Recent maintenance alerts")
    parts.recent_alerts(limit=6)

    # -----------------------------------------------------
    # CONDITION ANALYSIS
    # -----------------------------------------------------

    metrics.section_title("Condition history")

    parts.condition_history(
        p,
        idx,
        key="head_condition_history",
    )

    metrics.section_title("Anomaly trends")

    parts.rate_trend(
        p,
        idx,
        key="head_rate_trend",
    )

    with st.expander("Understanding condition readings"):
        parts.score_explainer()

    # -----------------------------------------------------
    # ACTIVITY AND CONDITION CHANGES
    # -----------------------------------------------------

    left, right = st.columns(2)

    with left:
        metrics.section_title("Maintenance activity")
        parts.maintenance_activity(limit=6)

    with right:
        metrics.section_title("Recent condition changes")
        parts.recent_changes(
            p,
            idx,
            limit=6,
        )

    # -----------------------------------------------------
    # REPLAY INFORMATION
    # -----------------------------------------------------

    with st.expander("Historical replay information"):
        parts.replay_status_card(p, idx)