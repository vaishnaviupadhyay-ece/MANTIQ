"""
Shared building blocks for the Operator and Maintenance Head dashboards.

ML data comes from the historical NASA IMS pipeline.
Alert and maintenance data comes from the MANTIQ SQLite database.
"""

import html

import pandas as pd
import streamlit as st

from app.components import charts, metrics
from app.config import (
    BEARINGS,
    CONDITION_WINDOW,
    REPLAY_LABEL,
    TIMESTAMP_FORMAT,
)
from app.services import condition_service as cs
from app.services import replay_service
from app.database.alert_service import (
    get_all_alerts,
    get_alert_activity,
)

CONDITIONS = ("NORMAL", "WARNING", "CRITICAL")


def safe(value) -> str:
    """Escape values before displaying them in HTML."""
    return html.escape(str(value if value is not None else ""))


def fmt_time(ts) -> str:
    return pd.Timestamp(ts).strftime("%d %b %Y, %H:%M:%S")


def period_start(p, idx: int) -> int:
    """First row to draw in trend charts."""
    first = p.split.first_test_index
    return first if idx >= first else 0


def pipeline_notices(p) -> None:
    if not p.integrity.ok:
        st.warning(p.integrity.message)

    if p.notes:
        with st.expander("Data notes"):
            for item in p.notes:
                st.write(item)


def position_banner(p, idx: int) -> None:
    row = p.conditions.iloc[idx]
    recording, total = int(row["recording"]), len(p.conditions)

    if replay_service.is_replaying():
        lead = (
            f"<strong>Replay position:</strong> "
            f"Recording {recording} of {total}"
        )
    else:
        lead = (
            f"<strong>Latest available recording</strong> "
            f"({recording} of {total}); replay has not been started"
        )

    in_test = idx >= p.split.first_test_index

    period = (
        "Unseen test period"
        if in_test
        else "Training period: models have already seen this data"
    )

    items = [
        lead,
        f"Original dataset time <strong>{fmt_time(row['time'])}</strong> "
        f"(historical, not current time)",
        period,
    ]

    window = int(row["window_size"])

    if window < CONDITION_WINDOW:
        items.append(
            f"Condition window filling: "
            f"{window}/{CONDITION_WINDOW} recordings"
        )

    st.markdown(
        '<div class="mq-banner">'
        + " &nbsp;·&nbsp; ".join(items)
        + "</div>",
        unsafe_allow_html=True,
    )


def condition_summary(snap: dict) -> None:
    """Overall condition and Normal / Warning / Critical counts."""

    total = len(snap["bearings"])

    counts = {
        condition: sum(
            1
            for bearing in snap["bearings"].values()
            if bearing["condition"] == condition
        )
        for condition in CONDITIONS
    }

    overall = snap["overall"]
    key = overall.lower()

    cols = st.columns(4)

    cols[0].markdown(
        metrics.card_html(
            "Overall machine condition",
            f'<span style="color:var(--{key})">'
            f'{safe(overall.title())}</span>',
            f"Worst condition across {total} monitored bearings",
            status=key,
        ),
        unsafe_allow_html=True,
    )

    for col, condition in zip(cols[1:], CONDITIONS):
        col.markdown(
            metrics.card_html(
                f"{condition.title()} components",
                str(counts[condition]),
                f"Out of {total} bearings",
                status=condition.lower(),
            ),
            unsafe_allow_html=True,
        )


def bearing_cards(snap: dict) -> None:
    cols = st.columns(len(BEARINGS))

    for col, bearing in zip(cols, BEARINGS):
        col.markdown(
            metrics.bearing_card_html(
                bearing,
                snap["bearings"][bearing],
                snap["window_size"],
            ),
            unsafe_allow_html=True,
        )


def score_trend(p, idx: int, key: str, n: int = 300) -> None:
    start = max(0, idx - n + 1)

    charts.show(
        charts.score_trend_chart(
            p.scored,
            start,
            idx,
            p.split.first_test_index,
        ),
        key=key,
    )

    metrics.note(
        "Original dataset times (2003). Lower scores indicate more "
        "unusual recordings. Scores below the dashed zero line are "
        "flagged as anomalies; a flag alone does not prove a defect."
    )


