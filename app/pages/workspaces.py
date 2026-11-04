
"""MANTIQ functional pages shared by Operator and Maintenance Head."""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.components.header import data_source_banner, page_header
from app.config import (
    APP_NAME,
    DATA_SOURCE_LABEL,
    CONDITION_WINDOW,
    TRAIN_FRACTION,
    BEARINGS,
)
from app.services import auth_service, replay_service
from app.services import condition_service as cs
from app.services.pipeline import get_pipeline_or_stop
from app.services.data_service import feature_columns
from app.database.alert_service import (
    get_all_alerts,
    get_alert_activity,
    assign_maintenance,
    resolve_alert,
    verify_alert,
    AlertError,
)


def _head_only(user):
    if user is None:
        st.warning("Please sign in.")
        return False

    try:
        auth_service.require_role(user, "maintenance_head")
        return True
    except PermissionError as exc:
        st.error(str(exc))
        return False


def _page_start(title, subtitle):
    user = auth_service.current_user()

    if user is None:
        st.warning("Please sign in.")
        return None

    page_header(title, subtitle)
    data_source_banner(show_replay_label=replay_service.is_replaying())

    return user


def render_machines():
    user = _page_start(
        "Machines",
        "Bearing test rig · individual component monitoring",
    )

    if user is None:
        return

    p = get_pipeline_or_stop()
    idx = replay_service.view_index(p)
    snapshot = cs.snapshot(p.conditions, p.scored, idx)

    st.markdown("### Machine overview")

    st.info(
        "NASA IMS historical bearing experiment. "
        "This prototype does not connect to a physical machine."
    )

    bearing = st.selectbox(
        "Select bearing",
        BEARINGS,
        format_func=lambda value: f"Bearing {value}",
    )

    info = snapshot["bearings"][bearing]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Condition", info["condition"])
    c2.metric("Anomaly rate", f"{info['anomaly_rate'] * 100:.1f}%")
    c3.metric("Average anomaly score", f"{info['avg_score']:+.4f}")
    c4.metric("Consecutive flags", info["streak"])

    st.markdown("### Current assessment")
    st.write(info["action"])

    st.caption(
        f"Latest historical recording: {snapshot['recording']} · "
        f"{snapshot['timestamp']}"
    )

    st.divider()
    st.markdown("### Vibration trend")

    rms_columns = [
        column
        for column in feature_columns(bearing)
        if "rms" in column.lower()
    ]

    if rms_columns:
        history = p.features.iloc[:idx + 1].tail(500)

        chart_data = history[["time"] + rms_columns].copy()

        fig = px.line(
            chart_data,
            x="time",
            y=rms_columns,
            title=f"Bearing {bearing} · RMS vibration by channel",
            labels={
                "time": "Historical timestamp",
                "value": "RMS vibration (dataset units)",
                "variable": "Channel",
            },
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(
            "RMS feature columns could not be identified in the loaded dataset."
        )

    st.markdown("### Anomaly score trend")

    score_column = f"bearing_{bearing}_score"

    score_data = p.scored.iloc[:idx + 1].tail(500)

    if score_column in score_data.columns:
        fig = px.line(
            score_data,
            x="time",
            y=score_column,
            title=f"Bearing {bearing} · Isolation Forest score",
            labels={
                "time": "Historical timestamp",
                score_column: "Anomaly score",
            },
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            annotation_text="Anomaly threshold",
        )

        st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Lower Isolation Forest scores indicate more unusual recordings. "
        "Anomaly flags are not proof of a mechanical defect."
    )


