"""Interactive event timeline (Plotly).

Plots every dated memory on a horizontal timeline; the figure is shown
live in Streamlit and exported as a standalone HTML file users can share.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import plotly.graph_objects as go

from ..core.models import MediaItem
from ..core.themes import Theme


def build_timeline(photos: list[MediaItem], theme: Theme, title: str,
                   output_path: Optional[Path] = None) -> Optional[go.Figure]:
    """Return a Plotly figure of dated memories (None when nothing is dated)."""
    dated = sorted((p for p in photos if p.taken_at), key=lambda p: p.taken_at)
    if not dated:
        return None

    xs = [datetime.fromisoformat(p.taken_at) for p in dated]
    labels = [p.caption or Path(p.path).stem.replace("-", " ").title() for p in dated]
    # alternate above/below the axis so labels never collide
    ys = [1 if i % 2 == 0 else -1 for i in range(len(dated))]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=[0] * len(xs), mode="lines",
        line=dict(color=theme.hex(theme.accent), width=2),
        hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=xs, y=ys, mode="markers+text",
        text=[l[:28] for l in labels],
        textposition=["top center" if y > 0 else "bottom center" for y in ys],
        marker=dict(size=14, color=theme.hex(theme.primary),
                    line=dict(color=theme.hex(theme.accent), width=2)),
        hovertext=[f"{x:%d %b %Y}<br>{l}" for x, l in zip(xs, labels)],
        hoverinfo="text", showlegend=False))
    # stems from axis to markers
    for x, y in zip(xs, ys):
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=y,
                      line=dict(color=theme.hex(theme.accent), width=1, dash="dot"))

    fig.update_layout(
        title=dict(text=title or "Timeline of Memories",
                   font=dict(size=22, color=theme.hex(theme.primary))),
        paper_bgcolor=theme.hex(theme.background),
        plot_bgcolor=theme.hex(theme.background),
        font=dict(color=theme.hex(theme.text)),
        yaxis=dict(visible=False, range=[-2, 2]),
        xaxis=dict(showgrid=False, tickfont=dict(size=12)),
        height=420, margin=dict(l=40, r=40, t=70, b=40))

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.write_html(str(output_path), include_plotlyjs="cdn")
    return fig
