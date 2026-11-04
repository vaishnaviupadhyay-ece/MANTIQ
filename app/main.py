"""
MANTIQ - application entry point.

Run from the project root with:
    python -m streamlit run app\\main.py
"""

import sys
from pathlib import Path

# Make "from app...." imports work no matter where Streamlit is started from.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st  # noqa: E402

from app.components.sidebar import render_sidebar  # noqa: E402
from app.config import APP_NAME, FAVICON_SVG, ROLE_HEAD, pages_for_role  # noqa: E402
from app.pages import login, maintenance_dashboard, operator_dashboard, placeholders  # noqa: E402
from app.services import auth_service  # noqa: E402
from app.theme import init_theme, inject_css  # noqa: E402
from app.pages.alerts import render_alerts
from app.pages import replay, workspaces

# st.set_page_config must be the first Streamlit command in the script.
try:
    st.set_page_config(
        page_title=APP_NAME,
        page_icon=str(FAVICON_SVG) if FAVICON_SVG.exists() else None,
        layout="wide",
        initial_sidebar_state="expanded",
    )
except Exception:
    # If this Streamlit version cannot use the SVG as a favicon, fall back.
    st.set_page_config(
        page_title=APP_NAME,
        page_icon="◎",
        layout="wide",
        initial_sidebar_state="expanded",
    )

init_theme()
inject_css()


def _slug(name: str) -> str:
    return name.lower().replace(" / ", "-").replace(" ", "-")




def _renderer_for(name: str, role: str):
    """Connect every navigation item to its functional page."""

    if name == "Overview":
        return (
            maintenance_dashboard.render
            if role == ROLE_HEAD
            else operator_dashboard.render
        )

    if name == "Replay":
        return replay.render

    if name == "Alerts":
        return lambda: render_alerts(auth_service.current_user())

    page_renderers = {
        "Machines": workspaces.render_machines,
        "Maintenance": workspaces.render_maintenance,
        "History": workspaces.render_history,
        "Team / Assignments": workspaces.render_team_assignments,
        "Analytics": workspaces.render_analytics,
        "Configuration": workspaces.render_configuration,
    }

    if name in page_renderers:
        return page_renderers[name]

    return placeholders.PAGE_RENDERERS.get(name)


def _build_pages(role: str) -> dict:
    """Only the pages this role may see are registered with Streamlit.
    Pages that are not registered cannot be opened, not even by typing the URL."""
    pages = {}
    for name in pages_for_role(role):
        renderer = _renderer_for(name, role)
        if renderer is None:
            continue
        pages[name] = st.Page(
            renderer, title=name, url_path=_slug(name), default=(name == "Overview")
        )
    return pages


user = auth_service.current_user()

if user is None:
    nav = st.navigation(
        [st.Page(login.render, title="Sign in", url_path="login", default=True)],
        position="hidden",
    )
else:
    pages = _build_pages(user.role)
    nav = st.navigation(list(pages.values()), position="hidden")
    render_sidebar(pages, user)

nav.run()