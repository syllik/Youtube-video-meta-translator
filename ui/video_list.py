"""Workflow-agnostic video cards for the shared application sidebar."""

import html
from typing import Any, Iterable, MutableMapping, Sequence, Tuple

from models import VideoSummary
from state.common_state import (
    get_selected_video_id,
    init_common_state,
    set_selected_video_id,
)


def widget_key(video_id: str) -> str:
    return "common-video-{}".format(video_id)


def video_localization_counts(
    video: VideoSummary, supported_language_codes: Iterable[str]
) -> Tuple[int, int]:
    """Count known existing and missing non-default metadata localizations."""
    default_code = (
        video.default_language_code.casefold()
        if isinstance(video.default_language_code, str)
        else None
    )
    existing = {
        code.casefold()
        for code in video.current_language_codes
        if isinstance(code, str) and code.casefold() != default_code
    }
    live_codes = {
        code.casefold()
        for code in supported_language_codes
        if isinstance(code, str) and code.strip()
    }
    if default_code is not None:
        live_codes.discard(default_code)
    return len(existing & live_codes), len(live_codes - existing)


def _render_thumbnail(video: VideoSummary) -> None:
    import streamlit as st

    if not video.thumbnail_url:
        return
    st.markdown(
        '<a class="video-thumbnail-link" href="https://www.youtube.com/watch?v={id}" '
        'target="_blank" rel="noopener noreferrer" aria-label="Open video on YouTube">'
        '<img src="{thumbnail}" alt="{title}" />'
        '<span class="video-external-link" aria-hidden="true">'
        '<svg viewBox="0 0 24 24" focusable="false"><path d="M14 4h6v6m-1-5-8 8"/>'
        '<path d="M19 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h5"/></svg>'
        '</span></a>'.format(
            id=html.escape(video.id, quote=True),
            thumbnail=html.escape(video.thumbnail_url, quote=True),
            title=html.escape(video.title, quote=True),
        ),
        unsafe_allow_html=True,
    )


def _render_reset_control(
    video: VideoSummary, session_state: MutableMapping[str, Any]
) -> None:
    from ui.reset_control import render_reset_button, reset_widget_key

    warning = (
        "Reset all YouTube localizations for {title} ({video_id})? "
        "All translations will be deleted. Only the default title, description, "
        "and language will remain. Save any translations you need before resetting."
    ).format(title=video.title or "this video", video_id=video.id)
    event_id = render_reset_button(
        video.id,
        warning,
        key=reset_widget_key(video.id),
    )
    if event_id and session_state.get("common.last_reset_event") != (
        video.id,
        event_id,
    ):
        session_state["common.last_reset_event"] = (video.id, event_id)
        session_state["common.pending_reset_video_id"] = video.id


def _render_video_details(
    video: VideoSummary, supported_language_codes: Iterable[str]
) -> None:
    import streamlit as st

    _render_thumbnail(video)
    st.markdown(
        '<div class="video-title">{}</div>'.format(html.escape(video.title)),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-default-language">Default language: {}</div>'.format(
            html.escape(video.default_language_code or "Not set")
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-localizations">Localizations: {} / {}</div>'.format(
            *video_localization_counts(video, supported_language_codes)
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-id">Video ID: {}</div>'.format(html.escape(video.id)),
        unsafe_allow_html=True,
    )


def render_video_list(
    videos: Sequence[VideoSummary],
    session_state: MutableMapping[str, Any],
    supported_language_codes: Iterable[str] = (),
):
    """Render cards that read and write only the common video selection."""
    import streamlit as st

    init_common_state(session_state)
    selected_id = get_selected_video_id(session_state)
    for video in videos:
        is_selected = selected_id == video.id
        with st.container(border=is_selected):
            _render_video_details(video, supported_language_codes)
            if st.button(
                "Selected" if is_selected else "Select",
                type="primary" if is_selected else "secondary",
                disabled=is_selected,
                use_container_width=True,
                key=widget_key(video.id),
            ):
                set_selected_video_id(session_state, video.id)
                st.rerun()
            _render_reset_control(video, session_state)
    return get_selected_video_id(session_state)
