"""Domain models shared across the UI, processing and persistence layers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class EventDetails:
    """Everything the user tells us about the occasion."""

    title: str = ""
    honoree: str = ""              # birthday person, couple, graduate ...
    event_date: str = ""           # ISO date string
    location: str = ""
    message: str = ""              # dedication / wish shown on the cover
    quotes: list[str] = field(default_factory=list)
    wishes: list[str] = field(default_factory=list)   # "From Mom: ..." lines

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "EventDetails":
        try:
            return cls(**json.loads(raw or "{}"))
        except (TypeError, ValueError):
            return cls()


@dataclass
class MediaItem:
    """A single uploaded photo / video / audio track."""

    id: Optional[int] = None
    project_id: Optional[int] = None
    path: str = ""
    kind: str = "photo"            # photo | video | audio
    caption: str = ""
    taken_at: Optional[str] = None  # ISO datetime from EXIF when available
    sort_order: int = 0
    width: int = 0
    height: int = 0


@dataclass
class Project:
    """One memory project = event + media + generated outputs."""

    id: Optional[int] = None
    name: str = ""
    event_type: str = "Birthday"
    theme: str = "Elegant Gold"
    details: EventDetails = field(default_factory=EventDetails)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


@dataclass
class OutputArtifact:
    """A generated deliverable (video, pdf, collage, timeline, qr...)."""

    id: Optional[int] = None
    project_id: Optional[int] = None
    kind: str = ""                 # video | pdf | collage | timeline | qr
    path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
