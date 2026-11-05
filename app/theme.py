"""
MANTIQ theme system.
Centralised light/dark styling for the application.
"""

import streamlit as st

from app.config import DEFAULT_THEME


# ----------------------------------------------------------------------------
# PALETTES
# ----------------------------------------------------------------------------

PALETTES = {
    "light": {
        "bg": "#F2F2ED",
        "surface": "#FFFFFF",
        "surface_alt": "#F7F7F3",
        "primary": "#173B3A",
        "sage": "#718C83",
        "brass": "#C4A875",
        "text": "#303B43",
        "text_muted": "#66737A",
        "border": "#E2E2DA",
        "on_primary": "#FFFFFF",
        "shadow": "0 2px 8px rgba(23, 59, 58, 0.05)",
        "sidebar_bg": "#173B3A",
        "sidebar_text": "#E8EFEA",
        "sidebar_muted": "#9DB5AD",
        "sidebar_active_bg": "rgba(255, 255, 255, 0.10)",
        "normal": "#3F8F74",
        "warning": "#C28A2C",
        "critical": "#BF5B4F",
        "offline": "#77838C",
        "series": ["#173B3A", "#C4A875", "#718C83", "#5F7D95"],
    },

    "dark": {
        "bg": "#141C20",
        "surface": "#202B30",
        "surface_alt": "#1A2428",
        "primary": "#244B45",
        "sage": "#83B6A1",
        "brass": "#C4A875",
        "text": "#E5EEE8",
        "text_muted": "#A3B2AC",
        "border": "#2F3D43",
        "on_primary": "#E5EEE8",
        "shadow": "0 2px 10px rgba(0, 0, 0, 0.20)",
        "sidebar_bg": "#1A2428",
        "sidebar_text": "#E5EEE8",
        "sidebar_muted": "#A3B2AC",
        "sidebar_active_bg": "rgba(131, 182, 161, 0.16)",
        "normal": "#5FB596",
        "warning": "#D8A347",
        "critical": "#E27C6E",
        "offline": "#8B98A1",
        "series": ["#83B6A1", "#C4A875", "#7C9BB3", "#B7C3BD"],
    },
}


FONT_STACK = (
    '"Segoe UI", system-ui, -apple-system, '
    '"Helvetica Neue", Arial, sans-serif'
)

STATUS_KEYS = {
    "NORMAL": "normal",
    "WARNING": "warning",
    "CRITICAL": "critical",
    "OFFLINE": "offline",
}


# ----------------------------------------------------------------------------
# THEME STATE
# ----------------------------------------------------------------------------

def init_theme() -> None:
    if "theme" not in st.session_state:
        st.session_state["theme"] = DEFAULT_THEME


def current_theme() -> str:
    theme = st.session_state.get("theme", DEFAULT_THEME)
    return theme if theme in PALETTES else "light"


def is_dark() -> bool:
    return current_theme() == "dark"


def palette() -> dict:
    return PALETTES[current_theme()]


def on_theme_toggle() -> None:
    st.session_state["theme"] = (
        "dark"
        if st.session_state.get("theme_toggle")
        else "light"
    )


def status_color(condition: str) -> str:
    key = STATUS_KEYS.get(str(condition).upper(), "offline")
    return palette()[key]


# ----------------------------------------------------------------------------
# GLOBAL CSS
# ----------------------------------------------------------------------------

