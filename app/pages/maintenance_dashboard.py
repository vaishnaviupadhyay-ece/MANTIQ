"""
MANTIQ Maintenance Head dashboard (Overview page for the Maintenance Head role).

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
        auth_service.require_role(user, ROLE_HEAD)   # enforced here, not only in the sidebar
    except PermissionError as exc:
        st.error(str(exc))
        return

    page_header("Overview", "Maintenance Head workspace · operational view")
    data_source_banner(show_replay_label=replay_service.is_replaying())

    p = get_pipeline_or_stop()
    idx = replay_service.view_index(p)
    snap = cs.snapshot(p.conditions, p.scored, idx)

    parts.pipeline_notices(p)
    parts.position_banner(p, idx)
    parts.condition_summary(snap)

    metrics.section_title("Maintenance workload")
    parts.workflow_cards(["Pending acknowledgements", "Unassigned maintenance work",
                          "Active maintenance tasks", "Pending verification"])

    metrics.section_title("Critical and warning components")
    parts.attention_table(snap)

    metrics.section_title("Condition history")
    parts.condition_history(p, idx, key="head_condition_history")

    metrics.section_title("Anomaly rate trend")
    parts.rate_trend(p, idx, key="head_rate_trend")
    parts.score_explainer()

    metrics.section_title("Recent condition changes")
    parts.recent_changes(p, idx, limit=10)

    left, right = st.columns(2)
    with left:
        metrics.section_title("Maintenance activity timeline")
        parts.maintenance_activity_empty()
    with right:
        metrics.section_title("Historical replay")
        parts.replay_status_card(p, idx)