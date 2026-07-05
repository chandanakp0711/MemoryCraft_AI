"""Application service layer.

Orchestrates the domain: ingesting uploads (validate -> dedupe -> EXIF
sort) and generating every deliverable. The Streamlit UI only ever talks
to this module, keeping business logic framework-free.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from .config import PREVIEW_FPS, PREVIEW_SIZE, VIDEO_FPS, VIDEO_SIZE
from .core.database import Database
from .core.events import get_event
from .core.models import MediaItem, OutputArtifact, Project
from .core.themes import get_theme
from .processing.collage import build_collage
from .processing.image_processor import (find_duplicates, is_valid_image,
                                         read_capture_time, read_dimensions)
from .processing.pdf_builder import PDFBookBuilder
from .processing.qr_share import build_qr_card
from .processing.timeline import build_timeline
from .processing.video_generator import VideoGenerator
from .utils.files import project_output_dir, save_upload, slugify

logger = logging.getLogger(__name__)
ProgressCb = Callable[[float, str], None]


class ProjectService:
    """High-level operations the UI calls."""

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    # ---------------------------------------------------------- ingestion
    def ingest_uploads(self, project: Project,
                       uploads: list[tuple[str, bytes]],
                       kind: str, captions: Optional[dict[str, str]] = None
                       ) -> tuple[int, int, list[str]]:
        """Store uploads for a project.

        Photos are validated, de-duplicated and sorted by EXIF capture
        time when available. Returns (added, skipped, messages).
        """
        captions = captions or {}
        errors: list[str] = []
        saved: list[Path] = []

        for filename, data in uploads:
            path, err = save_upload(project.id, filename, data)
            if err:
                errors.append(err)
                continue
            if kind == "photo" and not is_valid_image(path):
                errors.append(f"{filename} is not a readable image - skipped")
                path.unlink(missing_ok=True)
                continue
            saved.append(path)

        skipped = 0
        if kind == "photo" and len(saved) > 1:
            dupes = find_duplicates(saved)
            for d in dupes:
                d.unlink(missing_ok=True)
            skipped = len(dupes)
            saved = [p for p in saved if p not in dupes]

        # chronological ordering: EXIF date first, then filename
        def sort_key(p: Path):
            taken = read_capture_time(p) if kind == "photo" else None
            return (taken or "9999", p.name)

        saved.sort(key=sort_key)
        existing = len(self.db.get_media(project.id, kind))
        for order, path in enumerate(saved, start=existing):
            w, h = read_dimensions(path) if kind == "photo" else (0, 0)
            self.db.add_media(MediaItem(
                project_id=project.id, path=str(path), kind=kind,
                caption=captions.get(path.name, ""),
                taken_at=read_capture_time(path) if kind == "photo" else None,
                sort_order=order, width=w, height=h))
        return len(saved), skipped, errors

    # --------------------------------------------------------- generation
    def _output_path(self, project: Project, suffix: str, ext: str) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{slugify(project.name)}_{suffix}_{stamp}.{ext}"
        return project_output_dir(project.id) / name

    def generate_video(self, project: Project, draft: bool = False,
                       progress: Optional[ProgressCb] = None) -> Path:
        theme = get_theme(project.theme)
        event = get_event(project.event_type)
        photos = self.db.get_media(project.id, "photo")
        videos = self.db.get_media(project.id, "video")
        music = self.db.get_media(project.id, "audio")
        music_path = Path(music[0].path) if music else None

        size, fps = (PREVIEW_SIZE, PREVIEW_FPS) if draft else (VIDEO_SIZE, VIDEO_FPS)
        generator = VideoGenerator(project, theme, event, size, fps)
        out = generator.generate(photos, videos, music_path,
                                 self._output_path(project, "film", "mp4"),
                                 progress)
        self.db.add_output(OutputArtifact(project_id=project.id, kind="video",
                                          path=str(out)))
        return out

    def generate_pdf(self, project: Project) -> Path:
        theme = get_theme(project.theme)
        event = get_event(project.event_type)
        photos = self.db.get_media(project.id, "photo")
        builder = PDFBookBuilder(project, theme, event)
        out = builder.build(photos, self._output_path(project, "memory-book", "pdf"))
        self.db.add_output(OutputArtifact(project_id=project.id, kind="pdf",
                                          path=str(out)))
        return out

    def generate_collage(self, project: Project) -> Optional[Path]:
        theme = get_theme(project.theme)
        photos = self.db.get_media(project.id, "photo")
        out = build_collage([Path(p.path) for p in photos], theme,
                            project.details.title or project.name,
                            self._output_path(project, "collage", "jpg"))
        if out:
            self.db.add_output(OutputArtifact(project_id=project.id,
                                              kind="collage", path=str(out)))
        return out

    def generate_timeline(self, project: Project):
        """Returns (figure, html_path) - figure is None with no dated photos."""
        theme = get_theme(project.theme)
        photos = self.db.get_media(project.id, "photo")
        html_path = self._output_path(project, "timeline", "html")
        fig = build_timeline(photos, theme,
                             project.details.title or project.name, html_path)
        if fig is not None:
            self.db.add_output(OutputArtifact(project_id=project.id,
                                              kind="timeline", path=str(html_path)))
            return fig, html_path
        return None, None

    def generate_qr(self, project: Project, link: str) -> Path:
        theme = get_theme(project.theme)
        out = build_qr_card(link, theme,
                            project.details.title or project.name,
                            self._output_path(project, "share-qr", "png"))
        self.db.add_output(OutputArtifact(project_id=project.id, kind="qr",
                                          path=str(out)))
        return out