def render_maintenance():
    user = _page_start(
        "Maintenance",
        "Maintenance work orders, corrective actions and verification",
    )

    if user is None:
        return

    is_head = user.role == "maintenance_head"
    alerts = get_all_alerts()

    active = [
        alert for alert in alerts
        if alert["status"] not in {"VERIFIED"}
    ]

    c1, c2, c3 = st.columns(3)

    c1.metric("Open work items", len(active))
    c2.metric(
        "Under maintenance",
        sum(a["status"] == "UNDER MAINTENANCE" for a in alerts),
    )
    c3.metric(
        "Awaiting verification",
        sum(a["status"] == "RESOLVED" for a in alerts),
    )

    st.divider()

    if not active:
        st.info(
            "No active maintenance work orders. "
            "Alerts will appear here when generated during replay."
        )
        return

    for alert in active:
        with st.expander(
            f"{alert['alert_code']} · Bearing {alert['bearing']} · "
            f"{alert['severity']} · {alert['status']}"
        ):
            st.write(f"**Assigned to:** {alert['assigned_to'] or 'Unassigned'}")
            st.write(f"**Operator findings:** {alert['operator_findings'] or 'Not provided'}")
            st.write(f"**Historical recording:** {alert['recording_timestamp']}")

            if alert["corrective_action"]:
                st.write(
                    f"**Corrective action:** {alert['corrective_action']}"
                )

            if is_head and alert["status"] not in {"RESOLVED", "VERIFIED"}:
                assignee = st.text_input(
                    "Assign maintenance to",
                    key=f"maintenance_assignee_{alert['id']}",
                )

                instructions = st.text_area(
                    "Work instructions",
                    key=f"maintenance_instructions_{alert['id']}",
                )

                if st.button(
                    "Assign / update work",
                    key=f"maintenance_assign_{alert['id']}",
                ):
                    try:
                        assign_maintenance(
                            alert["id"],
                            user.username,
                            user.role,
                            assignee,
                            instructions,
                        )
                        st.success("Maintenance assignment saved.")
                        st.rerun()
                    except AlertError as exc:
                        st.error(str(exc))

            if is_head and alert["status"] == "UNDER MAINTENANCE":
                action = st.text_area(
                    "Corrective action performed",
                    key=f"maintenance_action_{alert['id']}",
                )

                if st.button(
                    "Mark resolved",
                    key=f"maintenance_resolve_{alert['id']}",
                ):
                    try:
                        resolve_alert(
                            alert["id"],
                            user.username,
                            user.role,
                            action,
                        )
                        st.success("Work marked as resolved.")
                        st.rerun()
                    except AlertError as exc:
                        st.error(str(exc))

            if is_head and alert["status"] == "RESOLVED":
                notes = st.text_area(
                    "Verification notes",
                    key=f"maintenance_verify_notes_{alert['id']}",
                )

                if st.button(
                    "Verify and close",
                    key=f"maintenance_verify_{alert['id']}",
                ):
                    try:
                        verify_alert(
                            alert["id"],
                            user.username,
                            user.role,
                            notes,
                        )
                        st.success("Maintenance verified.")
                        st.rerun()
                    except AlertError as exc:
                        st.error(str(exc))

            activities = get_alert_activity(alert["id"])

            if activities:
                st.markdown("**Work order activity**")

                for activity in activities:
                    st.caption(
                        f"{activity['created_at']} · "
                        f"{activity['action']} · "
                        f"{activity['performed_by']}"
                    )


