"""Generate sample photos (with EXIF dates) for trying out MemoryCraft AI.

Run once:  python scripts/make_samples.py
Creates assets/samples/ with colourful demo images you can upload.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw

from memorycraft.config import SAMPLE_DIR
from memorycraft.utils.fonts import load_font

SCENES = [
    ("Golden Hour", (255, 179, 71), (120, 60, 20), "landscape"),
    ("By the Sea", (64, 164, 223), (10, 40, 80), "landscape"),
    ("Garden Party", (134, 168, 115), (30, 60, 25), "portrait"),
    ("City Lights", (90, 70, 160), (20, 12, 40), "landscape"),
    ("First Dance", (196, 88, 122), (60, 20, 40), "portrait"),
    ("Family Table", (210, 160, 90), (70, 45, 20), "landscape"),
    ("Candle Glow", (255, 140, 60), (50, 25, 10), "portrait"),
    ("Morning Walk", (170, 200, 220), (40, 60, 80), "landscape"),
]


def make_image(title: str, top: tuple, bottom: tuple, orient: str) -> Image.Image:
    size = (1600, 1000) if orient == "landscape" else (1000, 1500)
    img = Image.new("RGB", size)
    draw = ImageDraw.Draw(img)
    w, h = size
    for y in range(h):  # vertical gradient
        t = y / h
        color = tuple(round(a + (b - a) * t) for a, b in zip(top, bottom))
        draw.line([(0, y), (w, y)], fill=color)
    # simple sun/moon disc for visual interest
    r = min(w, h) // 6
    draw.ellipse([w * 0.62, h * 0.14, w * 0.62 + r, h * 0.14 + r],
                 fill=tuple(min(c + 60, 255) for c in top))
    font = load_font("serif-bold", h // 14)
    draw.text((w // 2, int(h * 0.82)), title, font=font,
              fill=(255, 255, 255), anchor="mm")
    return img


def main() -> None:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    for i, (title, top, bottom, orient) in enumerate(SCENES):
        img = make_image(title, top, bottom, orient)
        exif = Image.Exif()
        exif[36867] = f"2026:06:{10 + i:02d} 1{i}:30:00"   # DateTimeOriginal
        path = SAMPLE_DIR / f"sample_{i + 1:02d}_{title.lower().replace(' ', '_')}.jpg"
        img.save(path, quality=90, exif=exif)
        print(f"created {path}")
    print(f"\n{len(SCENES)} sample photos in {SAMPLE_DIR}")


if __name__ == "__main__":
    main()
