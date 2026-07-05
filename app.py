"""MemoryCraft AI - application entry point.

Run with:  streamlit run app.py
"""

from __future__ import annotations

import logging

import streamlit as st

from memorycraft import __app_name__, __version__
from memorycraft.services import ProjectService
from memorycraft.ui import create_page, dashboard_page, library_page
from memorycraft.ui.styles import APP_CSS

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(name)s %(levelname)s %(message)s")

st.set_page_config(page_title=__app_name__, page_icon="🎞️",
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(APP_CSS, unsafe_allow_html=True)


@st.cache_resource
def get_service() -> ProjectService:
    """One service (and one SQLite schema check) per server process."""
    return ProjectService()


PAGES = ["🏠 Dashboard", "✨ Create Memory", "🗂️ Memory Library"]


def main() -> None:
    service = get_service()

    with st.sidebar:
        st.title("🎞️ MemoryCraft AI")
        st.caption(f"v{__version__} · your memories, beautifully told")
        # allow other pages to steer navigation via session state
        default = st.session_state.pop("nav_page", None)
        if default in PAGES:
            st.session_state["nav_radio"] = default
        page = st.radio("Navigate", PAGES, key="nav_radio")
        st.divider()
        pid = st.session_state.get("draft_project_id")
        if pid:
            project = service.db.get_project(pid)
            if project:
                st.markdown(f"**Working on:** {project.name}")
                st.caption(f"{project.event_type} · {project.theme}")
        st.divider()
        st.caption("Built with Python · Streamlit · MoviePy · OpenCV · "
                   "Pillow · Plotly · ReportLab")

    if page == PAGES[0]:
        dashboard_page.render(service)
    elif page == PAGES[1]:
        create_page.render(service)
    else:
        library_page.render(service)


if __name__ == "__main__":
    main()
