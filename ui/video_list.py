"""Workflow-agnostic video cards for the shared application sidebar."""

import html
from typing import Any, MutableMapping, Sequence

from models import VideoSummary
from state.common_state import (
    get_selected_video_id,
    init_common_state,
    set_selected_video_id,
)
from ui.badges import render_language_badges


def widget_key(video_id: str) -> str:
    return "common-video-{}".format(video_id)


def _description(text: str, max_length: int = 220) -> str:
    compact = text or ""
    return compact if len(compact) <= max_length else compact[:max_length].rstrip() + "…"


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


def _render_video_details(video: VideoSummary) -> None:
    import streamlit as st

    _render_thumbnail(video)
    st.markdown(
        '<div class="video-title">{}</div>'.format(html.escape(video.title)),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-description">{}</div>'.format(
            html.escape(_description(video.description))
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-id">ID: {}</div>'.format(html.escape(video.id)),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="video-default-language">Default language: {}</div>'.format(
            html.escape(video.default_language_code or "Not set")
        ),
        unsafe_allow_html=True,
    )
    if video.current_language_codes:
        render_language_badges(video.current_language_codes, label="Localizations")
    else:
        st.caption("No localizations")


def render_video_list(
    videos: Sequence[VideoSummary], session_state: MutableMapping[str, Any]
):
    """Render cards that read and write only the common video selection."""
    import streamlit as st

    init_common_state(session_state)
    selected_id = get_selected_video_id(session_state)
    for video in videos:
        with st.container(border=True):
            details_col, action_col = st.columns((5, 1))
            with details_col:
                _render_video_details(video)
            with action_col:
                is_selected = selected_id == video.id
                if st.button(
                    "Selected" if is_selected else "Select",
                    type="primary" if is_selected else "secondary",
                    disabled=is_selected,
                    key=widget_key(video.id),
                ):
                    set_selected_video_id(session_state, video.id)
                    st.rerun()
    return get_selected_video_id(session_state)
