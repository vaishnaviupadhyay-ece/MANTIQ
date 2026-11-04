"""
MANTIQ theme system.

"""

import streamlit as st

from app.config import DEFAULT_THEME

# ----------------------------------------------------------------------------
# Palettes
# ----------------------------------------------------------------------------
PALETTES = {
    "light": {
        # approved palette
        "bg": "#F2F2ED",
        "surface": "#FFFFFF",
        "primary": "#173B3A",
        "sage": "#718C83",
        "brass": "#C4A875",
        "text": "#303B43",
        # derived shades
        "surface_alt": "#F7F7F3",
        "text_muted": "#66737A",
        "border": "#E2E2DA",
        "on_primary": "#FFFFFF",
        "shadow": "0 1px 2px rgba(23, 59, 58, 0.06)",
        "sidebar_bg": "#173B3A",
        "sidebar_text": "#E8EFEA",
        "sidebar_muted": "#9DB5AD",
        "sidebar_active_bg": "rgba(255, 255, 255, 0.10)",
        # status colours (muted)
        "normal": "#3F8F74",
        "warning": "#C28A2C",
        "critical": "#BF5B4F",
        "offline": "#77838C",
        # chart series colours (derived)
        "series": ["#173B3A", "#C4A875", "#718C83", "#5F7D95"],
    },
    "dark": {
        # approved palette
        "bg": "#141C20",
        "surface": "#202B30",
        "primary": "#244B45",
        "sage": "#83B6A1",
        "brass": "#C4A875",
        "text": "#E5EEE8",
        "text_muted": "#A3B2AC",
        # derived shades
        "surface_alt": "#1A2428",
        "border": "#2F3D43",
        "on_primary": "#E5EEE8",
        "shadow": "0 1px 2px rgba(0, 0, 0, 0.35)",
        "sidebar_bg": "#1A2428",
        "sidebar_text": "#E5EEE8",
        "sidebar_muted": "#A3B2AC",
        "sidebar_active_bg": "rgba(131, 182, 161, 0.16)",
        # status colours (muted)
        "normal": "#5FB596",
        "warning": "#D8A347",
        "critical": "#E27C6E",
        "offline": "#8B98A1",
        # chart series colours (derived)
        "series": ["#83B6A1", "#C4A875", "#7C9BB3", "#B7C3BD"],
    },
}

FONT_STACK = '"Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif'

# Maps the condition names used by src/condition_engine.py to palette keys.
STATUS_KEYS = {
    "NORMAL": "normal",
    "WARNING": "warning",
    "CRITICAL": "critical",
    "OFFLINE": "offline",
}


# ----------------------------------------------------------------------------
# Theme state (kept in st.session_state so it survives reruns and navigation)
# ----------------------------------------------------------------------------
def init_theme() -> None:
    """Call once per run, before anything else. Sets the default theme."""
    if "theme" not in st.session_state:
        st.session_state["theme"] = DEFAULT_THEME


def current_theme() -> str:
    return st.session_state.get("theme", DEFAULT_THEME)


def is_dark() -> bool:
    return current_theme() == "dark"


def palette() -> dict:
    return PALETTES[current_theme()]


def on_theme_toggle() -> None:
    """Callback for the sidebar toggle widget (key: 'theme_toggle')."""
    st.session_state["theme"] = "dark" if st.session_state.get("theme_toggle") else "light"


def status_color(condition: str) -> str:
    """Hex colour for NORMAL / WARNING / CRITICAL / OFFLINE in the current theme."""
    key = STATUS_KEYS.get(str(condition).upper(), "offline")
    return palette()[key]