def rate_trend(p, idx: int, key: str) -> None:
    start = period_start(p, idx)

    charts.show(
        charts.anomaly_rate_chart(
            p.conditions,
            start,
            idx,
            p.split.first_test_index,
        ),
        key=key,
    )

    metrics.note(
        "Share of the latest 50 recordings flagged as anomalous. "
        "Condition rules also consider average anomaly score "
        "and consecutive anomaly flags."
    )


def condition_history(p, idx: int, key: str) -> None:
    start = period_start(p, idx)

    charts.show(
        charts.condition_strip_chart(
            p.conditions,
            start,
            idx,
        ),
        key=key,
    )

    metrics.note(
        "Condition assigned to each bearing at every recording, "
        "using the latest 50 recordings. These are prototype "
        "heuristics, not validated industrial limits."
    )


def recent_changes(p, idx, limit: int = 8) -> None:
    """Show the latest model-assessed condition transitions."""

    first = p.split.first_test_index

    trans = (
        cs.transitions_between(p.conditions, first, idx)
        if idx > first
        else pd.DataFrame()
    )

    if trans.empty:
        metrics.empty_state(
            "No condition changes have been detected up to this recording."
        )
        return

    latest = trans.tail(limit).iloc[::-1]
    rows = []

    for _, r in latest.iterrows():
        when = pd.to_datetime(
            r["timestamp"],
            format=TIMESTAMP_FORMAT,
        )

        rows.append({
            "recording": int(r["recording"]),
            "time": fmt_time(when),
            "bearing": f"Bearing {int(r['bearing'])}",
            "change": (
                f"{metrics.condition_badge(r['from_condition'])} "
                f"→ {metrics.condition_badge(r['to_condition'])}"
            ),
            "direction": (
                "Worsened"
                if r["change"] == "WORSENED"
                else "Improved"
            ),
        })

    columns = [
        ("recording", "Recording"),
        ("time", "Original dataset time"),
        ("bearing", "Bearing"),
        ("change", "Change"),
        ("direction", "Direction"),
    ]

    metrics.render_table(
        columns,
        rows,
        html_columns=("change",),
    )

    metrics.note(
        f"Showing {len(latest)} of {len(trans)} condition changes. "
        "These are model-assessed transitions, separate from "
        "tracked maintenance alerts."
    )


def attention_table(snap: dict) -> None:
    """Show bearings that need attention."""

    items = [
        (bearing, info)
        for bearing, info in snap["bearings"].items()
        if info["condition"] != "NORMAL"
    ]

    if not items:
        metrics.empty_state(
            "All bearings are Normal under the condition rules "
            "at this recording."
        )
        return

    items.sort(
        key=lambda item: cs.SEVERITY_RANK[item[1]["condition"]],
        reverse=True,
    )

    rows = [{
        "bearing": f"Bearing {bearing}",
        "condition": metrics.condition_badge(info["condition"]),
        "rate": f"{info['anomaly_rate'] * 100:.1f}%",
        "score": f"{info['avg_score']:+.4f}",
        "streak": f"{info['streak']} recordings",
        "action": info["action"],
    } for bearing, info in items]

    columns = [
        ("bearing", "Bearing"),
        ("condition", "Condition"),
        ("rate", f"Flagged (latest {snap['window_size']})"),
        ("score", "Average score"),
        ("streak", "Current anomaly streak"),
        ("action", "Suggested action"),
    ]

    metrics.render_table(
        columns,
        rows,
        html_columns=("condition",),
    )


# ---------------------------------------------------------
# DATABASE-CONNECTED ALERT AND MAINTENANCE COMPONENTS
# ---------------------------------------------------------

def workflow_cards(titles: list) -> None:
    """Display maintenance workload counts from SQLite."""

    try:
        alerts = get_all_alerts()

        counts = {
            "Pending acknowledgements": sum(
                alert["status"] == "NEW"
                for alert in alerts
            ),
            "Unassigned maintenance work": sum(
                alert["status"] not in ("RESOLVED", "VERIFIED")
                and not alert["assigned_to"]
                for alert in alerts
            ),
            "Active maintenance tasks": sum(
                alert["status"] == "UNDER MAINTENANCE"
                for alert in alerts
            ),
            "Pending verification": sum(
                alert["status"] == "RESOLVED"
                for alert in alerts
            ),
        }

        cols = st.columns(len(titles))

        for col, title in zip(cols, titles):
            col.markdown(
                metrics.card_html(
                    title,
                    str(counts.get(title, 0)),
                    "Tracked maintenance alerts",
                ),
                unsafe_allow_html=True,
            )

    except Exception as exc:
        st.error(f"Could not load maintenance workload: {exc}")


