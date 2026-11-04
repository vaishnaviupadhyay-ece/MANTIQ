"""
MANTIQ sidebar.

"""

import html

import streamlit as st

from app.components.logo import render_logo
from app.config import DATA_SOURCE_LABEL, pages_for_role
from app.services import auth_service
from app.theme import is_dark, on_theme_toggle


def render_theme_toggle(label: str = "Dark mode") -> None:
    """Light/dark switch. The choice is stored in st.session_state['theme']
    by on_theme_toggle(), so it survives reruns and page navigation."""
    st.toggle(label, value=is_dark(), key="theme_toggle", on_change=on_theme_toggle)


def render_sidebar(pages: dict, user) -> None:
    """pages: {page name: st.Page}. user: auth_service.User."""
    with st.sidebar:
        render_logo("full", height=32, surface="sidebar")

        st.markdown(
            f'<div style="margin:1rem 0 0.5rem 0;">'
            f'<div style="font-weight:600;">{html.escape(user.display_name)}</div>'
            f'<div class="mq-sidebar-muted" style="font-size:0.8rem;">'
            f'{html.escape(user.role_label)}</div></div>',
            unsafe_allow_html=True,
        )
        st.divider()

        for name in pages_for_role(user.role):
            page = pages.get(name)
            if page is not None:
                st.page_link(page, label=name)

        st.divider()
        st.markdown(
            f'<div class="mq-sidebar-muted" style="font-size:0.75rem;line-height:1.45;'
            f'margin-bottom:0.75rem;">{html.escape(DATA_SOURCE_LABEL)}<br>'
            f'Historical replay, not live sensors</div>',
            unsafe_allow_html=True,
        )

        render_theme_toggle()
        if st.button("Sign out", key="sign_out"):
            auth_service.logout()
            st.rerun()