"""MANTIQ login screen."""

import html

import streamlit as st

from app.components.logo import logo_html
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
from app.theme import current_theme

_HIDE_SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="collapsedControl"] {
    display: none;
}

.mq-login-brand {
    text-align: center;
    padding: 2.4rem 1.5rem 2rem;
    margin: 0.5rem 0 1.8rem;
    border: 1px solid var(--mq-border, rgba(128,128,128,0.2));
    border-radius: 18px;
    background: var(--mq-card, rgba(128,128,128,0.04));
}

.mq-login-logo {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 1.4rem;
}

.mq-login-logo img {
    height: 76px !important;
    width: auto !important;
    max-width: 100%;
}

.mq-login-tagline {
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    line-height: 1.7;
    text-transform: uppercase;
}

.mq-login-description {
    margin-top: 0.65rem;
    font-size: 0.82rem;
    line-height: 1.6;
    opacity: 0.65;
    letter-spacing: 0.015em;
}

.mq-login-notice {
    text-align: center;
    font-size: 0.72rem;
    opacity: 0.58;
    margin-top: 1.3rem;
}
</style>
"""

def render() -> None:
    st.markdown(_HIDE_SIDEBAR_CSS, unsafe_allow_html=True)

    _, centre, _ = st.columns([1, 1.4, 1])

    with centre:
        st.write("")

        # Existing logo and tagline are retained.
        brand_logo = logo_html("full", height=76, surface="page")

        st.markdown(
            f"""
            <div class="mq-login-brand">
                <div class="mq-login-logo">{brand_logo}</div>
                <div class="mq-login-tagline">{html.escape(TAGLINE)}</div>
                <div class="mq-login-description">
                    Industrial maintenance intelligence. Sign in to continue.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        role_names = [
            ROLE_LABELS[ROLE_OPERATOR],
            ROLE_LABELS[ROLE_HEAD],
        ]
        role_by_label = {
            label: role for role, label in ROLE_LABELS.items()
        }

        with st.form("login_form"):
            chosen_label = st.radio(
                "Sign in as",
                role_names,
                horizontal=True,
            )
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Sign in",
                type="primary",
                use_container_width=True,
            )

        if submitted:
            user = auth_service.authenticate(username, password)

            if user is None:
                st.error("Incorrect username or password.")
            elif user.role != role_by_label[chosen_label]:
                st.error(
                    f"This account is not a {chosen_label} account. "
                    "Select the matching role and try again."
                )
            else:
                auth_service.login(user)
                st.rerun()

        with st.expander("Demo credentials"):
            for name, info in DEMO_USERS.items():
                st.markdown(
                    f"**{ROLE_LABELS[info['role']]}**: "
                    f"username `{name}`, "
                    f"password `{info['password']}`"
                )
            st.caption(DEMO_AUTH_NOTICE)

        st.markdown(
            f"""
            <div class="mq-login-notice">
                Prototype · {html.escape(DATA_SOURCE_LABEL)}
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_theme_toggle()