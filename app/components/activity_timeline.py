
"""MANTIQ activity timeline component."""

import html
from datetime import datetime

import streamlit as st


ACTION_LABELS = {
    "ALERT_CREATED": "Alert generated",
    "ACKNOWLEDGED": "Alert acknowledged",
    "OPERATOR_FINDINGS_ADDED": "Operator findings recorded",
    "ESCALATED": "Escalated to maintenance",
    "MAINTENANCE_ASSIGNED": "Maintenance assigned",
    "RESOLVED": "Corrective action completed",
    "VERIFIED": "Resolution verified",
    "SEVERITY_UPGRADED": "Severity upgraded",
}

ROLE_LABELS = {
    "system": "System",
    "operator": "Operator",
    "maintenance_head": "Maintenance Head",
}

EVENT_COLORS = {
    "ALERT_CREATED": "#82968D",
    "ACKNOWLEDGED": "#6687B5",
    "OPERATOR_FINDINGS_ADDED": "#6687B5",
    "ESCALATED": "#C18A52",
    "MAINTENANCE_ASSIGNED": "#B3935E",
    "RESOLVED": "#4D9672",
    "VERIFIED": "#4D9672",
    "SEVERITY_UPGRADED": "#C16A58",
}


def _format_timestamp(value):
    """Format an ISO timestamp for local display."""
    if not value:
        return "Time unavailable"

    try:
        parsed = datetime.fromisoformat(
            str(value).replace("Z", "+00:00")
        )
        return parsed.astimezone().strftime(
            "%d %b %Y · %I:%M %p"
        )
    except (ValueError, TypeError):
        return str(value)


def _event_color(activity):
    action = str(activity.get("action", "")).upper()
    return EVENT_COLORS.get(action, "#82968D")


def _event_label(activity):
    action = str(activity.get("action", "")).upper()

    return ACTION_LABELS.get(
        action,
        action.replace("_", " ").title() or "Activity recorded",
    )


def _event_person(activity):
    person = str(activity.get("performed_by") or "Unknown")
    role = str(activity.get("role") or "user").lower()

    role_label = ROLE_LABELS.get(
        role,
        role.replace("_", " ").title(),
    )

    return html.escape(person), html.escape(role_label)


def render_activity_timeline(
    activities,
    *,
    compact=False,
    title=None,
):
    """
    Render actual alert activity as a vertical timeline.

    Full alert timelines should be chronological.
    Dashboard feeds can be passed newest-first.
    """

    if title:
        st.markdown(f"**{html.escape(str(title))}**")

    if not activities:
        st.caption("No activity recorded yet.")
        return

    st.markdown(
        """
        <style>
        .mq-timeline {
            margin: 12px 0 4px 2px;
            padding: 0;
        }

        .mq-timeline-event {
            display: grid;
            grid-template-columns: 14px minmax(0, 1fr);
            column-gap: 12px;
            position: relative;
            padding-bottom: 19px;
        }

        .mq-timeline-event:last-child {
            padding-bottom: 2px;
        }

        .mq-timeline-marker {
            position: relative;
            display: flex;
            justify-content: center;
        }

        .mq-timeline-marker:after {
            content: "";
            position: absolute;
            top: 12px;
            bottom: -5px;
            width: 1px;
            background: var(--border-color);
            opacity: 0.8;
        }

        .mq-timeline-event:last-child
        .mq-timeline-marker:after {
            display: none;
        }

        .mq-timeline-dot {
            width: 8px;
            height: 8px;
            margin-top: 4px;
            border-radius: 50%;
            display: block;
            flex-shrink: 0;
        }

        .mq-timeline-content {
            min-width: 0;
        }

        .mq-timeline-heading {
            font-size: 0.88rem;
            line-height: 1.4;
            font-weight: 650;
            color: var(--text-color);
        }

        .mq-timeline-meta {
            margin-top: 3px;
            font-size: 0.73rem;
            line-height: 1.5;
            color: var(--text-color);
            opacity: 0.62;
        }

        .mq-timeline-details {
            margin-top: 6px;
            padding: 8px 10px;
            border-left: 2px solid var(--border-color);
            border-radius: 0 6px 6px 0;
            background: var(--secondary-background-color);
            font-size: 0.80rem;
            line-height: 1.5;
            color: var(--text-color);
            opacity: 0.88;
            white-space: pre-wrap;
            overflow-wrap: anywhere;
        }

        .mq-timeline-compact {
            margin-top: 8px;
        }

        .mq-timeline-compact .mq-timeline-event {
            padding-bottom: 13px;
        }

        .mq-timeline-compact .mq-timeline-heading {
            font-size: 0.83rem;
        }

        .mq-timeline-compact .mq-timeline-meta {
            font-size: 0.70rem;
        }

        .mq-timeline-compact .mq-timeline-details {
            margin-top: 4px;
            padding: 6px 8px;
            font-size: 0.76rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    timeline_class = (
        "mq-timeline mq-timeline-compact"
        if compact
        else "mq-timeline"
    )

    event_markup = [f'<div class="{timeline_class}">']

    for activity in activities:
        label = html.escape(_event_label(activity))
        person, role = _event_person(activity)

        timestamp = html.escape(
            _format_timestamp(activity.get("created_at"))
        )

        details = str(activity.get("details") or "").strip()
        safe_details = html.escape(details)

        color = _event_color(activity)

        details_markup = (
            f'<div class="mq-timeline-details">{safe_details}</div>'
            if details
            else ""
        )

        event_markup.append(
            f"""
            <div class="mq-timeline-event">
                <div class="mq-timeline-marker">
                    <span class="mq-timeline-dot"
                          style="background:{color};"></span>
                </div>

                <div class="mq-timeline-content">
                    <div class="mq-timeline-heading">
                        {label}
                    </div>

                    <div class="mq-timeline-meta">
                        {person} · {role} · {timestamp}
                    </div>

                    {details_markup}
                </div>
            </div>
            """
        )

    event_markup.append("</div>")

    st.markdown(
        "\n".join(event_markup),
        unsafe_allow_html=True,
    )