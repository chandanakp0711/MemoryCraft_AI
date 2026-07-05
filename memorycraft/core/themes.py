"""Visual theme registry.

A theme is the single source of truth for typography, colour, motion and
layout. Video, PDF, collage and timeline generators all consume the same
Theme object so every deliverable in a project looks like one family.

Colours are (R, G, B) tuples so they can feed Pillow, OpenCV (after BGR
swap), ReportLab (scaled to 0-1) and CSS (via hex helper) alike.
"""

from __future__ import annotations

from dataclasses import dataclass

RGB = tuple[int, int, int]


@dataclass(frozen=True)
class Theme:
    name: str
    # -- colour -----------------------------------------------------------
    background: RGB          # title cards / pdf page base
    surface: RGB             # panels, caption bars
    primary: RGB             # headings, borders
    accent: RGB              # decorative flourishes
    text: RGB                # body text on background
    # -- typography (keys into config.FONT_CANDIDATES) --------------------
    heading_font: str = "serif-bold"
    body_font: str = "sans"
    # -- motion -----------------------------------------------------------
    transition: str = "crossfade"     # crossfade | slide | zoom
    ken_burns: bool = True
    zoom_strength: float = 1.0        # multiplies config.KEN_BURNS_ZOOM
    # -- decoration -------------------------------------------------------
    frame_style: str = "line"         # line | double | corners | none
    overlay_alpha: int = 70           # darkness of caption backdrop (0-255)

    def hex(self, rgb: RGB) -> str:
        return "#{:02x}{:02x}{:02x}".format(*rgb)


THEMES: dict[str, Theme] = {t.name: t for t in [
    Theme("Elegant Gold",
          background=(20, 16, 8), surface=(38, 32, 18),
          primary=(212, 175, 55), accent=(245, 222, 130), text=(245, 240, 225),
          heading_font="serif-bold", body_font="serif",
          transition="crossfade", zoom_strength=1.0, frame_style="double"),
    Theme("Royal",
          background=(18, 10, 40), surface=(35, 22, 66),
          primary=(190, 155, 255), accent=(255, 215, 0), text=(240, 236, 250),
          heading_font="serif-bold", body_font="serif",
          transition="crossfade", zoom_strength=1.1, frame_style="double"),
    Theme("Classic",
          background=(24, 24, 24), surface=(40, 40, 40),
          primary=(200, 200, 200), accent=(150, 150, 150), text=(235, 235, 235),
          heading_font="serif-bold", body_font="serif",
          transition="crossfade", zoom_strength=0.9, frame_style="line"),
    Theme("Minimal",
          background=(248, 248, 246), surface=(255, 255, 255),
          primary=(30, 30, 30), accent=(120, 120, 120), text=(40, 40, 40),
          heading_font="sans-bold", body_font="sans",
          transition="slide", ken_burns=False, frame_style="none",
          overlay_alpha=40),
    Theme("Floral",
          background=(253, 245, 246), surface=(250, 232, 235),
          primary=(196, 88, 122), accent=(134, 168, 115), text=(70, 45, 55),
          heading_font="script", body_font="serif",
          transition="crossfade", zoom_strength=0.9, frame_style="corners"),
    Theme("Vintage",
          background=(46, 39, 30), surface=(66, 56, 42),
          primary=(201, 173, 127), accent=(160, 120, 85), text=(232, 220, 200),
          heading_font="serif", body_font="serif",
          transition="crossfade", zoom_strength=0.8, frame_style="line"),
    Theme("Luxury",
          background=(10, 10, 12), surface=(25, 25, 30),
          primary=(230, 200, 120), accent=(255, 255, 255), text=(240, 238, 230),
          heading_font="serif-bold", body_font="sans",
          transition="zoom", zoom_strength=1.2, frame_style="double"),
    Theme("Modern",
          background=(15, 20, 30), surface=(28, 36, 52),
          primary=(80, 180, 255), accent=(255, 90, 120), text=(235, 240, 248),
          heading_font="sans-bold", body_font="sans",
          transition="slide", zoom_strength=1.1, frame_style="none"),
    Theme("Kids",
          background=(255, 250, 235), surface=(255, 240, 200),
          primary=(255, 105, 97), accent=(64, 185, 220), text=(60, 50, 45),
          heading_font="script", body_font="sans",
          transition="zoom", zoom_strength=1.15, frame_style="corners",
          overlay_alpha=50),
    Theme("Traditional",
          background=(60, 12, 12), surface=(88, 24, 20),
          primary=(255, 178, 44), accent=(255, 214, 120), text=(255, 244, 224),
          heading_font="serif-bold", body_font="serif",
          transition="crossfade", zoom_strength=1.0, frame_style="double"),
]}


def get_theme(name: str) -> Theme:
    """Look up a theme; unknown names fall back to Elegant Gold."""
    return THEMES.get(name, THEMES["Elegant Gold"])