_BASE_CSS = """

/* =========================================================
   GLOBAL
   ========================================================= */

html, body, .stApp {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg);
}

[data-testid="stHeader"] {
    background: transparent;
}

footer {
    visibility: hidden;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}

h1, h2, h3, h4 {
    color: var(--text);
    font-weight: 600;
    letter-spacing: -0.015em;
}

p, label, li {
    color: inherit;
}

[data-testid="stMarkdownContainer"] {
    color: var(--text);
}

[data-testid="stWidgetLabel"],
[data-testid="stWidgetLabel"] p {
    color: var(--text-muted);
    font-size: 0.85rem;
}

hr {
    border-color: var(--border);
}


/* =========================================================
   SIDEBAR
   ========================================================= */

[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] {
    color: var(--sidebar-text);
}

[data-testid="stSidebar"] .mq-sidebar-muted {
    color: var(--sidebar-muted);
}

[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
    border-radius: 8px;
    padding: 0.45rem 0.75rem;
    transition: background 160ms ease, color 160ms ease;
}

[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
    background: var(--sidebar-active-bg);
}

[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
    background: var(--sidebar-active-bg);
    box-shadow: inset 3px 0 0 var(--brass);
    font-weight: 600;
}

[data-testid="stSidebar"] .stButton > button {
    background: transparent;
    color: var(--sidebar-text);
    border: 1px solid var(--sidebar-muted);
    border-radius: 8px;
}


/* =========================================================
   INPUTS
   ========================================================= */

[data-baseweb="base-input"] {
    background: transparent !important;
}

[data-baseweb="input"],
[data-baseweb="textarea"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    transition: border-color 150ms ease, box-shadow 150ms ease;
}

[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--text);
}

[data-baseweb="input"] input::placeholder,
[data-baseweb="textarea"] textarea::placeholder {
    color: var(--text-muted) !important;
    -webkit-text-fill-color: var(--text-muted) !important;
}

[data-baseweb="input"]:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 2px color-mix(
        in srgb, var(--sage) 18%, transparent
    );
}


/* =========================================================
   SELECT BOXES
   Target the actual control, not every nested div.
   ========================================================= */

[data-baseweb="select"] [role="combobox"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    transition: border-color 150ms ease, box-shadow 150ms ease;
}

[data-baseweb="select"] [role="combobox"]:focus,
[data-baseweb="select"] [role="combobox"]:focus-within {
    border-color: var(--sage) !important;
    box-shadow: 0 0 0 2px color-mix(
        in srgb, var(--sage) 18%, transparent
    );
}

[data-baseweb="select"] input {
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
    caret-color: var(--text);
}

/* Selected value */
[data-baseweb="select"] [role="combobox"] > div {
    color: var(--text);
}

/* Dropdown arrow and control icons */
[data-baseweb="select"] svg {
    fill: var(--text-muted);
    color: var(--text-muted);
}

/* Multi-select tags */
[data-baseweb="tag"] {
    background: var(--surface-alt) !important;
    border: 1px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 6px !important;
}

[data-baseweb="tag"] span {
    color: var(--text) !important;
}


/* =========================================================
   DROPDOWN MENUS AND POPOVERS
   ========================================================= */

[data-baseweb="popover"] {
    z-index: 9999 !important;
}

/* Menu surface */
[data-baseweb="popover"] [data-baseweb="menu"],
[data-baseweb="popover"] [role="listbox"] {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border);
    border-radius: 9px;
    padding: 4px;
    box-shadow: var(--shadow);
}

/* Individual options */
[data-baseweb="popover"] [role="option"] {
    background: transparent !important;
    color: var(--text) !important;
    border-radius: 6px;
    transition: background 120ms ease;
}

/* Hover and keyboard-highlighted option */
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][data-highlighted="true"] {
    background: var(--surface-alt) !important;
    color: var(--text) !important;
}

/* Selected option */
[data-baseweb="popover"] [role="option"][aria-selected="true"] {
    background: var(--surface-alt) !important;
    color: var(--text) !important;
    font-weight: 600;
}

/* Calendar and date picker surfaces */
[data-baseweb="popover"] [data-baseweb="calendar"] {
    background: var(--surface) !important;
    color: var(--text) !important;
}

[data-baseweb="popover"] [data-baseweb="calendar"] * {
    color: var(--text);
}


/* =========================================================
   BUTTONS
   ========================================================= */

.stButton > button,
[data-testid="stFormSubmitButton"] > button {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-weight: 550;
    transition:
        background 150ms ease,
        border-color 150ms ease,
        color 150ms ease,
        box-shadow 150ms ease,
        transform 150ms ease;
}

.stButton > button:hover,
[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--surface-alt);
    border-color: var(--sage);
    color: var(--text);
    box-shadow: 0 2px 7px rgba(0, 0, 0, 0.06);
    transform: translateY(-1px);
}

.stButton > button:active,
[data-testid="stFormSubmitButton"] > button:active {
    transform: translateY(0);
}

/* Primary buttons */
.stButton > button[kind="primary"],
[data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: var(--primary);
    color: var(--on_primary);
    border-color: var(--primary);
}

.stButton > button[kind="primary"]:hover,
[data-testid="stBaseButton-primary"]:hover,
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"]:hover {
    background: var(--primary);
    border-color: var(--sage);
    color: var(--on_primary);
}

button[kind="primary"] p,
button[kind="primaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p {
    color: var(--on_primary) !important;
}

/* Sign out */
[data-testid="stSidebar"] .st-key-sign_out button {
    width: 100%;
    background: transparent;
    color: var(--sidebar-text);
    border: 1px solid var(--sidebar-muted);
    border-radius: 8px;
    font-weight: 500;
}

[data-testid="stSidebar"] .st-key-sign_out button:hover {
    background: var(--sidebar-active-bg);
    color: var(--sidebar-text);
    border-color: var(--brass);
    box-shadow: none;
}


/* =========================================================
   FORMS, EXPANDERS AND TABS
   ========================================================= */

[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.25rem;
    box-shadow: var(--shadow);
}

[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: visible;
}

[data-testid="stExpander"] summary {
    color: var(--text);
}

[data-testid="stExpander"] summary:hover {
    color: var(--sage);
}

button[data-baseweb="tab"] {
    color: var(--text-muted);
    transition: color 150ms ease;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--text);
}


/* =========================================================
   MANTIQ CARDS
   ========================================================= */

.mq-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow);
    transition:
        border-color 170ms ease,
        box-shadow 170ms ease,
        transform 170ms ease;
}

.mq-card:hover {
    border-color: color-mix(
        in srgb, var(--sage) 45%, var(--border)
    );
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
    transform: translateY(-2px);
}

.mq-card-title {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    margin-bottom: 0.4rem;
}

.mq-metric-value {
    font-size: 1.9rem;
    font-weight: 600;
    line-height: 1.1;
    color: var(--text);
}

.mq-metric-sub {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
}

.mq-page-title {
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--text);
    margin: 0;
}

.mq-page-subtitle {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin: 0.2rem 0 1rem 0;
}

.mq-badge {
    display: inline-block;
    padding: 0.12rem 0.6rem;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

.mq-badge-normal {
    color: var(--normal);
    background: color-mix(in srgb, var(--normal) 14%, transparent);
}

.mq-badge-warning {
    color: var(--warning);
    background: color-mix(in srgb, var(--warning) 16%, transparent);
}

.mq-badge-critical {
    color: var(--critical);
    background: color-mix(in srgb, var(--critical) 14%, transparent);
}

.mq-badge-offline {
    color: var(--offline);
    background: color-mix(in srgb, var(--offline) 16%, transparent);
}


/* =========================================================
   BANNERS AND NOTES
   ========================================================= */

.mq-banner {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--brass);
    border-radius: 9px;
    padding: 0.6rem 0.9rem;
    font-size: 0.85rem;
    color: var(--text-muted);
}

.mq-banner strong {
    color: var(--text);
}

.mq-placeholder {
    border: 1px dashed var(--sage);
    border-radius: 9px;
    padding: 1.25rem;
    color: var(--text-muted);
    background: var(--surface-alt);
}

.mq-login-tagline {
    color: var(--text-muted);
    font-size: 1rem;
    margin-top: 0.25rem;
}

.mq-login-notice {
    color: var(--text-muted);
    font-size: 0.78rem;
    margin-top: 0.75rem;
}


/* =========================================================
   DASHBOARD COMPONENTS
   ========================================================= */

.mq-card.mq-status-normal {
    border-left: 3px solid var(--normal);
}

.mq-card.mq-status-warning {
    border-left: 3px solid var(--warning);
}

.mq-card.mq-status-critical {
    border-left: 3px solid var(--critical);
}

.mq-card.mq-status-offline {
    border-left: 3px solid var(--offline);
}

.mq-section-title {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text);
    margin: 1.6rem 0 0.6rem 0;
}

.mq-note {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin: 0.4rem 0 0 0;
}

.mq-bearing-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.6rem;
}

.mq-bearing-name {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text);
}

.mq-kv {
    display: flex;
    justify-content: space-between;
    gap: 0.75rem;
    font-size: 0.84rem;
    padding: 0.15rem 0;
    color: var(--text-muted);
}

.mq-kv span:last-child {
    color: var(--text);
    font-weight: 500;
    text-align: right;
}

.mq-action {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-top: 0.7rem;
    padding-top: 0.6rem;
    border-top: 1px solid var(--border);
}

.mq-empty {
    border: 1px dashed var(--border);
    border-radius: 9px;
    padding: 1rem 1.25rem;
    color: var(--text-muted);
    background: var(--surface-alt);
    font-size: 0.88rem;
}

.mq-table-wrap {
    overflow-x: auto;
}

.mq-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.86rem;
    background: var(--surface);
    border: 1px solid var(--border);
}

.mq-table th {
    text-align: left;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    font-weight: 600;
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}

.mq-table td {
    padding: 0.55rem 0.8rem;
    border-bottom: 1px solid var(--border);
    color: var(--text);
    vertical-align: top;
}

.mq-table tr:last-child td {
    border-bottom: none;
}


/* =========================================================
   PLOTLY CONTAINERS
   ========================================================= */

[data-testid="stPlotlyChart"] {
    background: transparent;
    border-radius: 10px;
    overflow: hidden;
}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media (max-width: 768px) {
    .block-container {
        padding: 1rem 0.75rem 3rem 0.75rem;
    }

    .mq-metric-value {
        font-size: 1.5rem;
    }

    .mq-page-title {
        font-size: 1.3rem;
    }

    .mq-card:hover {
        transform: none;
    }
}


/* =========================================================
   REDUCED MOTION
   ========================================================= */

@media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
"""


