"""Printable PDF memory book (ReportLab).

Cover -> event information -> timeline -> photo pages with captions ->
family wishes -> thank-you page, all painted with the project theme.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

from ..core.events import EventProfile, resolve_text
from ..core.models import MediaItem, Project
from ..core.themes import Theme

logger = logging.getLogger(__name__)

PAGE_W, PAGE_H = A4


def _rl_color(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    return tuple(c / 255 for c in rgb)


class PDFBookBuilder:
    """Streams the memory book page by page onto a ReportLab canvas."""

    def __init__(self, project: Project, theme: Theme, event: EventProfile):
        self.project = project
        self.theme = theme
        self.event = event

    # ------------------------------------------------------------ helpers
    def _paint_background(self, c: rl_canvas.Canvas, dark: bool = True) -> None:
        color = self.theme.background if dark else (252, 250, 246)
        c.setFillColorRGB(*_rl_color(color))
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    def _frame(self, c: rl_canvas.Canvas) -> None:
        c.setStrokeColorRGB(*_rl_color(self.theme.primary))
        c.setLineWidth(1.2)
        m = 12 * mm
        c.rect(m, m, PAGE_W - 2 * m, PAGE_H - 2 * m, fill=0, stroke=1)

    def _heading(self, c: rl_canvas.Canvas, text: str, y: float,
                 size: int = 26) -> None:
        c.setFillColorRGB(*_rl_color(self.theme.primary))
        c.setFont("Times-Bold", size)
        c.drawCentredString(PAGE_W / 2, y, text)

    def _body(self, c: rl_canvas.Canvas, text: str, y: float, size: int = 12,
              color: Optional[tuple[int, int, int]] = None) -> None:
        c.setFillColorRGB(*_rl_color(color or self.theme.text))
        c.setFont("Helvetica", size)
        c.drawCentredString(PAGE_W / 2, y, text)

    def _place_photo(self, c: rl_canvas.Canvas, path: Path, x: float, y: float,
                     max_w: float, max_h: float) -> bool:
        """Draw a photo centred in a box, preserving aspect ratio."""
        try:
            with Image.open(path) as img:
                img = ImageOps.exif_transpose(img).convert("RGB")
                iw, ih = img.size
                scale = min(max_w / iw, max_h / ih)
                dw, dh = iw * scale, ih * scale
                reader = ImageReader(img)
                px = x + (max_w - dw) / 2
                py = y + (max_h - dh) / 2
                c.drawImage(reader, px, py, dw, dh)
                c.setStrokeColorRGB(*_rl_color(self.theme.primary))
                c.setLineWidth(1)
                c.rect(px, py, dw, dh, fill=0, stroke=1)
            return True
        except Exception:
            logger.warning("PDF: skipping unreadable photo %s", path)
            return False

    # -------------------------------------------------------------- pages
    def _cover(self, c: rl_canvas.Canvas) -> None:
        d = self.project.details
        self._paint_background(c)
        self._frame(c)
        title = resolve_text(self.event.opening_line, d.title, d.honoree)
        self._heading(c, title, PAGE_H * 0.62, 30)
        if d.message or self.event.subtitle:
            self._body(c, d.message or self.event.subtitle, PAGE_H * 0.54, 13)
        c.setStrokeColorRGB(*_rl_color(self.theme.accent))
        c.line(PAGE_W * 0.35, PAGE_H * 0.5, PAGE_W * 0.65, PAGE_H * 0.5)
        info = " • ".join(x for x in (d.event_date, d.location) if x)
        if info:
            self._body(c, info, PAGE_H * 0.45, 12, self.theme.accent)
        self._body(c, "A MemoryCraft AI Album", PAGE_H * 0.1, 9, self.theme.accent)
        c.showPage()

    def _event_info(self, c: rl_canvas.Canvas) -> None:
        d = self.project.details
        self._paint_background(c)
        self._frame(c)
        self._heading(c, "The Occasion", PAGE_H - 60 * mm + 30 * mm)
        rows = [("Event", self.project.event_type),
                ("Celebrating", d.honoree or d.title or "-"),
                ("Date", d.event_date or "-"),
                ("Location", d.location or "-"),
                ("Theme", self.theme.name)]
        y = PAGE_H * 0.65
        for label, value in rows:
            c.setFont("Helvetica-Bold", 12)
            c.setFillColorRGB(*_rl_color(self.theme.accent))
            c.drawRightString(PAGE_W * 0.45, y, label)
            c.setFont("Helvetica", 12)
            c.setFillColorRGB(*_rl_color(self.theme.text))
            c.drawString(PAGE_W * 0.5, y, str(value))
            y -= 11 * mm
        quote = d.quotes[0] if d.quotes else self.event.quote
        if quote:
            c.setFont("Times-Italic", 14)
            c.setFillColorRGB(*_rl_color(self.theme.primary))
            c.drawCentredString(PAGE_W / 2, PAGE_H * 0.25, f'"{quote}"')
        c.showPage()

    def _timeline(self, c: rl_canvas.Canvas, photos: list[MediaItem]) -> None:
        dated = sorted((p for p in photos if p.taken_at), key=lambda p: p.taken_at)
        if not dated:
            return
        self._paint_background(c)
        self._frame(c)
        self._heading(c, "Timeline of Memories", PAGE_H - 30 * mm)
        x_line = PAGE_W * 0.3
        c.setStrokeColorRGB(*_rl_color(self.theme.accent))
        c.setLineWidth(1.5)
        top, bottom = PAGE_H - 45 * mm, 30 * mm
        c.line(x_line, top, x_line, bottom)
        entries = dated[:14]
        step = (top - bottom) / max(len(entries), 1)
        for i, item in enumerate(entries):
            y = top - step * (i + 0.5)
            c.setFillColorRGB(*_rl_color(self.theme.primary))
            c.circle(x_line, y, 2.2, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 10)
            c.drawRightString(x_line - 5 * mm, y - 1.5, item.taken_at[:10])
            c.setFont("Helvetica", 10)
            c.setFillColorRGB(*_rl_color(self.theme.text))
            caption = item.caption or Path(item.path).stem.replace("-", " ").title()
            c.drawString(x_line + 5 * mm, y - 1.5, caption[:60])
        c.showPage()

    def _photo_pages(self, c: rl_canvas.Canvas, photos: list[MediaItem]) -> None:
        margin = 18 * mm
        slot_h = (PAGE_H - 2 * margin - 20 * mm) / 2
        for i in range(0, len(photos), 2):
            self._paint_background(c, dark=False)
            pair = photos[i:i + 2]
            for j, item in enumerate(pair):
                y = PAGE_H - margin - slot_h * (j + 1) - 10 * mm * j
                ok = self._place_photo(c, Path(item.path), margin, y,
                                       PAGE_W - 2 * margin, slot_h)
                if ok and item.caption:
                    c.setFont("Times-Italic", 11)
                    c.setFillColorRGB(*_rl_color((80, 70, 60)))
                    c.drawCentredString(PAGE_W / 2, y - 4 * mm, item.caption)
            c.setFont("Helvetica", 8)
            c.setFillColorRGB(*_rl_color((150, 140, 130)))
            c.drawCentredString(PAGE_W / 2, 10 * mm, f"{i // 2 + 3}")
            c.showPage()

    def _wishes(self, c: rl_canvas.Canvas) -> None:
        wishes = [w for w in self.project.details.wishes if w.strip()]
        if not wishes:
            return
        self._paint_background(c)
        self._frame(c)
        self._heading(c, "Wishes & Blessings", PAGE_H - 30 * mm)
        y = PAGE_H - 50 * mm
        c.setFont("Times-Italic", 12)
        for wish in wishes[:16]:
            c.setFillColorRGB(*_rl_color(self.theme.text))
            c.drawCentredString(PAGE_W / 2, y, f'"{wish[:90]}"')
            y -= 12 * mm
            if y < 25 * mm:
                break
        c.showPage()

    def _thank_you(self, c: rl_canvas.Canvas) -> None:
        d = self.project.details
        self._paint_background(c)
        self._frame(c)
        closing = resolve_text(self.event.closing_line, d.title, d.honoree)
        self._heading(c, "Thank You", PAGE_H * 0.58, 30)
        self._body(c, closing, PAGE_H * 0.48, 13)
        self._body(c, "Crafted with MemoryCraft AI", PAGE_H * 0.1, 9, self.theme.accent)
        c.showPage()

    # -------------------------------------------------------------- build
    def build(self, photos: list[MediaItem], output_path: Path) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        c = rl_canvas.Canvas(str(output_path), pagesize=A4)
        c.setTitle(self.project.name or "Memory Book")
        c.setAuthor("MemoryCraft AI")
        self._cover(c)
        self._event_info(c)
        self._timeline(c, photos)
        self._photo_pages(c, photos)
        self._wishes(c)
        self._thank_you(c)
        c.save()
        return output_path
