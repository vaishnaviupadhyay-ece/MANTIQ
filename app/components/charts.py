"""
MANTIQ charts (Plotly). Every chart is drawn from real pipeline data.
All x axes show ORIGINAL dataset times (2003), never the current date.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.config import BEARINGS
from app.theme import palette, plotly_layout

# MIRRORS the anomaly-rate thresholds in src/condition_engine.assess_condition
# (conditions also depend on average score and streaks, see the page notes).
RATE_WARNING = 20.0
RATE_CRITICAL = 75.0

_RANK = {"NORMAL": 0, "WARNING": 1, "CRITICAL": 2}
_HOVER_TIME = "%{x|%d %b %Y %H:%M}"


def show(fig, key: str = None) -> None:
    """Draw a figure so it follows MANTIQ's theme (not Streamlit's own)."""
    config = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}
    try:
        st.plotly_chart(fig, theme=None, width="stretch", config=config, key=key)
    except TypeError:  # older Streamlit without the width argument
        st.plotly_chart(fig, theme=None, use_container_width=True, config=config, key=key)


def _color(i: int) -> str:
    series = palette()["series"]
    return series[i % len(series)]


def _mark_test_start(fig, times: pd.Series, start: int, end: int, test_start_index: int) -> None:
    """Dotted line where the unseen test period begins (only if it is in view)."""
    if not (start < test_start_index <= end):
        return
    p = palette()
    x = pd.Timestamp(times.iloc[test_start_index]).to_pydatetime()
    fig.add_shape(type="line", x0=x, x1=x, xref="x", yref="paper", y0=0, y1=1,
                  line=dict(color=p["brass"], width=1.5, dash="dot"))
    fig.add_annotation(x=x, xref="x", y=1, yref="paper", text="Unseen test period starts",
                       showarrow=False, xanchor="left", yanchor="top",
                       font=dict(size=11, color=p["text_muted"]))


def score_trend_chart(scored: pd.DataFrame, start: int, end: int, test_start_index: int,
                      height: int = 340):
    """Anomaly score of every bearing over recordings start..end (0-based, inclusive)."""
    p = palette()
    sub = scored.iloc[start:end + 1]
    fig = go.Figure()
    for i, bearing in enumerate(BEARINGS):
        fig.add_trace(go.Scatter(
            x=sub["time"], y=sub[f"bearing_{bearing}_score"], mode="lines",
            name=f"Bearing {bearing}", line=dict(width=1.6, color=_color(i)),
            hovertemplate=f"Bearing {bearing}<br>{_HOVER_TIME}<br>Score %{{y:.3f}}<extra></extra>",
        ))
    fig.add_hline(y=0, line_dash="dash", line_width=1, line_color=p["text_muted"],
                  annotation_text="Cutoff: below 0 is flagged", annotation_position="bottom right",
                  annotation_font_color=p["text_muted"])
    _mark_test_start(fig, scored["time"], start, end, test_start_index)
    fig.update_layout(**plotly_layout(), height=height)
    fig.update_layout(xaxis_title_text="Original dataset time",
                      yaxis_title_text="Anomaly score (lower = more unusual)")
    return fig


def anomaly_rate_chart(conditions: pd.DataFrame, start: int, end: int, test_start_index: int,
                       height: int = 320):
    """Share of the latest 50 recordings flagged as anomalous, per bearing."""
    p = palette()
    sub = conditions.iloc[start:end + 1]
    fig = go.Figure()
    for i, bearing in enumerate(BEARINGS):
        fig.add_trace(go.Scatter(
            x=sub["time"], y=sub[f"bearing_{bearing}_rate"] * 100, mode="lines",
            name=f"Bearing {bearing}", line=dict(width=1.6, color=_color(i)),
            hovertemplate=f"Bearing {bearing}<br>{_HOVER_TIME}<br>%{{y:.1f}}% flagged<extra></extra>",
        ))
    fig.add_hline(y=RATE_WARNING, line_dash="dot", line_width=1, line_color=p["warning"],
                  annotation_text=f"{RATE_WARNING:.0f}% (Warning rule)", annotation_position="top left",
                  annotation_font_color=p["warning"])
    fig.add_hline(y=RATE_CRITICAL, line_dash="dot", line_width=1, line_color=p["critical"],
                  annotation_text=f"{RATE_CRITICAL:.0f}% (Critical rule)", annotation_position="top left",
                  annotation_font_color=p["critical"])
    _mark_test_start(fig, conditions["time"], start, end, test_start_index)
    fig.update_layout(**plotly_layout(), height=height)
    fig.update_layout(xaxis_title_text="Original dataset time",
                      yaxis_title_text="Flagged in latest 50 recordings (%)",
                      yaxis_range=[0, 100])
    return fig


def condition_strip_chart(conditions: pd.DataFrame, start: int, end: int, height: int = 250):
    """One coloured row per bearing showing its condition over time."""
    p = palette()
    sub = conditions.iloc[start:end + 1]
    labels = [f"Bearing {b}" for b in reversed(BEARINGS)]   # bottom to top, so Bearing 1 is on top
    z = [sub[f"bearing_{b}_condition"].map(_RANK).tolist() for b in reversed(BEARINGS)]
    text = [sub[f"bearing_{b}_condition"].str.title().tolist() for b in reversed(BEARINGS)]
    normal, warning, critical = p["normal"], p["warning"], p["critical"]
    scale = [[0.0, normal], [1 / 3, normal], [1 / 3, warning], [2 / 3, warning],
             [2 / 3, critical], [1.0, critical]]

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        x=sub["time"], y=labels, z=z, text=text, colorscale=scale, zmin=0, zmax=2,
        showscale=False, hovertemplate=f"%{{y}}<br>{_HOVER_TIME}<br>%{{text}}<extra></extra>",
    ))
    for name, color in (("Normal", normal), ("Warning", warning), ("Critical", critical)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=name,
                                 marker=dict(size=10, color=color, symbol="square")))
    fig.update_layout(**plotly_layout(), height=height)
    fig.update_layout(xaxis_title_text="Original dataset time")
    fig.update_yaxes(categoryorder="array", categoryarray=labels)
    fig.update_xaxes(showgrid=False)
    return fig