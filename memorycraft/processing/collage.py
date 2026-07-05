"""Photo collage builder.

Creates a themed mosaic poster from the project photos - great as a
social-media cover or the PDF book's centrefold.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageDraw

from ..core.themes import Theme
from ..utils.fonts import load_font
from .image_processor import fit_to_canvas, load_bgr

logger = logging.getLogger(__name__)


def build_collage(photo_paths: list[Path], theme: Theme, title: str,
                  output_path: Path, size: tuple[int, int] = (1600, 2000),
                  max_photos: int = 12) -> Optional[Path]:
    """Grid collage with a title band; returns the saved path or None."""
    paths = photo_paths[:max_photos]
    if not paths:
        return None

    w, h = size
    header_h = round(h * 0.12)
    gap = round(w * 0.012)

    cols = 2 if len(paths) <= 4 else 3
    rows = math.ceil(len(paths) / cols)
    cell_w = (w - gap * (cols + 1)) // cols
    cell_h = (h - header_h - gap * (rows + 1)) // rows

    poster = Image.new("RGB", size, theme.background)
    draw = ImageDraw.Draw(poster)

    # header band
    draw.rectangle([0, 0, w, header_h], fill=theme.surface)
    font = load_font(theme.heading_font, round(header_h * 0.42))
    draw.text((w // 2, header_h // 2), title or "Our Memories",
              font=font, fill=theme.primary, anchor="mm")
    draw.line([(gap, header_h), (w - gap, header_h)], fill=theme.accent, width=3)

    placed = 0
    for i, path in enumerate(paths):
        image = load_bgr(path)
        if image is None:
            continue
        tile = fit_to_canvas(image, (cell_w, cell_h), enhance_quality=False)
        col, row = placed % cols, placed // cols
        x = gap + col * (cell_w + gap)
        y = header_h + gap + row * (cell_h + gap)
        poster.paste(Image.fromarray(tile), (x, y))
        draw.rectangle([x, y, x + cell_w, y + cell_h], outline=theme.primary, width=2)
        placed += 1

    if placed == 0:
        return None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    poster.save(output_path, quality=92)
    return output_path
