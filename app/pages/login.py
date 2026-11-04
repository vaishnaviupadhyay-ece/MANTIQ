"""
MANTIQ login screen.
"""

import streamlit as st

from app.components.logo import render_logo
from app.components.sidebar import render_theme_toggle
from app.config import (
    DATA_SOURCE_LABEL,
    DEMO_AUTH_NOTICE,
    DEMO_USERS,
    ROLE_HEAD,
    ROLE_LABELS,
    ROLE_OPERATOR,
    TAGLINE,
)
from app.services import auth_service

# Nobody is signed in on this screen, so hide the sidebar completely.
_HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] { display: none; }
</style>
"""


def render() -> None:
    st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    _, centre, _ = st.columns([1, 1.4, 1])
    with centre:
        st.write("")
        render_logo("full", height=60, surface="page")
        st.markdown(f'<div class="mq-login-tagline">{TAGLINE}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="mq-page-subtitle" style="margin-top:0.75rem;">'
            "Industrial maintenance intelligence. Sign in to continue.</div>",
            unsafe_allow_html=True,
        )

        role_names = [ROLE_LABELS[ROLE_OPERATOR], ROLE_LABELS[ROLE_HEAD]]
        role_by_label = {label: role for role, label in ROLE_LABELS.items()}

        with st.form("login_form"):
            chosen_label = st.radio("Sign in as", role_names, horizontal=True)
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary")

        if submitted:
            user = auth_service.authenticate(username, password)
            if user is None:
                st.error("Incorrect username or password.")
            elif user.role != role_by_label[chosen_label]:
                st.error(f"This account is not a {chosen_label} account. "
                         "Select the matching role and try again.")
            else:
                auth_service.login(user)
                st.rerun()

        with st.expander("Demo credentials"):
            for name, info in DEMO_USERS.items():
                st.markdown(
                    f"**{ROLE_LABELS[info['role']]}**: username `{name}`, "
                    f"password `{info['password']}`"
                )
            st.caption(DEMO_AUTH_NOTICE)

        st.markdown(
            f'<div class="mq-login-notice">Prototype · {DATA_SOURCE_LABEL}</div>',
            unsafe_allow_html=True,
        )
        render_theme_toggle()