"""
MANTIQ Operator dashboard (Overview page for the Operator role).

Real data: conditions, scores and trends from the pipeline.
Not connected yet: alert workflow and maintenance activity (Stage 6),
replay controls (Stage 7). Those areas say so on screen.
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

    page_header("Overview", "Operator workspace · machine condition at a glance")
    data_source_banner(show_replay_label=replay_service.is_replaying())

    p = get_pipeline_or_stop()
    idx = replay_service.view_index(p)
    snap = cs.snapshot(p.conditions, p.scored, idx)

    parts.pipeline_notices(p)
    parts.position_banner(p, idx)
    parts.condition_summary(snap)

    metrics.section_title("Bearing health")
    parts.bearing_cards(snap)

    metrics.section_title("Recent anomaly trends")
    parts.score_trend(p, idx, key="operator_score_trend")
    parts.score_explainer()

    metrics.section_title("Recent alerts")
    metrics.empty_state("No alerts recorded. The alert workflow (acknowledge, record findings, escalate) "
                        "is connected in Stage 6. Until then, the table below shows the condition "
                        "changes the rule engine has detected in the data.")
    st.write("")
    parts.recent_changes(p, idx, limit=8)

    left, right = st.columns(2)
    with left:
        metrics.section_title("Maintenance activity")
        parts.maintenance_activity_empty()
    with right:
        metrics.section_title("Historical replay")
        parts.replay_status_card(p, idx)