# ----------------------------------------------------------------------------
# CSS INJECTION
# ----------------------------------------------------------------------------

def inject_css() -> None:
    """Inject theme variables and application styling."""

    p = palette()

    variables = {
        key.replace("_", "-"): value
        for key, value in p.items()
        if isinstance(value, str)
    }

    variables["font"] = FONT_STACK
    variables["color-scheme"] = current_theme()

    root = ":root{" + "".join(
        f"--{name}:{value};"
        for name, value in variables.items()
    ) + "color-scheme:var(--color-scheme);}"

    st.markdown(
        f"<style>{root}{_BASE_CSS}</style>",
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------------
# PLOTLY
# ----------------------------------------------------------------------------

def plotly_layout(with_title: bool = False) -> dict:
    """Return Plotly layout settings matching the active theme."""

    p = palette()

    axis = {
        "gridcolor": p["border"],
        "linecolor": p["border"],
        "zerolinecolor": p["border"],
        "tickfont": {
            "color": p["text_muted"],
            "size": 11,
        },
        "title": {
            "font": {
                "color": p["text_muted"],
                "size": 12,
            }
        },
        "showline": False,
        "zerolinewidth": 1,
    }

    return {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": FONT_STACK,
            "color": p["text"],
            "size": 13,
        },
        "colorway": p["series"],
        "margin": {
            "l": 48,
            "r": 16,
            "t": 48 if with_title else 16,
            "b": 40,
        },
        "xaxis": axis.copy(),
        "yaxis": axis.copy(),
        "legend": {
            "orientation": "h",
            "y": 1.1,
            "x": 0,
            "bgcolor": "rgba(0,0,0,0)",
            "font": {
                "color": p["text_muted"],
                "size": 11,
            },
        },
        "hovermode": "closest",
        "hoverlabel": {
            "bgcolor": p["surface"],
            "font": {
                "color": p["text"],
                "family": FONT_STACK,
                "size": 12,
            },
            "bordercolor": p["border"],
        },
    }