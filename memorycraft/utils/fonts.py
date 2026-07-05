"""Font resolution that works on any machine.

Themes ask for a *role* ("serif-bold", "script"...); we hunt the system
font directories for the first matching file and cache the result. When
nothing is found Pillow's bundled bitmap font keeps the app functional.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from PIL import ImageFont

from ..config import FONT_CANDIDATES, SYSTEM_FONT_DIRS


@lru_cache(maxsize=None)
def find_font_file(role: str) -> Optional[str]:
    """Return a path to a .ttf for the given role, or None."""
    for filename in FONT_CANDIDATES.get(role, []) + FONT_CANDIDATES["sans"]:
        for font_dir in SYSTEM_FONT_DIRS:
            candidate = font_dir / filename
            if candidate.exists():
                return str(candidate)
    return None


def load_font(role: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a scalable font for the role, falling back to Pillow's default."""
    path = find_font_file(role)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    # Pillow >= 10.1 can scale its default font
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # very old Pillow
        return ImageFont.load_default()
