import html

import pandas as pd
import streamlit as st

from app.database.alert_service import (
    get_all_alerts,
    acknowledge_alert,
    add_operator_findings,
    escalate_alert,
    assign_maintenance,
    resolve_alert,
    verify_alert,
    AlertError,
)

def _severity_badge(severity):
    colors = {
        "CRITICAL": ("#FCE8E6", "#B93832"),
        "WARNING": ("#FFF2D9", "#A66B13"),
    }

    background, foreground = colors.get(
        str(severity).upper(),
        ("#E8EDF5", "#526B8A"),
    )

    label = html.escape(str(severity).upper())

    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:4px 10px;
            border-radius:20px;
            background:{background};
            color:{foreground};
            font-size:0.72rem;
            font-weight:700;
            letter-spacing:0.04em;
        ">{label}</span>
        """,
        unsafe_allow_html=True,
    )


def _status_badge(status):
    colors = {
        "NEW": ("#FCE8E6", "#B93832"),
        "ACKNOWLEDGED": ("#E8EDF5", "#526B8A"),
        "UNDER MAINTENANCE": ("#E5EDF7", "#456B9A"),
        "RESOLVED": ("#E4F1E9", "#347653"),
        "VERIFIED": ("#DCECE3", "#286847"),
    }

    background, foreground = colors.get(
        str(status).upper(),
        ("#EEEEEE", "#555555"),
    )

    label = html.escape(str(status).replace("_", " ").upper())

    st.markdown(
        f"""
        <span style="
            display:inline-block;
            padding:4px 10px;
            border-radius:20px;
            background:{background};
            color:{foreground};
            font-size:0.72rem;
            font-weight:600;
        ">{label}</span>
        """,
        unsafe_allow_html=True,
    )


def _render_alert_details(alert, username, role):
    alert_id = alert["id"]

    # -----------------------------------------------------
    # ALERT INFORMATION
    # -----------------------------------------------------

    left, right = st.columns(2)

    with left:
        st.caption("Alert created")
        st.write(str(alert["created_at"]))

        st.caption("Historical recording")
        st.write(str(alert["recording_timestamp"]))

        st.caption("Anomaly score")
        st.write(str(alert["anomaly_score"]))

    with right:
        st.caption("Condition assessment")
        st.write(str(alert["condition_label"]))

        st.caption("Assigned to")
        st.write(alert["assigned_to"] or "Unassigned")

        st.caption("Alert status")
        _status_badge(alert["status"])

    st.divider()

    # -----------------------------------------------------
    # OPERATOR FINDINGS
    # -----------------------------------------------------

    st.markdown("**Operator findings**")

    if alert["operator_findings"]:
        st.info(alert["operator_findings"])
    else:
        st.caption("No operator findings recorded yet.")

    # -----------------------------------------------------
    # CORRECTIVE ACTION
    # -----------------------------------------------------

    if alert["corrective_action"]:
        st.markdown("**Corrective action recorded**")
        st.write(alert["corrective_action"])

    # -----------------------------------------------------
    # OPERATOR WORKFLOW
    # -----------------------------------------------------

    if role == "operator":
        st.divider()
        st.markdown("**Operator actions**")

        # Acknowledge only once
        if alert["status"] == "NEW":
            if st.button(
                "Acknowledge alert",
                key=f"ack_{alert_id}",
                type="primary",
            ):
                try:
                    acknowledge_alert(alert_id, username, role)
                    st.success("Alert acknowledged.")
                    st.rerun()
                except AlertError as exc:
                    st.error(str(exc))

        elif alert["status"] != "NEW":
            st.caption("This alert has already been acknowledged.")

        # Findings can be updated while alert is open
        if alert["status"] not in {"RESOLVED", "VERIFIED"}:
            with st.form(key=f"findings_form_{alert_id}"):
                findings = st.text_area(
                    "Add or update operator findings",
                    value="",
                    placeholder=(
                        "Describe unusual vibration, noise, heat, "
                        "visible damage or other observations..."
                    ),
                    height=110,
                )

                save_findings = st.form_submit_button(
                    "Save findings",
                    use_container_width=True,
                )

                if save_findings:
                    if not findings.strip():
                        st.warning("Please enter your findings first.")
                    else:
                        try:
                            add_operator_findings(
                                alert_id,
                                username,
                                role,
                                findings.strip(),
                            )
                            st.success("Operator findings saved.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

        # Escalation is allowed only once
        if (
            alert["status"] not in {"RESOLVED", "VERIFIED"}
            and not bool(alert.get("escalated", 0))
        ):
            with st.form(key=f"escalate_form_{alert_id}"):
                reason = st.text_area(
                    "Escalation reason",
                    placeholder=(
                        "Explain why this alert needs "
                        "maintenance-head attention..."
                    ),
                    height=80,
                )

                escalate = st.form_submit_button(
                    "Escalate to Maintenance Head",
                    use_container_width=True,
                )

                if escalate:
                    if not reason.strip():
                        st.warning("Please provide an escalation reason.")
                    else:
                        try:
                            escalate_alert(
                                alert_id,
                                username,
                                role,
                                reason.strip(),
                            )
                            st.success("Alert escalated.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

        elif bool(alert.get("escalated", 0)):
            st.success(
                "Already escalated to the Maintenance Head."
            )

    # -----------------------------------------------------
    # MAINTENANCE HEAD WORKFLOW
    # -----------------------------------------------------

    elif role == "maintenance_head":
        st.divider()
        st.markdown("**Maintenance management**")

        if alert["status"] not in {"RESOLVED", "VERIFIED"}:
            with st.form(key=f"assign_form_{alert_id}"):
                assigned_to = st.text_input(
                    "Assign maintenance to",
                    value=alert["assigned_to"] or "",
                    placeholder="Technician or responsible person",
                )

                instructions = st.text_area(
                    "Maintenance instructions",
                    placeholder=(
                        "Describe the inspection or maintenance "
                        "work required..."
                    ),
                    height=100,
                )

                assign = st.form_submit_button(
                    "Assign maintenance",
                    use_container_width=True,
                )

                if assign:
                    if not assigned_to.strip():
                        st.warning("Please enter the assigned technician.")
                    else:
                        try:
                            assign_maintenance(
                                alert_id,
                                username,
                                role,
                                assigned_to.strip(),
                                instructions.strip(),
                            )
                            st.success("Maintenance assignment saved.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

        if alert["status"] == "UNDER MAINTENANCE":
            with st.form(key=f"resolve_form_{alert_id}"):
                action = st.text_area(
                    "Corrective action performed",
                    placeholder=(
                        "Record what was inspected, repaired "
                        "or replaced..."
                    ),
                    height=110,
                )

                resolve = st.form_submit_button(
                    "Mark as resolved",
                    use_container_width=True,
                )

                if resolve:
                    if not action.strip():
                        st.warning("Please describe the corrective action.")
                    else:
                        try:
                            resolve_alert(
                                alert_id,
                                username,
                                role,
                                action.strip(),
                            )
                            st.success("Maintenance marked as resolved.")
                            st.rerun()
                        except AlertError as exc:
                            st.error(str(exc))

        if alert["status"] == "RESOLVED":
            with st.form(key=f"verify_form_{alert_id}"):
                notes = st.text_area(
                    "Verification notes",
                    placeholder="Record the verification outcome...",
                    height=100,
                )

                verify = st.form_submit_button(
                    "Verify and close alert",
                    use_container_width=True,
                )

                if verify:
                    try:
                        verify_alert(
                            alert_id,
                            username,
                            role,
                            notes.strip(),
                        )
                        st.success("Alert verified and closed.")
                        st.rerun()
                    except AlertError as exc:
                        st.error(str(exc))


def render_alerts(user):
    st.title("Alerts")
    st.caption(
        "Machine condition alerts and maintenance tracking"
    )

    username = user.username
    role = user.role

    try:
        alerts = get_all_alerts()
    except Exception as exc:
        st.error(f"Could not load alerts: {exc}")
        return

    if not alerts:
        st.info(
            "No alerts generated yet. Start historical replay "
            "to monitor bearing conditions."
        )
        return

    df = pd.DataFrame(alerts)

    # -----------------------------------------------------
    # ALERT SUMMARY
    # -----------------------------------------------------

    total = len(df)
    open_count = len(df[df["status"] != "VERIFIED"])
    critical_count = len(df[df["severity"] == "CRITICAL"])

    col1, col2, col3 = st.columns(3)

    col1.metric("Total alerts", total)
    col2.metric("Open alerts", open_count)
    col3.metric("Critical alerts", critical_count)

    st.divider()

    # -----------------------------------------------------
    # FILTERS
    # -----------------------------------------------------

    filter1, filter2 = st.columns(2)

    with filter1:
        status_filter = st.selectbox(
            "Filter by status",
            [
                "All",
                "NEW",
                "ACKNOWLEDGED",
                "UNDER MAINTENANCE",
                "RESOLVED",
                "VERIFIED",
            ],
            key="alerts_status_filter",
        )

    with filter2:
        severity_filter = st.selectbox(
            "Filter by severity",
            ["All", "CRITICAL", "WARNING"],
            key="alerts_severity_filter",
        )

    if status_filter != "All":
        df = df[df["status"] == status_filter]

    if severity_filter != "All":
        df = df[df["severity"] == severity_filter]

    st.caption(f"Showing {len(df)} alert(s)")

    if df.empty:
        st.info("No alerts match these filters.")
        return

    # -----------------------------------------------------
    # ALERT LIST
    # -----------------------------------------------------

    for _, alert in df.iterrows():
        severity = str(alert["severity"]).upper()
        status = str(alert["status"]).replace("_", " ").upper()

        title = (
            f"{alert['alert_code']}  ·  "
            f"B{alert['bearing']}  ·  "
            f"{severity}  ·  {status}"
        )

        with st.expander(title):
            _render_alert_details(
                alert,
                username,
                role,
            )