def recent_alerts(limit: int = 5) -> None:
    """Display actual maintenance alerts from the database."""

    try:
        alerts = get_all_alerts()

        if not alerts:
            metrics.empty_state(
                "No maintenance alerts have been recorded yet."
            )
            return

        for alert in alerts[:limit]:
            with st.container(border=True):
                left, middle, right = st.columns([2, 1, 1])

                with left:
                    st.markdown(f"**{safe(alert['alert_code'])}**")
                    st.caption(f"Bearing {int(alert['bearing'])}")

                with middle:
                    st.markdown(
                        metrics.condition_badge(alert["severity"]),
                        unsafe_allow_html=True,
                    )

                with right:
                    st.markdown(f"**{safe(alert['status'])}**")

                assigned = alert.get("assigned_to") or "Unassigned"

                st.caption(
                    f"Created: {safe(alert['created_at'])}"
                    f"  ·  Assigned to: {safe(assigned)}"
                )

    except Exception as exc:
        st.error(f"Could not load maintenance alerts: {exc}")


def maintenance_activity(limit: int = 8) -> None:
    """Display recent maintenance actions from the activity log."""

    try:
        alerts = get_all_alerts()
        activities = []

        for alert in alerts:
            for activity in get_alert_activity(alert["id"]):
                activities.append({
                    **activity,
                    "alert_code": alert["alert_code"],
                    "bearing": alert["bearing"],
                })

        activities.sort(
            key=lambda item: (
                item["created_at"],
                item["id"],
            ),
            reverse=True,
        )

        if not activities:
            metrics.empty_state(
                "Maintenance actions will appear here as alerts "
                "are acknowledged, assigned, resolved and verified."
            )
            return

        for activity in activities[:limit]:
            with st.container(border=True):
                action = activity["action"].replace(
                    "_", " "
                ).title()

                st.markdown(
                    f"**{safe(action)}**"
                    f"  ·  {safe(activity['alert_code'])}"
                )

                st.caption(
                    f"Bearing {int(activity['bearing'])}"
                    f"  ·  {safe(activity['created_at'])}"
                )

                st.caption(
                    f"{safe(activity['performed_by'])}"
                    f"  ·  {safe(activity['role'])}"
                )

                if activity.get("details"):
                    st.write(activity["details"])

    except Exception as exc:
        st.error(f"Could not load maintenance activity: {exc}")


# ---------------------------------------------------------
# HISTORICAL REPLAY DISPLAY
# ---------------------------------------------------------

def replay_status_card(p, idx: int) -> None:
    """Show the current position in the historical dataset."""

    if replay_service.is_replaying():
        sub = (
            f"Recording "
            f"{int(p.conditions['recording'].iloc[idx])} "
            f"of {len(p.conditions)}"
        )
    else:
        sub = (
            "Showing the last recording in the dataset. "
            "Replay controls are managed separately."
        )

    sub += f"<br><strong>{safe(REPLAY_LABEL)}</strong>"

    metrics.render_card(
        "Historical replay",
        safe(replay_service.status_label()),
        sub,
    )


def score_explainer() -> None:
    """Explain the model outputs and condition rules."""

    st.markdown(
        "- Each bearing has an Isolation Forest model trained on "
        "the **first 60% of recordings** (the training period).\n"
        "- Lower anomaly scores indicate more unusual recordings.\n"
        "- A score below 0 is flagged as an anomaly.\n"
        "- The approximately 5% training contamination is a model "
        "setting, not measured accuracy.\n"
        "- An anomaly flag does not prove a bearing defect.\n"
        "- Normal, Warning and Critical conditions use heuristic "
        "rules applied to the latest 50 recordings.\n"
        "- These are not validated industrial limits or estimates "
        "of remaining useful life."
    )