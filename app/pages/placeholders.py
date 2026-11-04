"""
MANTIQ placeholder pages 

"""

import html

import streamlit as st

from app.components.header import data_source_banner, page_header
from app.config import NAV_HEAD_ONLY, ROLE_HEAD
from app.services import auth_service

# page name: (subtitle, stage that replaces it, show the replay label?)
_INFO = {
    "Overview": ("Machine condition at a glance", 3, False),
    "Machines": ("Bearing test rig and individual bearings", 5, False),
    "Replay": ("Replay the recorded NASA IMS data through the trained models", 7, True),
    "Alerts": ("Alert queue and lifecycle", 6, False),
    "Maintenance": ("Maintenance tasks and progress", 6, False),
    "History": ("Searchable maintenance history", 8, False),
    "Team / Assignments": ("Assign and track maintenance work", 6, False),
    "Analytics": ("Condition trends and maintenance analytics", 5, False),
    "Configuration": ("Application settings", None, False),
}


def _card(title: str, value: str, sub_html: str) -> str:
    return (
        f'<div class="mq-card"><div class="mq-card-title">{html.escape(title)}</div>'
        f'<div class="mq-metric-value">{value}</div>'
        f'<div class="mq-metric-sub">{sub_html}</div></div>'
    )


def _style_preview() -> None:
    """Colours and card style only. There are no real numbers here."""
    cols = st.columns(3)
    for col, (label, key) in zip(
        cols, [("Normal", "normal"), ("Warning", "warning"), ("Critical", "critical")]
    ):
        col.markdown(
            _card(
                f"{label} components",
                "—",
                f'<span class="mq-badge mq-badge-{key}">{label.upper()}</span>',
            ),
            unsafe_allow_html=True,
        )
    st.caption("Layout and colour preview only. No machine data is shown until Stage 4.")


def _make_renderer(name: str):
    subtitle, stage, show_replay_label = _INFO[name]

    def render() -> None:
        user = auth_service.current_user()

        # Role check inside the page itself, not only in the sidebar.
        if name in NAV_HEAD_ONLY:
            try:
                auth_service.require_role(user, ROLE_HEAD)
            except PermissionError as exc:
                st.error(str(exc))
                return

        page_header(name, subtitle)
        data_source_banner(show_replay_label=show_replay_label)
        st.write("")

        if name == "Overview" and user is not None:
            st.markdown(
                f"Signed in as **{html.escape(user.display_name)}** ({html.escape(user.role_label)})."
            )
            _style_preview()
            st.write("")

        when = f"Stage {stage}" if stage else "a later stage"
        st.markdown(
            f'<div class="mq-placeholder"><strong>Placeholder page.</strong> '
            f"This section is not connected to the backend yet. "
            f"The real {html.escape(name)} page arrives in {when}.</div>",
            unsafe_allow_html=True,
        )

    return render


PAGE_RENDERERS = {name: _make_renderer(name) for name in _INFO}