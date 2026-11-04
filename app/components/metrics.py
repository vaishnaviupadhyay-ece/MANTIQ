"""
MANTIQ metric cards, condition badges, empty states and HTML tables.

"""

import html

import streamlit as st

_KNOWN = ("normal", "warning", "critical", "offline")


def condition_badge(condition: str) -> str:
    key = str(condition).lower()
    if key not in _KNOWN:
        key = "offline"
    return f'<span class="mq-badge mq-badge-{key}">{html.escape(str(condition).upper())}</span>'


def card_html(title: str, value: str, sub: str = "", status: str = None) -> str:
    css = "mq-card" + (f" mq-status-{status.lower()}" if status else "")
    sub_html = f'<div class="mq-metric-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="{css}"><div class="mq-card-title">{html.escape(title)}</div>'
        f'<div class="mq-metric-value">{value}</div>{sub_html}</div>'
    )


def bearing_card_html(bearing: int, info: dict, window_size: int) -> str:
    """One bearing's health card. `info` comes from condition_service.snapshot()."""
    condition = info["condition"]
    flag = "Flagged as anomalous" if info["latest_flag"] else "Not flagged"
    return (
        f'<div class="mq-card mq-status-{condition.lower()}">'
        f'<div class="mq-bearing-head"><span class="mq-bearing-name">Bearing {bearing}</span>'
        f"{condition_badge(condition)}</div>"
        f'<div class="mq-kv"><span>Latest anomaly score</span><span>{info["latest_score"]:+.4f}</span></div>'
        f'<div class="mq-kv"><span>Latest recording</span><span>{flag}</span></div>'
        f'<div class="mq-kv"><span>Flagged in last {window_size}</span>'
        f'<span>{info["anomaly_rate"] * 100:.1f}%</span></div>'
        f'<div class="mq-kv"><span>Longest flagged run</span><span>{info["streak"]} recordings</span></div>'
        f'<div class="mq-action"><strong>Suggested action:</strong> {html.escape(info["action"])}</div>'
        f"</div>"
    )


def section_title(text: str) -> None:
    st.markdown(f'<div class="mq-section-title">{html.escape(text)}</div>', unsafe_allow_html=True)


def note(text_html: str) -> None:
    st.markdown(f'<div class="mq-note">{text_html}</div>', unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="mq-empty">{html.escape(message)}</div>', unsafe_allow_html=True)


def render_card(title: str, value: str, sub: str = "", status: str = None) -> None:
    st.markdown(card_html(title, value, sub, status), unsafe_allow_html=True)


def html_table(columns: list, rows: list, html_columns: tuple = ()) -> str:
    """columns: [(key, label), ...]; rows: [{key: value}, ...].
    Cell text is HTML-escaped unless its column key is listed in html_columns."""
    head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
    body = ""
    for row in rows:
        cells = ""
        for key, _ in columns:
            value = row.get(key, "")
            text = str(value) if key in html_columns else html.escape(str(value))
            cells += f"<td>{text}</td>"
        body += f"<tr>{cells}</tr>"
    return (f'<div class="mq-table-wrap"><table class="mq-table"><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def render_table(columns: list, rows: list, html_columns: tuple = ()) -> None:
    st.markdown(html_table(columns, rows, html_columns), unsafe_allow_html=True)