"""Cinematic video generator built on MoviePy 2.x.

Produces the full film: themed opening scene, Ken Burns photo slides
with captions and crossfades, optional user video clips, synchronized
background music and an elegant closing scene.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Callable, Optional

import cv2
import numpy as np
from moviepy import (AudioFileClip, CompositeVideoClip, ImageClip, VideoClip,
                     VideoFileClip, afx, vfx)

from ..config import (CROSSFADE, KEN_BURNS_ZOOM, PHOTO_DURATION,
                      TITLE_DURATION, VIDEO_FPS, VIDEO_SIZE)
from ..core.events import EventProfile, resolve_text
from ..core.models import MediaItem, Project
from ..core.themes import Theme
from .image_processor import prepare_photo
from .title_cards import overlay_caption, render_title_card

logger = logging.getLogger(__name__)

ProgressCb = Callable[[float, str], None]
_OVERSAMPLE = 1.3          # head-room for zooming without softness
_MAX_VIDEO_CLIP = 8.0      # seconds of each user video used in the film


def _ease(t: float) -> float:
    """Smoothstep easing - motion accelerates and settles gently."""
    return t * t * (3.0 - 2.0 * t)


def _ken_burns_clip(source: np.ndarray, size: tuple[int, int], duration: float,
                    index: int, strength: float) -> VideoClip:
    """Pan & zoom over an oversampled photo.

    Direction alternates deterministically with the slide index so the
    film feels varied but renders identically every time.
    """
    out_w, out_h = size
    src_h, src_w = source.shape[:2]
    zoom_max = 1.0 + (KEN_BURNS_ZOOM - 1.0) * strength

    zoom_in = index % 2 == 0
    # pan corners cycle through 4 diagonal directions
    corners = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    pan_from = corners[index % 4]
    pan_to = corners[(index + 2) % 4]

    def frame(t: float) -> np.ndarray:
        p = _ease(min(max(t / duration, 0.0), 1.0))
        z = (1.0 + (zoom_max - 1.0) * p) if zoom_in else (zoom_max - (zoom_max - 1.0) * p)
        win_w, win_h = src_w / z, src_h / z
        max_x, max_y = src_w - win_w, src_h - win_h
        cx = pan_from[0] + (pan_to[0] - pan_from[0]) * p
        cy = pan_from[1] + (pan_to[1] - pan_from[1]) * p
        x0, y0 = int(max_x * cx), int(max_y * cy)
        window = source[y0:y0 + int(win_h), x0:x0 + int(win_w)]
        return cv2.resize(window, (out_w, out_h), interpolation=cv2.INTER_AREA)

    return VideoClip(frame, duration=duration)


def _static_clip(source: np.ndarray, size: tuple[int, int], duration: float) -> VideoClip:
    frame = cv2.resize(source, size, interpolation=cv2.INTER_AREA)
    return ImageClip(frame).with_duration(duration)


def _fit_video(path: Path, size: tuple[int, int]) -> Optional[VideoClip]:
    """Load a user video, trim it and crop-fill it to the canvas."""
    try:
        clip = VideoFileClip(str(path))
    except Exception:
        logger.warning("Skipping unreadable video %s", path)
        return None
    clip = clip.subclipped(0, min(clip.duration or _MAX_VIDEO_CLIP, _MAX_VIDEO_CLIP))
    w, h = size
    scale = max(w / clip.w, h / clip.h)
    clip = clip.resized(scale).cropped(x_center=clip.w * scale / 2,
                                       y_center=clip.h * scale / 2,
                                       width=w, height=h)
    return clip


def _assemble_with_crossfade(clips: list[VideoClip], size: tuple[int, int],
                             overlap: float) -> CompositeVideoClip:
    """Chain clips with overlapping crossfades on one composite timeline."""
    start = 0.0
    placed = []
    for i, clip in enumerate(clips):
        clip = clip.with_start(start)
        if i > 0:
            clip = clip.with_effects([vfx.CrossFadeIn(overlap)])
        placed.append(clip)
        start += clip.duration - overlap
    total = start + overlap
    return CompositeVideoClip(placed, size=size).with_duration(total)


class VideoGenerator:
    """Renders a complete memory film for a project."""

    def __init__(self, project: Project, theme: Theme, event: EventProfile,
                 size: tuple[int, int] = VIDEO_SIZE, fps: int = VIDEO_FPS):
        self.project = project
        self.theme = theme
        self.event = event
        self.size = size
        self.fps = fps

    # ------------------------------------------------------------ scenes
    def _opening(self) -> VideoClip:
        d = self.project.details
        title = resolve_text(self.event.opening_line, d.title, d.honoree)
        subtitle = d.message or self.event.subtitle
        footer = " • ".join(x for x in (d.event_date, d.location) if x)
        card = render_title_card(self.size, self.theme, title, subtitle, footer)
        return (ImageClip(card).with_duration(TITLE_DURATION)
                .with_effects([vfx.FadeIn(1.2), vfx.FadeOut(0.6)]))

    def _closing(self) -> VideoClip:
        d = self.project.details
        quote = (d.quotes[0] if d.quotes else self.event.quote)
        closing = resolve_text(self.event.closing_line, d.title, d.honoree)
        card = render_title_card(self.size, self.theme, closing, quote,
                                 "Made with MemoryCraft AI")
        return (ImageClip(card).with_duration(TITLE_DURATION)
                .with_effects([vfx.FadeIn(0.8), vfx.FadeOut(1.5)]))

    def _photo_slide(self, item: MediaItem, index: int, duration: float) -> Optional[VideoClip]:
        oversample = _OVERSAMPLE if self.theme.ken_burns else 1.0
        canvas = prepare_photo(Path(item.path), self.size, oversample)
        if canvas is None:
            return None
        if item.caption:
            canvas = overlay_caption(canvas, self.theme, item.caption)
        if self.theme.ken_burns:
            return _ken_burns_clip(canvas, self.size, duration, index,
                                   self.theme.zoom_strength)
        return _static_clip(canvas, self.size, duration)

    # ------------------------------------------------------------ render
    def generate(self, photos: list[MediaItem], videos: list[MediaItem],
                 music_path: Optional[Path], output_path: Path,
                 progress: Optional[ProgressCb] = None) -> Path:
        """Render the film and return the output path.

        Raises ValueError when there is nothing to render; every other
        per-item failure is skipped with a log entry so one bad file
        never kills a 300-photo render.
        """
        notify = progress or (lambda p, m: None)
        if not photos and not videos:
            raise ValueError("Add at least one photo or video before generating.")

        duration = max(2.5, PHOTO_DURATION * self.event.pace)
        clips: list[VideoClip] = [self._opening()]

        total = len(photos)
        for i, item in enumerate(photos):
            notify(0.05 + 0.45 * (i / max(total, 1)),
                   f"Designing slide {i + 1} of {total}")
            slide = self._photo_slide(item, i, duration)
            if slide is not None:
                clips.append(slide)

        # user videos slot in before the closing scene
        for item in videos:
            notify(0.55, f"Weaving in video {Path(item.path).name}")
            vclip = _fit_video(Path(item.path), self.size)
            if vclip is not None:
                clips.append(vclip)

        clips.append(self._closing())
        if len(clips) <= 2:
            raise ValueError("None of the uploaded photos could be processed.")

        notify(0.6, "Composing timeline and transitions")
        film = _assemble_with_crossfade(clips, self.size, CROSSFADE)

        if music_path and Path(music_path).exists():
            notify(0.65, "Synchronizing music")
            film = self._add_music(film, Path(music_path))

        notify(0.7, "Rendering film (this is the longest step)")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        film.write_videofile(
            str(output_path), fps=self.fps, codec="libx264",
            audio_codec="aac", preset="medium", threads=4, logger=None)
        film.close()
        notify(1.0, "Film ready")
        return output_path

    def _add_music(self, film: CompositeVideoClip, music_path: Path) -> CompositeVideoClip:
        try:
            audio = AudioFileClip(str(music_path))
        except Exception:
            logger.warning("Could not read music file %s - rendering silent", music_path)
            return film
        if audio.duration < film.duration:
            loops = math.ceil(film.duration / audio.duration)
            audio = audio.with_effects([afx.AudioLoop(n_loops=loops)])
        audio = (audio.subclipped(0, film.duration)
                 .with_effects([afx.AudioFadeIn(1.0), afx.AudioFadeOut(3.0)]))
        return film.with_audio(audio)
