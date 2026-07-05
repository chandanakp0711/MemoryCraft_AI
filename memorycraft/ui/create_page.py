"""'Create Memory' page - the guided five-step wizard."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from ..core.events import EVENTS, get_event
from ..core.models import EventDetails, Project
from ..core.themes import THEMES
from ..services import ProjectService

_STEPS = ["1 · Occasion", "2 · Memories", "3 · Words", "4 · Style", "5 · Generate"]


def _current_project(service: ProjectService) -> Project | None:
    pid = st.session_state.get("draft_project_id")
    return service.db.get_project(pid) if pid else None


def render(service: ProjectService) -> None:
    st.header("✨ Create a Memory")
    st.caption("Five small steps - MemoryCraft AI does the heavy lifting.")

    step = st.radio("Steps", _STEPS, horizontal=True,
                    key="wizard_step", label_visibility="collapsed")
    st.divider()
    project = _current_project(service)

    if step == _STEPS[0]:
        _step_occasion(service, project)
    elif project is None:
        st.info("Start with **Step 1** to choose your occasion and create the project.")
    elif step == _STEPS[1]:
        _step_memories(service, project)
    elif step == _STEPS[2]:
        _step_words(service, project)
    elif step == _STEPS[3]:
        _step_style(service, project)
    else:
        _step_generate(service, project)


# --------------------------------------------------------------- step 1 ---
def _step_occasion(service: ProjectService, project: Project | None) -> None:
    event_names = [f"{p.emoji} {p.name}" for p in EVENTS.values()]
    default_index = 0
    if project:
        names = list(EVENTS)
        if project.event_type in names:
            default_index = names.index(project.event_type)

    with st.form("occasion_form"):
        chosen = st.selectbox("What are we celebrating?", event_names,
                              index=default_index)
        event_name = chosen.split(" ", 1)[1]
        profile = get_event(event_name)

        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Event title", value=project.details.title if project else "",
                                  placeholder="Riya's 25th Birthday")
            honoree = st.text_input("Who is it for?", value=project.details.honoree if project else "",
                                    placeholder="Riya, Arjun & Meera, The Sharma family…")
        with col2:
            event_date = st.date_input("Event date", value=None, format="DD/MM/YYYY")
            location = st.text_input("Location", value=project.details.location if project else "",
                                     placeholder="Bengaluru, India")
        message = st.text_area("A short dedication for the cover (optional)",
                               value=project.details.message if project else "",
                               placeholder=profile.subtitle or "A few words from the heart…")

        if st.form_submit_button("Save & continue →", type="primary"):
            details = EventDetails(
                title=title.strip(), honoree=honoree.strip(),
                event_date=event_date.isoformat() if event_date else "",
                location=location.strip(), message=message.strip(),
                quotes=project.details.quotes if project else [],
                wishes=project.details.wishes if project else [])
            if project is None:
                project = Project(name=title.strip() or f"{event_name} Memory",
                                  event_type=event_name,
                                  theme=profile.default_theme, details=details)
            else:
                project.name = title.strip() or project.name
                project.event_type = event_name
                project.details = details
            project = service.db.save_project(project)
            st.session_state["draft_project_id"] = project.id
            st.success(f"Project **{project.name}** saved. "
                       f"Suggested music: *{profile.music_mood}*. Move on to Step 2!")


# --------------------------------------------------------------- step 2 ---
def _step_memories(service: ProjectService, project: Project) -> None:
    st.subheader(f"Add memories to *{project.name}*")

    photos = st.file_uploader("Photos", type=["jpg", "jpeg", "png", "webp", "bmp"],
                              accept_multiple_files=True,
                              help="Up to 500 photos. Duplicates are removed automatically.")
    videos = st.file_uploader("Short video clips (optional)",
                              type=["mp4", "mov", "avi", "mkv", "webm"],
                              accept_multiple_files=True)
    music = st.file_uploader("Background music (optional)",
                             type=["mp3", "wav", "ogg", "m4a", "aac"])

    if st.button("Add to project", type="primary"):
        with st.spinner("Organizing your memories - validating, removing duplicates, sorting by date…"):
            total_added = 0
            all_errors: list[str] = []
            if photos:
                added, skipped, errors = service.ingest_uploads(
                    project, [(f.name, f.getvalue()) for f in photos], "photo")
                total_added += added
                all_errors += errors
                if skipped:
                    st.info(f"🧹 Removed {skipped} duplicate photo(s) automatically.")
            if videos:
                added, _, errors = service.ingest_uploads(
                    project, [(f.name, f.getvalue()) for f in videos], "video")
                total_added += added
                all_errors += errors
            if music:
                service.db.clear_media(project.id, "audio")  # one soundtrack at a time
                added, _, errors = service.ingest_uploads(
                    project, [(music.name, music.getvalue())], "audio")
                total_added += added
                all_errors += errors
        for err in all_errors:
            st.warning(err)
        if total_added:
            st.success(f"Added {total_added} file(s) - sorted chronologically where dates were found.")
        elif not all_errors:
            st.info("Choose some files above first.")

    stored = service.db.get_media(project.id, "photo")
    if stored:
        st.caption(f"📸 {len(stored)} photos in this project")
        cols = st.columns(6)
        for i, item in enumerate(stored[:12]):
            with cols[i % 6]:
                if Path(item.path).exists():
                    st.image(item.path, width='stretch')
        if len(stored) > 12:
            st.caption(f"…and {len(stored) - 12} more")


# --------------------------------------------------------------- step 3 ---
def _step_words(service: ProjectService, project: Project) -> None:
    st.subheader("Captions, quotes & wishes")
    photos = service.db.get_media(project.id, "photo")

    with st.form("words_form"):
        st.markdown("**Photo captions** *(shown as lower-thirds in the film and under photos in the book)*")
        captions: dict[int, str] = {}
        for item in photos[:40]:
            col_img, col_cap = st.columns([1, 4])
            with col_img:
                if Path(item.path).exists():
                    st.image(item.path, width=90)
            with col_cap:
                captions[item.id] = st.text_input(
                    f"Caption {item.id}", value=item.caption,
                    key=f"cap_{item.id}", label_visibility="collapsed",
                    placeholder="Say something about this moment…")
        if len(photos) > 40:
            st.caption(f"Showing the first 40 of {len(photos)} photos.")

        st.markdown("**A quote for the closing scene**")
        quote = st.text_input("Quote", value=(project.details.quotes[0] if project.details.quotes else ""),
                              placeholder=get_event(project.event_type).quote,
                              label_visibility="collapsed")
        st.markdown("**Family wishes** *(one per line - they get their own page in the PDF book)*")
        wishes_text = st.text_area("Wishes", value="\n".join(project.details.wishes),
                                   label_visibility="collapsed", height=140,
                                   placeholder="From Mom: You make us proud every day.\nFrom Dev: Happy birthday, superstar!")

        if st.form_submit_button("Save words", type="primary"):
            for media_id, caption in captions.items():
                service.db.update_caption(media_id, caption.strip())
            project.details.quotes = [quote.strip()] if quote.strip() else []
            project.details.wishes = [w.strip() for w in wishes_text.splitlines() if w.strip()]
            service.db.save_project(project)
            st.success("Saved. Your words will appear across the film and the book.")


# --------------------------------------------------------------- step 4 ---
def _step_style(service: ProjectService, project: Project) -> None:
    st.subheader("Choose your visual theme")
    st.caption("The theme drives fonts, colours, transitions and motion across every output.")

    names = list(THEMES)
    current = names.index(project.theme) if project.theme in names else 0
    chosen = st.radio("Theme", names, index=current, horizontal=True,
                      label_visibility="collapsed")

    theme = THEMES[chosen]
    sw1, sw2, sw3, sw4 = st.columns(4)
    for col, (label, rgb) in zip(
            (sw1, sw2, sw3, sw4),
            [("Background", theme.background), ("Primary", theme.primary),
             ("Accent", theme.accent), ("Text", theme.text)]):
        col.color_picker(label, theme.hex(rgb), disabled=True)
    st.caption(f"Motion: **{theme.transition}** transitions · "
               f"Ken Burns {'on' if theme.ken_burns else 'off'} · "
               f"Frame style: {theme.frame_style}")

    if st.button("Apply theme", type="primary"):
        project.theme = chosen
        service.db.save_project(project)
        st.success(f"Theme **{chosen}** applied. Ready to generate!")


# --------------------------------------------------------------- step 5 ---
def _step_generate(service: ProjectService, project: Project) -> None:
    st.subheader("🎬 Generate your memory")
    photos = service.db.get_media(project.id, "photo")
    if not photos:
        st.warning("No photos yet - add some in **Step 2** first.")
        return

    st.markdown(f"**{project.name}** · {len(photos)} photos · "
                f"theme *{project.theme}* · event *{project.event_type}*")

    quality = st.radio("Video quality", ["Draft preview (fast, 480p)", "Full quality (1080p)"],
                       horizontal=True)
    draft = quality.startswith("Draft")

    col_v, col_p, col_c = st.columns(3)

    if col_v.button("🎞️ Generate film", type="primary", width='stretch'):
        bar = st.progress(0.0, text="Warming up the studio…")
        try:
            out = service.generate_video(
                project, draft=draft,
                progress=lambda p, m: bar.progress(min(p, 1.0), text=m))
            st.success("Your film is ready! 🎉")
            st.video(str(out))
            st.download_button("⬇️ Download film", Path(out).read_bytes(),
                               file_name=Path(out).name, mime="video/mp4")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Something went wrong while rendering: {exc}")

    if col_p.button("📖 Generate PDF book", width='stretch'):
        with st.spinner("Laying out your memory book…"):
            try:
                out = service.generate_pdf(project)
                st.success("Memory book ready!")
                st.download_button("⬇️ Download PDF", Path(out).read_bytes(),
                                   file_name=Path(out).name, mime="application/pdf")
            except Exception as exc:
                st.error(f"Could not build the PDF: {exc}")

    if col_c.button("🖼️ Generate collage", width='stretch'):
        with st.spinner("Arranging the mosaic…"):
            out = service.generate_collage(project)
            if out:
                st.success("Collage ready!")
                st.image(str(out), width='stretch')
                st.download_button("⬇️ Download collage", Path(out).read_bytes(),
                                   file_name=Path(out).name, mime="image/jpeg")
            else:
                st.error("No usable photos for a collage.")

    st.divider()
    col_t, col_q = st.columns(2)
    with col_t:
        st.markdown("**🗓️ Interactive timeline**")
        if st.button("Build timeline", width='stretch'):
            fig, html_path = service.generate_timeline(project)
            if fig is None:
                st.info("No photos carried a capture date, so there is nothing to plot yet.")
            else:
                st.plotly_chart(fig, width='stretch')
                st.download_button("⬇️ Download timeline (HTML)",
                                   Path(html_path).read_bytes(),
                                   file_name=Path(html_path).name, mime="text/html")
    with col_q:
        st.markdown("**🔗 QR share card**")
        link = st.text_input("Where will the video live?",
                             placeholder="https://youtu.be/… or a Drive link")
        if st.button("Create QR card", width='stretch'):
            if not link.strip():
                st.warning("Paste the link the QR code should open.")
            else:
                out = service.generate_qr(project, link.strip())
                st.image(str(out), width=320)
                st.download_button("⬇️ Download QR card", Path(out).read_bytes(),
                                   file_name=Path(out).name, mime="image/png")
