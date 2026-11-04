"""
MANTIQ shared page header and data-source banner.
"""

import html

import streamlit as st

from app.config import DATA_SOURCE_LABEL, REPLAY_LABEL


def page_header(title: str, subtitle: str = None) -> None:
    sub = (f'<div class="mq-page-subtitle">{html.escape(subtitle)}</div>'
           if subtitle else "")
    st.markdown(
        f'<div class="mq-page-title">{html.escape(title)}</div>{sub}',
        unsafe_allow_html=True,
    )


def data_source_banner(show_replay_label: bool = False) -> None:
    """One-line banner naming the data source. Timestamps shown anywhere in
    the app are original 2003 dataset times, and this banner says so."""
    parts = [f"<strong>Data source:</strong> {html.escape(DATA_SOURCE_LABEL)}"]
    if show_replay_label:
        parts.append(f"<strong>{html.escape(REPLAY_LABEL)}</strong>")
    parts.append("Timestamps are original dataset times, not current time.")
    st.markdown(
        '<div class="mq-banner">' + " &nbsp;·&nbsp; ".join(parts) + "</div>",
        unsafe_allow_html=True,
    )