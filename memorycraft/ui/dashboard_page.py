"""Dashboard - welcome hero, stats and recent projects."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..core.events import EVENTS, get_event
from ..services import ProjectService
from .styles import hero, stat_card


def render(service: ProjectService) -> None:
    st.markdown(hero(
        "MemoryCraft AI",
        "Turn ordinary photos into cinematic stories - films, memory books, "
        "timelines and collages, all generated automatically."),
        unsafe_allow_html=True)

    projects = service.db.search_projects()
    total_outputs = sum(len(service.db.get_outputs(p.id)) for p in projects)
    total_photos = sum(len(service.db.get_media(p.id, "photo")) for p in projects)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card(str(len(projects)), "Projects"), unsafe_allow_html=True)
    c2.markdown(stat_card(str(total_photos), "Photos"), unsafe_allow_html=True)
    c3.markdown(stat_card(str(total_outputs), "Creations"), unsafe_allow_html=True)
    c4.markdown(stat_card(str(len(EVENTS)), "Occasions"), unsafe_allow_html=True)

    st.divider()
    col_recent, col_start = st.columns([3, 2])

    with col_recent:
        st.subheader("Recent memories")
        if not projects:
            st.info("Nothing here yet - your first memory is one click away. 👉")
        for project in projects[:5]:
            profile = get_event(project.event_type)
            st.markdown(
                f'<div class="mc-card"><span class="title">{profile.emoji} '
                f'{project.name}</span><br>'
                f'<span class="mc-badge">{project.event_type}</span>'
                f'<span class="mc-badge">{project.theme}</span>'
                f'<span class="meta">created {project.created_at[:10]}</span></div>',
                unsafe_allow_html=True)
            photos = service.db.get_media(project.id, "photo")
            if photos:
                cols = st.columns(6)
                for i, item in enumerate(photos[:6]):
                    with cols[i]:
                        if Path(item.path).exists():
                            st.image(item.path, width='stretch')

    with col_start:
        st.subheader("Start something beautiful")
        st.write("Pick an occasion and let MemoryCraft handle the editing, "
                 "design and layout:")
        for profile in list(EVENTS.values())[:6]:
            if st.button(f"{profile.emoji} {profile.name}", key=f"quick_{profile.name}",
                         width='stretch'):
                st.session_state["nav_page"] = "✨ Create Memory"
                st.rerun()
        st.caption("…and 9 more occasions on the Create page.")