# ----------------------------------------------------------------------------
# CSS
# ----------------------------------------------------------------------------
_BASE_CSS = """
html, body, .stApp {
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
}
[data-testid="stHeader"] { background: transparent; }
footer { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1280px; }

h1, h2, h3, h4 { color: var(--text); font-weight: 600; letter-spacing: -0.01em; }
[data-testid="stMarkdownContainer"] { color: var(--text); }
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {
    color: var(--text-muted); font-size: 0.85rem;
}
hr { border-color: var(--border); }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: var(--sidebar-text); }
[data-testid="stSidebar"] .mq-sidebar-muted { color: var(--sidebar-muted); }
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"] {
    border-radius: 6px; padding: 0.45rem 0.75rem;
}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]:hover {
    background: var(--sidebar-active-bg);
}
[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"][aria-current="page"] {
    background: var(--sidebar-active-bg);
    box-shadow: inset 3px 0 0 var(--brass);
    font-weight: 600;
}
[data-testid="stSidebar"] button {
    background: transparent;
    border: 1px solid var(--sidebar-muted);
    border-radius: 6px;
}

/* ---------- Inputs ---------- */
[data-baseweb="base-input"] { background: transparent !important; }

[data-baseweb="input"], [data-baseweb="textarea"], [data-baseweb="select"] > div {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    border-radius: 6px !important;
}
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    background: transparent !important;
    color: var(--text) !important;
    -webkit-text-fill-color: var(--text) !important;
}
[data-baseweb="select"] * { color: var(--text); }
[data-baseweb="popover"] [role="listbox"], [data-baseweb="popover"] ul {
    background: var(--surface) !important;
}
[data-baseweb="popover"] li { color: var(--text) !important; }

/* ---------- Buttons (main area) ---------- */
.stButton > button, [data-testid="stFormSubmitButton"] > button {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-weight: 500;
}
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
    border-color: var(--sage); color: var(--text);
}
.stButton > button[kind="primary"], [data-testid="stBaseButton-primary"],
[data-testid="stFormSubmitButton"] > button[kind="primaryFormSubmit"] {
    background: var(--primary); color: var(--on-primary); border-color: var(--primary);
}
.stButton > button[kind="primary"] p,
button[kind="primary"] p,
button[kind="primaryFormSubmit"] p,
[data-testid="stBaseButton-primary"] p,
[data-testid="stBaseButton-primaryFormSubmit"] p { color: var(--on-primary) !important; }
[data-testid="stSidebar"] .stButton > button { color: var(--sidebar-text); }

/* ---------- Forms, expanders, tabs ---------- */
[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: var(--shadow);
}
[data-testid="stExpander"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
}
button[data-baseweb="tab"] { color: var(--text-muted); }
button[data-baseweb="tab"][aria-selected="true"] { color: var(--text); }

/* ---------- MANTIQ components (used by app/components/*) ---------- */
.mq-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1.1rem 1.25rem;
    box-shadow: var(--shadow);
}
.mq-card-title {
    font-size: 0.75rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 0.4rem;
}
.mq-metric-value { font-size: 1.9rem; font-weight: 600; line-height: 1.1; color: var(--text); }
.mq-metric-sub { font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem; }

.mq-page-title { font-size: 1.6rem; font-weight: 600; color: var(--text); margin: 0; }
.mq-page-subtitle { font-size: 0.9rem; color: var(--text-muted); margin: 0.2rem 0 1rem 0; }

.mq-badge {
    display: inline-block; padding: 0.12rem 0.6rem; border-radius: 999px;
    font-size: 0.74rem; font-weight: 600; letter-spacing: 0.03em;
}
.mq-badge-normal   { color: var(--normal);   background: color-mix(in srgb, var(--normal) 14%, transparent); }
.mq-badge-warning  { color: var(--warning);  background: color-mix(in srgb, var(--warning) 16%, transparent); }
.mq-badge-critical { color: var(--critical); background: color-mix(in srgb, var(--critical) 14%, transparent); }
.mq-badge-offline  { color: var(--offline);  background: color-mix(in srgb, var(--offline) 16%, transparent); }

.mq-banner {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--brass);
    border-radius: 6px;
    padding: 0.6rem 0.9rem;
    font-size: 0.85rem;
    color: var(--text-muted);
}
.mq-banner strong { color: var(--text); }
.mq-placeholder {
    border: 1px dashed var(--sage); border-radius: 8px; padding: 1.25rem;
    color: var(--text-muted); background: var(--surface-alt);
}
.mq-login-tagline { color: var(--text-muted); font-size: 1rem; margin-top: 0.25rem; }
.mq-login-notice { color: var(--text-muted); font-size: 0.78rem; margin-top: 0.75rem; }

/* ---------- Dashboard parts ---------- */
.mq-card.mq-status-normal   { border-left: 3px solid var(--normal); }
.mq-card.mq-status-warning  { border-left: 3px solid var(--warning); }
.mq-card.mq-status-critical { border-left: 3px solid var(--critical); }
.mq-card.mq-status-offline  { border-left: 3px solid var(--offline); }
.mq-section-title {
    font-size: 1.05rem; font-weight: 600; color: var(--text); margin: 1.6rem 0 0.6rem 0;
}
.mq-note { font-size: 0.82rem; color: var(--text-muted); margin: 0.4rem 0 0 0; }
.mq-bearing-head {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;
}
.mq-bearing-name { font-weight: 600; font-size: 1rem; color: var(--text); }
.mq-kv {
    display: flex; justify-content: space-between; gap: 0.75rem;
    font-size: 0.84rem; padding: 0.15rem 0; color: var(--text-muted);
}
.mq-kv span:last-child { color: var(--text); font-weight: 500; text-align: right; }
.mq-action {
    font-size: 0.82rem; color: var(--text-muted); margin-top: 0.7rem;
    padding-top: 0.6rem; border-top: 1px solid var(--border);
}
.mq-empty {
    border: 1px dashed var(--border); border-radius: 8px; padding: 1rem 1.25rem;
    color: var(--text-muted); background: var(--surface-alt); font-size: 0.88rem;
}
.mq-table-wrap { overflow-x: auto; }
.mq-table {
    width: 100%; border-collapse: collapse; font-size: 0.86rem;
    background: var(--surface); border: 1px solid var(--border);
}
.mq-table th {
    text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--text-muted); font-weight: 600; padding: 0.55rem 0.8rem;
    border-bottom: 1px solid var(--border); white-space: nowrap;
}
.mq-table td {
    padding: 0.55rem 0.8rem; border-bottom: 1px solid var(--border);
    color: var(--text); vertical-align: top;
}
.mq-table tr:last-child td { border-bottom: none; }

/* ---------- Small screens ---------- */
@media (max-width: 768px) {
    .block-container { padding: 1rem 0.75rem 3rem 0.75rem; }
    .mq-metric-value { font-size: 1.5rem; }
    .mq-page-title { font-size: 1.3rem; }
}
"""


def inject_css() -> None:
    """Write the theme CSS into the page. Call once per run, near the top."""
    p = palette()
    variables = {k.replace("_", "-"): v for k, v in p.items() if isinstance(v, str)}
    variables["font"] = FONT_STACK
    root = ":root{" + "".join(f"--{name}:{value};" for name, value in variables.items()) + "}"
    st.markdown(f"<style>{root}{_BASE_CSS}</style>", unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Plotly
# ----------------------------------------------------------------------------
def plotly_layout(with_title: bool = False) -> dict:
    """Layout settings that make a Plotly figure follow the current theme.
    Use it like:  fig.update_layout(**plotly_layout())"""
    p = palette()
    axis = dict(gridcolor=p["border"], linecolor=p["border"], zerolinecolor=p["border"])
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT_STACK, color=p["text"], size=13),
        colorway=p["series"],
        margin=dict(l=48, r=16, t=48 if with_title else 16, b=40),
        xaxis=axis,
        yaxis=axis,
        legend=dict(orientation="h", y=1.1, x=0, bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(bgcolor=p["surface"], font_color=p["text"], bordercolor=p["border"]),
    )