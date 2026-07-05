"""Title-card renderer.

Opening scenes, closing scenes and caption overlays are drawn with
Pillow rather than MoviePy's TextClip, so typography is fully theme
driven and there is no ImageMagick dependency.
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from ..core.themes import Theme
from ..utils.fonts import load_font


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Greedy word wrap measured in pixels."""
    lines: list[str] = []
    for paragraph in text.split("\n"):
        words, current = paragraph.split(), ""
        for word in words:
            trial = f"{current} {word}".strip()
            if draw.textlength(trial, font=font) <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    return [l for l in lines if l] or [""]


def _draw_frame(draw: ImageDraw.ImageDraw, size: tuple[int, int], theme: Theme) -> None:
    """Decorative border according to the theme's frame style."""
    w, h = size
    m = round(min(w, h) * 0.05)
    color = theme.primary
    if theme.frame_style == "line":
        draw.rectangle([m, m, w - m, h - m], outline=color, width=3)
    elif theme.frame_style == "double":
        draw.rectangle([m, m, w - m, h - m], outline=color, width=2)
        g = round(m * 0.35)
        draw.rectangle([m + g, m + g, w - m - g, h - m - g], outline=theme.accent, width=1)
    elif theme.frame_style == "corners":
        arm = round(min(w, h) * 0.08)
        for cx, cy, dx, dy in [(m, m, 1, 1), (w - m, m, -1, 1),
                               (m, h - m, 1, -1), (w - m, h - m, -1, -1)]:
            draw.line([(cx, cy), (cx + dx * arm, cy)], fill=color, width=4)
            draw.line([(cx, cy), (cx, cy + dy * arm)], fill=color, width=4)


def render_title_card(size: tuple[int, int], theme: Theme, title: str,
                      subtitle: str = "", footer: str = "") -> np.ndarray:
    """A full-frame card: big heading, optional subtitle and footer line."""
    w, h = size
    img = Image.new("RGB", size, theme.background)
    draw = ImageDraw.Draw(img)

    # soft radial glow behind the text lifts the card off a flat colour
    glow = Image.new("L", size, 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.2, h * 0.15, w * 0.8, h * 0.85], fill=45)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=min(w, h) // 8))
    img = Image.composite(Image.new("RGB", size, theme.surface), img, glow)
    draw = ImageDraw.Draw(img)

    _draw_frame(draw, size, theme)

    title_font = load_font(theme.heading_font, round(h * 0.085))
    sub_font = load_font(theme.body_font, round(h * 0.038))
    foot_font = load_font(theme.body_font, round(h * 0.028))

    title_lines = _wrap(draw, title, title_font, round(w * 0.78))
    sub_lines = _wrap(draw, subtitle, sub_font, round(w * 0.7)) if subtitle else []

    line_h = round(h * 0.105)
    sub_h = round(h * 0.055)
    block = len(title_lines) * line_h + (len(sub_lines) * sub_h + round(h * 0.04) if sub_lines else 0)
    y = (h - block) // 2

    for line in title_lines:
        draw.text((w // 2, y), line, font=title_font, fill=theme.primary, anchor="ma")
        y += line_h
    if sub_lines:
        y += round(h * 0.04)
        # short accent rule between heading and subtitle
        draw.line([(w * 0.42, y - h * 0.02), (w * 0.58, y - h * 0.02)],
                  fill=theme.accent, width=2)
        for line in sub_lines:
            draw.text((w // 2, y), line, font=sub_font, fill=theme.text, anchor="ma")
            y += sub_h
    if footer:
        draw.text((w // 2, round(h * 0.88)), footer, font=foot_font,
                  fill=theme.accent, anchor="ma")

    return np.asarray(img)


def overlay_caption(frame_rgb: np.ndarray, theme: Theme, caption: str) -> np.ndarray:
    """Lower-third caption bar burned onto a photo frame."""
    if not caption.strip():
        return frame_rgb
    img = Image.fromarray(frame_rgb).convert("RGBA")
    w, h = img.size
    bar_h = round(h * 0.12)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # gradient backdrop so text stays readable on any photo
    for i in range(bar_h):
        alpha = int(theme.overlay_alpha * 2.2 * (i / bar_h))
        od.line([(0, h - bar_h + i), (w, h - bar_h + i)],
                fill=(0, 0, 0, min(alpha, 200)))
    font = load_font(theme.body_font, round(h * 0.042))
    od.text((round(w * 0.05), h - round(bar_h * 0.62)), caption,
            font=font, fill=(*theme.accent, 255), anchor="lm")

    return np.asarray(Image.alpha_composite(img, overlay).convert("RGB"))
