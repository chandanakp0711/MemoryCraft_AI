"""File-system helpers: safe uploads, validation and project folders."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from ..config import (AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, MAX_UPLOAD_MB,
                      OUTPUT_DIR, UPLOAD_DIR, VIDEO_EXTENSIONS)


def classify_file(filename: str) -> str | None:
    """Return 'photo' | 'video' | 'audio' or None for unsupported files."""
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "photo"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    return None


def slugify(text: str, fallback: str = "project") -> str:
    """Filesystem-safe slug for folder and file names."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text or fallback


def project_upload_dir(project_id: int) -> Path:
    d = UPLOAD_DIR / f"project_{project_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def project_output_dir(project_id: int) -> Path:
    d = OUTPUT_DIR / f"project_{project_id}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_upload(project_id: int, filename: str, data: bytes) -> tuple[Path | None, str]:
    """Persist an uploaded file. Returns (path, error_message).

    Rejects unsupported extensions and oversized files with a human
    message instead of raising, so the UI can report gracefully.
    """
    kind = classify_file(filename)
    if kind is None:
        return None, f"Unsupported file type: {filename}"
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        return None, f"{filename} is larger than {MAX_UPLOAD_MB} MB"
    if not data:
        return None, f"{filename} is empty"

    safe_name = slugify(Path(filename).stem, "file") + Path(filename).suffix.lower()
    dest = project_upload_dir(project_id) / safe_name
    # avoid silently overwriting a different file with the same name
    counter = 1
    while dest.exists():
        dest = dest.with_name(f"{dest.stem}_{counter}{dest.suffix}")
        counter += 1
    dest.write_bytes(data)
    return dest, ""
