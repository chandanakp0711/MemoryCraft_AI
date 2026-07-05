"""SQLite persistence layer.

A thin repository around three tables (projects, media, outputs) so the
UI never writes SQL and business logic never touches Streamlit.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from ..config import DB_PATH
from .models import EventDetails, MediaItem, OutputArtifact, Project

_SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    theme       TEXT NOT NULL,
    details     TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS media (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    path        TEXT NOT NULL,
    kind        TEXT NOT NULL,
    caption     TEXT NOT NULL DEFAULT '',
    taken_at    TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    width       INTEGER NOT NULL DEFAULT 0,
    height      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS outputs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    kind        TEXT NOT NULL,
    path        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_media_project ON media(project_id);
CREATE INDEX IF NOT EXISTS idx_outputs_project ON outputs(project_id);
"""


class Database:
    """Repository for projects, their media and generated outputs."""

    def __init__(self, path: Path = DB_PATH):
        self.path = path
        with self._connect() as con:
            con.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        con = sqlite3.connect(self.path)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            yield con
            con.commit()
        finally:
            con.close()

    # ------------------------------------------------------------ projects
    def save_project(self, project: Project) -> Project:
        with self._connect() as con:
            if project.id is None:
                cur = con.execute(
                    "INSERT INTO projects (name, event_type, theme, details, created_at)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (project.name, project.event_type, project.theme,
                     project.details.to_json(), project.created_at))
                project.id = cur.lastrowid
            else:
                con.execute(
                    "UPDATE projects SET name=?, event_type=?, theme=?, details=? WHERE id=?",
                    (project.name, project.event_type, project.theme,
                     project.details.to_json(), project.id))
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        with self._connect() as con:
            row = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        return self._row_to_project(row) if row else None

    def search_projects(self, text: str = "", event_type: str = "",
                        year: str = "") -> list[Project]:
        """Search by free text (name / honoree / location), event and year."""
        sql = "SELECT * FROM projects WHERE 1=1"
        params: list = []
        if text:
            sql += " AND (name LIKE ? OR details LIKE ?)"
            like = f"%{text}%"
            params += [like, like]
        if event_type and event_type != "All":
            sql += " AND event_type = ?"
            params.append(event_type)
        if year and year != "All":
            # match the event date first, fall back to creation date
            sql += " AND (details LIKE ? OR created_at LIKE ?)"
            params += [f'%"event_date": "{year}%', f"{year}%"]
        sql += " ORDER BY created_at DESC"
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        return [self._row_to_project(r) for r in rows]

    def delete_project(self, project_id: int) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM projects WHERE id=?", (project_id,))

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        return Project(id=row["id"], name=row["name"], event_type=row["event_type"],
                       theme=row["theme"], details=EventDetails.from_json(row["details"]),
                       created_at=row["created_at"])

    # --------------------------------------------------------------- media
    def add_media(self, item: MediaItem) -> MediaItem:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO media (project_id, path, kind, caption, taken_at,"
                " sort_order, width, height) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (item.project_id, item.path, item.kind, item.caption,
                 item.taken_at, item.sort_order, item.width, item.height))
            item.id = cur.lastrowid
        return item

    def get_media(self, project_id: int, kind: str = "") -> list[MediaItem]:
        sql = "SELECT * FROM media WHERE project_id=?"
        params: list = [project_id]
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        sql += " ORDER BY sort_order, id"
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        return [MediaItem(**dict(r)) for r in rows]

    def update_caption(self, media_id: int, caption: str) -> None:
        with self._connect() as con:
            con.execute("UPDATE media SET caption=? WHERE id=?", (caption, media_id))

    def delete_media(self, media_id: int) -> None:
        with self._connect() as con:
            con.execute("DELETE FROM media WHERE id=?", (media_id,))

    def clear_media(self, project_id: int, kind: str = "") -> None:
        sql = "DELETE FROM media WHERE project_id=?"
        params: list = [project_id]
        if kind:
            sql += " AND kind=?"
            params.append(kind)
        with self._connect() as con:
            con.execute(sql, params)

    # ------------------------------------------------------------- outputs
    def add_output(self, artifact: OutputArtifact) -> OutputArtifact:
        with self._connect() as con:
            cur = con.execute(
                "INSERT INTO outputs (project_id, kind, path, created_at)"
                " VALUES (?, ?, ?, ?)",
                (artifact.project_id, artifact.kind, artifact.path, artifact.created_at))
            artifact.id = cur.lastrowid
        return artifact

    def get_outputs(self, project_id: int) -> list[OutputArtifact]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT * FROM outputs WHERE project_id=? ORDER BY created_at DESC",
                (project_id,)).fetchall()
        return [OutputArtifact(**dict(r)) for r in rows]
