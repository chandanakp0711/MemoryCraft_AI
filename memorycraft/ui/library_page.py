"""'Memory Library' page - search, manage and re-download past projects."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..core.events import EVENTS, get_event
from ..services import ProjectService

_MIME = {"video": "video/mp4", "pdf": "application/pdf",
         "collage": "image/jpeg", "timeline": "text/html", "qr": "image/png"}
_ICON = {"video": "🎞️", "pdf": "📖", "collage": "🖼️", "timeline": "🗓️", "qr": "🔗"}


def render(service: ProjectService) -> None:
    st.header("🗂️ Memory Library")
    st.caption("Every celebration you have crafted, searchable and re-downloadable.")

    col_text, col_event, col_year = st.columns([2, 1, 1])
    with col_text:
        text = st.text_input("Search", placeholder="Search by name, person or location…")
    with col_event:
        event = st.selectbox("Event", ["All"] + list(EVENTS))
    with col_year:
        years = ["All"] + [str(y) for y in range(2026, 1999, -1)]
        year = st.selectbox("Year", years)

    projects = service.db.search_projects(text.strip(), event, year)
    if not projects:
        st.info("No memories found. Create your first one from the **Create Memory** page!")
        return

    st.caption(f"{len(projects)} project(s) found")
    for project in projects:
        profile = get_event(project.event_type)
        with st.expander(f"{profile.emoji} **{project.name}** · {project.event_type}"
                         f" · {project.details.event_date or project.created_at[:10]}"):
            _project_panel(service, project)


def _project_panel(service: ProjectService, project) -> None:
    details = project.details
    meta = " · ".join(x for x in (details.honoree, details.location,
                                  f"theme: {project.theme}") if x)
    if meta:
        st.caption(meta)

    photos = service.db.get_media(project.id, "photo")
    if photos:
        cols = st.columns(8)
        for i, item in enumerate(photos[:8]):
            with cols[i]:
                if Path(item.path).exists():
                    st.image(item.path, width='stretch')

    outputs = [o for o in service.db.get_outputs(project.id) if Path(o.path).exists()]
    if outputs:
        st.markdown("**Generated outputs**")
        for out in outputs:
            col_info, col_dl = st.columns([3, 1])
            col_info.write(f"{_ICON.get(out.kind, '📄')} {out.kind.title()} · "
                           f"{out.created_at[:16].replace('T', ' ')}")
            col_dl.download_button(
                "Download", Path(out.path).read_bytes(),
                file_name=Path(out.path).name,
                mime=_MIME.get(out.kind, "application/octet-stream"),
                key=f"dl_{out.id}")
    else:
        st.caption("No outputs generated yet.")

    col_open, col_del = st.columns([1, 1])
    if col_open.button("✏️ Open in editor", key=f"open_{project.id}"):
        st.session_state["draft_project_id"] = project.id
        st.session_state["nav_page"] = "✨ Create Memory"
        st.rerun()
    if col_del.button("🗑️ Delete project", key=f"del_{project.id}"):
        st.session_state[f"confirm_del_{project.id}"] = True
    if st.session_state.get(f"confirm_del_{project.id}"):
        st.warning(f"Delete **{project.name}** and all its media? This cannot be undone.")
        c_yes, c_no = st.columns(2)
        if c_yes.button("Yes, delete", key=f"yes_{project.id}", type="primary"):
            service.db.delete_project(project.id)
            st.session_state.pop(f"confirm_del_{project.id}", None)
            if st.session_state.get("draft_project_id") == project.id:
                st.session_state.pop("draft_project_id", None)
            st.rerun()
        if c_no.button("Keep it", key=f"no_{project.id}"):
            st.session_state.pop(f"confirm_del_{project.id}", None)
            st.rerun()
