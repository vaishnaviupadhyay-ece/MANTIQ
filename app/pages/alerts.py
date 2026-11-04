
import streamlit as st
import pandas as pd

from app.database.alert_service import (
    get_all_alerts,
    get_alert_activity,
    acknowledge_alert,
    add_operator_findings,
    escalate_alert,
    assign_maintenance,
    resolve_alert,
    verify_alert,
    AlertError,
)


def render_alerts(user):
    st.title("Alerts")
    st.caption("Machine condition alerts and maintenance tracking")

    username = user.username
    role = user.role

    try:
        alerts = get_all_alerts()
    except Exception as exc:
        st.error(f"Could not load alerts: {exc}")
        return

    if not alerts:
        st.info("No alerts generated yet. Start historical replay to monitor bearing conditions.")
        return

    df = pd.DataFrame(alerts)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total alerts", len(df))
    col2.metric("Open alerts", len(df[df["status"] != "VERIFIED"]))
    col3.metric("Critical alerts", len(df[df["severity"] == "CRITICAL"]))

    st.divider()

    status_filter = st.selectbox(
        "Filter by status",
        ["All", "NEW", "ACKNOWLEDGED", "UNDER MAINTENANCE", "RESOLVED", "VERIFIED"],
    )

    if status_filter != "All":
        df = df[df["status"] == status_filter]

    severity_filter = st.selectbox(
        "Filter by severity",
        ["All", "CRITICAL", "WARNING"],
    )

    if severity_filter != "All":
        df = df[df["severity"] == severity_filter]

    if df.empty:
        st.info("No alerts match these filters.")
        return

    for _, alert in df.iterrows():
        with st.expander(
            f"{alert['alert_code']} | Bearing {alert['bearing']} | "
            f"{alert['severity']} | {alert['status']}"
        ):
            st.write(f"**Created:** {alert['created_at']}")
            st.write(f"**Historical recording:** {alert['recording_timestamp']}")
            st.write(f"**Anomaly score:** {alert['anomaly_score']}")
            st.write(f"**Condition:** {alert['condition_label']}")
            st.write(f"**Assigned to:** {alert['assigned_to'] or 'Unassigned'}")

            if alert["operator_findings"]:
                st.write("**Operator findings:**")
                st.write(alert["operator_findings"])

            if alert["corrective_action"]:
                st.write("**Corrective action:**")
                st.write(alert["corrective_action"])

            st.divider()

            if role == "operator":
                if alert["status"] == "NEW":
                    if st.button("Acknowledge", key=f"ack_{alert['id']}"):
                        try:
                            acknowledge_alert(alert["id"], username, role)
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

                findings = st.text_area(
                    "Add machine findings",
                    key=f"findings_{alert['id']}",
                )

                if st.button("Save findings", key=f"save_{alert['id']}"):
                    try:
                        add_operator_findings(
                            alert["id"], username, role, findings
                        )
                        st.success("Findings saved.")
                        st.rerun()
                    except AlertError as exc:
                        st.error(str(exc))

                if alert["status"] not in {"RESOLVED", "VERIFIED"}:
                    reason = st.text_input(
                        "Escalation reason",
                        key=f"reason_{alert['id']}",
                    )
                    if st.button("Escalate", key=f"escalate_{alert['id']}"):
                        try:
                            escalate_alert(
                                alert["id"], username, role, reason
                            )
                            st.success("Escalated to maintenance head.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

            elif role == "maintenance_head":
                if alert["status"] not in {"RESOLVED", "VERIFIED"}:
                    assigned_to = st.text_input(
                        "Assign to",
                        key=f"assign_{alert['id']}",
                    )
                    instructions = st.text_area(
                        "Maintenance instructions",
                        key=f"instructions_{alert['id']}",
                    )

                    if st.button("Assign maintenance", key=f"assign_btn_{alert['id']}"):
                        try:
                            assign_maintenance(
                                alert["id"],
                                username,
                                role,
                                assigned_to,
                                instructions,
                            )
                            st.success("Maintenance assigned.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

                if alert["status"] == "UNDER MAINTENANCE":
                    action = st.text_area(
                        "Corrective action taken",
                        key=f"action_{alert['id']}",
                    )

                    if st.button("Mark resolved", key=f"resolve_{alert['id']}"):
                        try:
                            resolve_alert(
                                alert["id"], username, role, action
                            )
                            st.success("Alert marked resolved.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

                if alert["status"] == "RESOLVED":
                    notes = st.text_area(
                        "Verification notes",
                        key=f"verify_{alert['id']}",
                    )

                    if st.button("Verify and close", key=f"verify_btn_{alert['id']}"):
                        try:
                            verify_alert(
                                alert["id"], username, role, notes
                            )
                            st.success("Alert verified and closed.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

            st.divider()
            st.write("**Activity history**")

            activities = get_alert_activity(alert["id"])

            for activity in activities:
                st.caption(
                    f"{activity['created_at']} · "
                    f"{activity['performed_by']} · "
                    f"{activity['action']}"
                )
                if activity["details"]:
                    st.write(activity["details"])
