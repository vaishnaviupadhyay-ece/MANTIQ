
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
            f"recording {recording} of {total}"
        )
    else:
        lead = (
            f"<strong>Showing the last recording in the dataset</strong> "
            f"(recording {recording} of {total}); "
            f"the replay has not been started"
        )

    in_test = idx >= p.split.first_test_index

    period = (
        "unseen test period"
        if in_test
        else "training period: the models have already seen this data"
    )

    items = [
        lead,
        f"original dataset time <strong>{fmt_time(row['time'])}</strong> "
        f"(historical, not current time)",
        period,
    ]

    window = int(row["window_size"])

    if window < CONDITION_WINDOW:
        items.append(
            f"condition window still filling "
            f"({window} of {CONDITION_WINDOW} recordings)"
        )

    st.markdown(
        '<div class="mq-banner">'
        + " &nbsp;·&nbsp; ".join(items)
        + "</div>",
        unsafe_allow_html=True,
    )

    st.write("")


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
            f'{overall.title()}</span>',
            f"Worst condition among the {total} bearings",
            status=key,
        ),
        unsafe_allow_html=True,
    )

    for col, condition in zip(cols[1:], CONDITIONS):
        col.markdown(
            metrics.card_html(
                f"{condition.title()} components",
                str(counts[condition]),
                f"of {total} bearings",
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
        "Original dataset times (2003). Lower scores are more unusual, "
        "and a recording below the dashed line (0) is flagged. "
        "A flag on its own does not prove a bearing defect."
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
        "The dotted lines are the anomaly-rate thresholds in the "
        "condition rules. Conditions also depend on average score "
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
        "Condition of each bearing at every recording, based on "
        "the latest 50 recordings. These are heuristic rules, "
        "not validated industrial limits."
    )


def recent_changes(p, idx: int, limit: int = 8) -> None:
    first = p.split.first_test_index

    trans = (
        cs.transitions_between(p.conditions, first, idx)
        if idx > first
        else pd.DataFrame()
    )

    if len(trans) == 0:
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
                f"→ "
                f"{metrics.condition_badge(r['to_condition'])}"
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
        f"Latest {len(latest)} of {len(trans)} condition changes detected. "
        "Condition changes and tracked maintenance alerts are separate records."
    )


def attention_table(snap: dict) -> None:
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
        ("streak", "Longest flagged run"),
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
                    "From tracked maintenance alerts",
                ),
                unsafe_allow_html=True,
            )

    except Exception as exc:
        st.error(f"Could not load maintenance workload: {exc}")


def recent_alerts(limit: int = 5) -> None:
    """Display the most recently created tracked alerts."""

    try:
        alerts = get_all_alerts()

        if not alerts:
            metrics.empty_state(
                "No alerts recorded yet. Historical replay can generate "
                "alerts when a bearing enters Warning or Critical."
            )
            return

        for alert in alerts[:limit]:
            st.markdown(
                f"**{html.escape(str(alert['alert_code']))}** "
                f"· Bearing {int(alert['bearing'])} · "
                f"{metrics.condition_badge(alert['severity'])}",
                unsafe_allow_html=True,
            )

            st.caption(
                f"{alert['status']} · "
                f"Created {alert['created_at']}"
            )

    except Exception as exc:
        st.error(f"Could not load recent alerts: {exc}")


def maintenance_activity_empty() -> None:
    """Display recent events from the SQLite activity log."""

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
                "No maintenance activity recorded yet. "
                "Activity will appear here when alerts are acknowledged, "
                "assigned, updated or verified."
            )
            return

        for activity in activities[:8]:
            st.markdown(
                f"**{activity['action'].replace('_', ' ').title()}** "
                f"· {html.escape(str(activity['alert_code']))} "
                f"· Bearing {int(activity['bearing'])}"
            )

            st.caption(
                f"{activity['created_at']} · "
                f"{activity['performed_by']} "
                f"({activity['role']})"
            )

            if activity["details"]:
                st.write(activity["details"])

            st.divider()

    except Exception as exc:
        st.error(f"Could not load maintenance activity: {exc}")


# ---------------------------------------------------------
# HISTORICAL REPLAY DISPLAY
# ---------------------------------------------------------

def replay_status_card(p, idx: int) -> None:
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

    sub += f"<br><strong>{html.escape(REPLAY_LABEL)}</strong>"

    metrics.render_card(
        "Historical replay",
        html.escape(replay_service.status_label()),
        sub,
    )


def score_explainer() -> None:
    with st.expander(
        "How to read the anomaly score and conditions"
    ):
        st.markdown(
            "- Each bearing has an Isolation Forest model trained on "
            "the **first 60% of recordings** (the training period).\n"
            "- The **anomaly score** shows how unusual a recording looks "
            "compared with the training data. **Lower scores are more unusual.**\n"
            "- A score below 0 is flagged as an anomaly.\n"
            "- The model was configured with approximately 5% training "
            "contamination; this is a model setting, not measured accuracy.\n"
            "- **An anomaly flag does not prove a bearing defect.**\n"
            "- A bearing's condition (Normal, Warning, Critical) comes "
            "from rules applied to the latest 50 recordings: anomaly rate, "
            "average score and consecutive anomaly flags.\n"
            "- These conditions are heuristics, not validated industrial "
            "limits or estimates of remaining useful life."
        )
