"""
MANTIQ logo component.

"""

import base64
import html
import re

import streamlit as st

from app.config import APP_NAME, LOGO_SVG
from app.theme import current_theme

# Colours substituted into the var(--mq-...) placeholders inside logo.svg
_INK = {"mark": "#173B3A", "word": "#173B3A", "accent": "#C4A875"}     # for light backgrounds
_LIGHT = {"mark": "#83B6A1", "word": "#E5EEE8", "accent": "#C4A875"}   # for dark backgrounds


def _read_svg() -> str:
    try:
        return LOGO_SVG.read_text(encoding="utf-8")
    except OSError:
        return ""


def _recolor(svg: str, colors: dict) -> str:
    """Replace var(--mq-name,#fallback) with the chosen colour for 'name'."""
    return re.sub(
        r"var\(--mq-(\w+),\s*(#[0-9A-Fa-f]{6})\)",
        lambda m: colors.get(m.group(1), m.group(2)),
        svg,
    )


def _to_icon(svg: str) -> str:
    """Remove the wordmark and crop to the 64x64 symbol area."""
    svg = re.sub(r"<text.*?</text>", "", svg, flags=re.DOTALL)
    svg = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 64 64"', svg, count=1)
    # This literal string matches the root tag of logo.svg. If you edit the
    # logo's size, update it here as well.
    svg = svg.replace('width="250" height="64"', 'width="64" height="64"', 1)
    return svg


def logo_html(variant: str = "full", height: int = 40,
              surface: str = "page", dark=None) -> str:
    """Return the logo as an HTML <img> string.

    dark=None  -> use the current app theme (normal use)
    dark=True/False -> force a theme (handy for testing outside Streamlit)
    """
    svg = _read_svg()
    if not svg:
        # Missing file: show a plain text wordmark instead of crashing.
        return (f'<span style="font-weight:600;letter-spacing:0.2em;">'
                f'{html.escape(APP_NAME)}</span>')

    if dark is None:
        dark = current_theme() == "dark"
    colors = _LIGHT if (dark or surface == "sidebar") else _INK
    svg = _recolor(svg, colors)
    if variant == "icon":
        svg = _to_icon(svg)

    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return (f'<img alt="{html.escape(APP_NAME)}" '
            f'src="data:image/svg+xml;base64,{encoded}" '
            f'style="height:{int(height)}px;width:auto;display:block;" />')


def render_logo(variant: str = "full", height: int = 40, surface: str = "page") -> None:
    st.markdown(logo_html(variant, height, surface), unsafe_allow_html=True)