def render_history():
    user = _page_start(
        "History",
        "Historical alerts and maintenance activity audit trail",
    )

    if user is None:
        return

    alerts = get_all_alerts()

    if not alerts:
        st.info("No alert history is available yet.")
        return

    st.markdown("### Alert history")

    status_options = [
        "All",
        "NEW",
        "ACKNOWLEDGED",
        "UNDER MAINTENANCE",
        "RESOLVED",
        "VERIFIED",
    ]

    selected_status = st.selectbox(
        "Filter by status",
        status_options,
        key="history_status_filter",
    )

    filtered = [
        alert for alert in alerts
        if selected_status == "All"
        or alert["status"] == selected_status
    ]

    if filtered:
        table = pd.DataFrame(filtered)

        columns = [
            "alert_code",
            "bearing",
            "severity",
            "status",
            "created_at",
            "recording_timestamp",
            "assigned_to",
        ]

        st.dataframe(
            table[columns],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No alerts match this filter.")

    st.divider()
    st.markdown("### Activity timeline")

    activities = []

    for alert in alerts:
        for activity in get_alert_activity(alert["id"]):
            activities.append({
                "Alert": alert["alert_code"],
                "Bearing": alert["bearing"],
                "Action": activity["action"],
                "Person": activity["performed_by"],
                "Role": activity["role"],
                "Time": activity["created_at"],
                "Details": activity["details"],
            })

    activities.sort(
        key=lambda item: item["Time"],
        reverse=True,
    )

    if activities:
        st.dataframe(
            pd.DataFrame(activities),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No activity entries have been recorded.")


def render_team_assignments():
    user = auth_service.current_user()

    if not _head_only(user):
        return

    page_header(
        "Team / Assignments",
        "Maintenance workload and assigned personnel",
    )

    alerts = get_all_alerts()

    assigned = [
        alert for alert in alerts
        if alert["assigned_to"]
    ]

    if not assigned:
        st.info(
            "No maintenance assignments yet. "
            "Assign personnel from the Maintenance page."
        )
        return

    rows = []

    for alert in assigned:
        rows.append({
            "Alert": alert["alert_code"],
            "Bearing": alert["bearing"],
            "Severity": alert["severity"],
            "Assigned to": alert["assigned_to"],
            "Status": alert["status"],
            "Created": alert["created_at"],
        })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Assignments are based on recorded alert work orders. "
        "This prototype does not yet maintain a separate employee directory."
    )


def render_analytics():
    user = auth_service.current_user()

    if not _head_only(user):
        return

    page_header(
        "Analytics",
        "Historical model behaviour and maintenance statistics",
    )

    p = get_pipeline_or_stop()
    idx = replay_service.view_index(p)

    alerts = get_all_alerts()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Dataset recordings", f"{len(p.scored):,}")
    c2.metric("Tracked alerts", len(alerts))
    c3.metric(
        "Critical alerts",
        sum(a["severity"] == "CRITICAL" for a in alerts),
    )
    c4.metric(
        "Verified alerts",
        sum(a["status"] == "VERIFIED" for a in alerts),
    )

    st.divider()
    st.markdown("### Bearing anomaly score trends")

    score_columns = [
        f"bearing_{bearing}_score"
        for bearing in BEARINGS
        if f"bearing_{bearing}_score" in p.scored.columns
    ]

    if score_columns:
        data = p.scored.iloc[:idx + 1].tail(1000)

        fig = px.line(
            data,
            x="time",
            y=score_columns,
            title="Isolation Forest anomaly scores",
            labels={
                "time": "Historical timestamp",
                "value": "Anomaly score",
                "variable": "Bearing",
            },
        )

        fig.add_hline(y=0, line_dash="dash")

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Condition history")

    from app.components import charts

    charts.show(
        charts.condition_strip_chart(
            p.conditions,
            max(0, p.split.first_test_index),
            idx,
        ),
        key="analytics_condition_history",
    )

    st.caption(
        "The model scores and condition history are calculated from "
        "the historical NASA IMS recordings. These are not live "
        "production-machine statistics."
    )

    st.divider()
    st.markdown("### Alert severity distribution")

    if alerts:
        severity_data = pd.DataFrame(alerts)

        counts = (
            severity_data["severity"]
            .value_counts()
            .rename_axis("Severity")
            .reset_index(name="Alerts")
        )

        fig = px.bar(
            counts,
            x="Severity",
            y="Alerts",
            title="Tracked alert severity",
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tracked alerts are available for analysis yet.")


def render_configuration():
    user = auth_service.current_user()

    if not _head_only(user):
        return

    page_header(
        "Configuration",
        "MANTIQ prototype settings and model information",
    )

    st.markdown("### Application")

    st.write(f"**Application:** {APP_NAME}")
    st.write(f"**Data source:** {DATA_SOURCE_LABEL}")
    st.write("**Replay mode:** Historical dataset replay")
    st.write("**Database:** SQLite")
    st.write("**Machine:** NASA IMS bearing test rig")

    st.divider()
    st.markdown("### Model configuration")

    st.write(f"**Training fraction:** {TRAIN_FRACTION * 100:.0f}%")
    st.write(f"**Condition window:** {CONDITION_WINDOW} recordings")
    st.write("**Model:** Isolation Forest")
    st.write("**Models:** One model per bearing")
    st.write("**Anomaly threshold:** Score below zero")

    st.divider()
    st.markdown("### Condition assessment rules")

    st.write(
        "- CRITICAL: anomaly rate at least 75%, or average score "
        "below -0.10 with at least 5 consecutive anomaly flags."
    )

    st.write(
        "- WARNING: anomaly rate at least 20%, or average score "
        "below 0.05 with at least 3 consecutive anomaly flags."
    )

    st.write(
        "- NORMAL: neither Warning nor Critical rule is triggered."
    )

    st.warning(
        "These are prototype heuristics, not validated industrial "
        "thresholds. Do not use them as the sole basis for machine "
        "safety or shutdown decisions."
    )

    st.divider()
    st.markdown("### Access roles")

    st.write("**Operator:** view machine conditions, acknowledge alerts, add findings and escalate.")
    st.write("**Maintenance Head:** manage assignments, corrective actions and verification.")
