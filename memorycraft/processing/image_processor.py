"""Image intelligence: EXIF sorting, duplicate removal, enhancement and
orientation-aware framing.

Every function is pure (path/array in, array/data out) so the pipeline is
easy to test and reuse outside Streamlit.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Pillow EXIF tag ids
_TAG_DATETIME_ORIGINAL = 36867
_TAG_DATETIME = 306


# --------------------------------------------------------------- metadata
def read_capture_time(path: Path) -> Optional[str]:
    """Extract the capture timestamp from EXIF, ISO formatted, or None."""
    try:
        with Image.open(path) as img:
            exif = img.getexif()
            raw = exif.get(_TAG_DATETIME_ORIGINAL) or exif.get(_TAG_DATETIME)
        if raw:
            return datetime.strptime(str(raw), "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception:  # corrupt EXIF must never break the pipeline
        logger.debug("No usable EXIF date in %s", path)
    return None


def read_dimensions(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as img:
            return img.size
    except Exception:
        return (0, 0)


def is_valid_image(path: Path) -> bool:
    """Cheap integrity check used before a file enters a project."""
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


# ------------------------------------------------------------- duplicates
def image_signature(path: Path, hash_size: int = 8
                    ) -> Optional[tuple[int, tuple[float, float, float]]]:
    """Perceptual signature: (per-channel average-hash, mean RGB colour).

    The 192-bit hash captures spatial structure; the mean colour guards
    against different scenes that merely share a brightness layout
    (sunsets vs. seascapes) being mistaken for one another.
    """
    try:
        with Image.open(path) as img:
            small = img.convert("RGB").resize((hash_size, hash_size),
                                              Image.Resampling.LANCZOS)
        pixels = np.asarray(small, dtype=np.float32)
        bits = []
        for c in range(3):
            channel = pixels[:, :, c]
            bits.extend(channel.flatten() > channel.mean())
        h = int("".join("1" if b else "0" for b in bits), 2)
        mean_rgb = tuple(float(pixels[:, :, c].mean()) for c in range(3))
        return h, mean_rgb
    except Exception:
        return None


def find_duplicates(paths: list[Path], hash_threshold: int = 12,
                    color_threshold: float = 25.0) -> set[Path]:
    """Return the *later* file of every near-duplicate pair.

    Duplicates must match in structure (hamming distance of the 192-bit
    hash <= hash_threshold) AND colour (euclidean mean-RGB distance <=
    color_threshold); the first occurrence is always kept.
    """
    seen: list[tuple[int, tuple[float, float, float]]] = []
    duplicates: set[Path] = set()
    for path in paths:
        sig = image_signature(path)
        if sig is None:
            continue
        h, rgb = sig
        is_dupe = any(
            bin(h ^ prev_h).count("1") <= hash_threshold
            and math.dist(rgb, prev_rgb) <= color_threshold
            for prev_h, prev_rgb in seen)
        if is_dupe:
            duplicates.add(path)
        else:
            seen.append((h, rgb))
    return duplicates


# ------------------------------------------------------------ enhancement
def enhance(image: np.ndarray) -> np.ndarray:
    """Gentle, professional-looking auto-enhancement (BGR in / BGR out).

    CLAHE on lightness restores contrast in flat photos, a small
    saturation lift adds life, and a mild unsharp mask crisps details -
    all conservative enough to never look 'filtered'.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.8, tileGridSize=(8, 8))
    lab = cv2.merge((clahe.apply(l), a, b))
    out = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    hsv = cv2.cvtColor(out, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.08, 0, 255)
    out = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    blur = cv2.GaussianBlur(out, (0, 0), sigmaX=2.0)
    return cv2.addWeighted(out, 1.25, blur, -0.25, 0)


# ---------------------------------------------------------------- framing
def load_bgr(path: Path) -> Optional[np.ndarray]:
    """Load any image as BGR, honouring EXIF rotation. None on failure."""
    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    except Exception:
        logger.warning("Could not load image %s", path)
        return None


def fit_to_canvas(image: np.ndarray, size: tuple[int, int],
                  enhance_quality: bool = True) -> np.ndarray:
    """Frame a photo on a fixed canvas without distortion.

    Landscape shots that roughly match the canvas are cover-cropped;
    portraits and odd ratios are letterboxed over a blurred, darkened
    blow-up of themselves - the standard cinematic treatment.
    Returns RGB (ready for MoviePy / Pillow).
    """
    if enhance_quality:
        image = enhance(image)

    cw, ch = size
    h, w = image.shape[:2]
    canvas_ratio, image_ratio = cw / ch, w / h

    if 0.85 <= image_ratio / canvas_ratio <= 1.25:
        # close enough: crop-to-fill keeps the frame edge-to-edge
        scale = max(cw / w, ch / h)
        resized = cv2.resize(image, (round(w * scale), round(h * scale)),
                             interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
        y0 = (resized.shape[0] - ch) // 2
        x0 = (resized.shape[1] - cw) // 2
        framed = resized[y0:y0 + ch, x0:x0 + cw]
    else:
        # blurred-fill letterbox for portraits / panoramas
        bg_scale = max(cw / w, ch / h)
        bg = cv2.resize(image, (round(w * bg_scale), round(h * bg_scale)))
        y0 = (bg.shape[0] - ch) // 2
        x0 = (bg.shape[1] - cw) // 2
        bg = bg[y0:y0 + ch, x0:x0 + cw]
        bg = cv2.GaussianBlur(bg, (0, 0), sigmaX=25)
        bg = (bg * 0.55).astype(np.uint8)

        fg_scale = min(cw / w, ch / h)
        fg = cv2.resize(image, (round(w * fg_scale), round(h * fg_scale)),
                        interpolation=cv2.INTER_AREA if fg_scale < 1 else cv2.INTER_CUBIC)
        fy = (ch - fg.shape[0]) // 2
        fx = (cw - fg.shape[1]) // 2
        bg[fy:fy + fg.shape[0], fx:fx + fg.shape[1]] = fg
        framed = bg

    return cv2.cvtColor(framed, cv2.COLOR_BGR2RGB)


def prepare_photo(path: Path, size: tuple[int, int],
                  oversample: float = 1.0) -> Optional[np.ndarray]:
    """Full pipeline for one photo -> RGB canvas (optionally oversampled
    so the Ken Burns effect can zoom without losing sharpness)."""
    image = load_bgr(path)
    if image is None:
        return None
    target = (round(size[0] * oversample), round(size[1] * oversample))
    return fit_to_canvas(image, target)
