"""Shared video list for the Manual and LLM workflows."""

import html
from dataclasses import dataclass
from typing import Any, MutableMapping, Optional, Sequence, Tuple

from models import VideoSummary


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    selected_video_ids: Tuple[str, ...] = ()
    selected_manual_video_id: Optional[str] = None
    selected_video_id: Optional[str] = None


def widget_key(mode: str, video_id: str) -> str:
    if mode not in {"manual", "llm"}:
        raise ValueError("Unknown video-list mode: {}".format(mode))
    return "{}-video-{}".format(mode, video_id)


def _description(text: str, max_length: int = 220) -> str:
    compact = text or ""
    return compact if len(compact) <= max_length else compact[:max_length].rstrip() + "…"


def _render_video_details(video: VideoSummary) -> None:
    import streamlit as st

    with st.container():
        image_col, content_col = st.columns((1, 5))
        with image_col:
            if video.thumbnail_url:
                st.image(video.thumbnail_url, width=140)
        with content_col:
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
                '<div class="video-id">ID: {} · '
                '<a href="https://www.youtube.com/watch?v={}" target="_blank" '
                'rel="noopener noreferrer">Open on YouTube</a></div>'.format(
                    html.escape(video.id),
                    html.escape(video.id, quote=True),
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="video-default-language">Default language: {}</div>'.format(
                    html.escape(video.default_language_code or "Not set")
                ),
                unsafe_allow_html=True,
            )
            if video.current_language_codes:
                badges = " ".join(
                    '<span class="localization-badge">{}</span>'.format(html.escape(code))
                    for code in video.current_language_codes
                )
                st.markdown("Localizations: {}".format(badges), unsafe_allow_html=True)
            else:
                st.caption("No localizations")


def render_video_list(
    videos: Sequence[VideoSummary],
    mode: str,
    workflow_state: MutableMapping[str, Any],
    manual_state: Optional[MutableMapping[str, Any]] = None,
) -> SelectionResult:
    """Render Manual and LLM cards with isolated workflow state."""
    import streamlit as st

    if mode == "manual":
        from state.manual_state import set_manual_video

        set_video = set_manual_video
        selected_state = manual_state if manual_state is not None else workflow_state
    elif mode == "llm":
        from state.llm_state import set_llm_video

        set_video = set_llm_video
        selected_state = workflow_state

    if mode in {"manual", "llm"}:
        selected_id = selected_state.get("selected_video_id")
        for video in videos:
            details_col, action_col = st.columns((7, 1))
            with details_col:
                _render_video_details(video)
            with action_col:
                is_selected = selected_id == video.id
                if st.button(
                    "Selected" if is_selected else "Select",
                    type="primary" if is_selected else "secondary",
                    disabled=is_selected,
                    key=widget_key(mode, video.id),
                ):
                    set_video(selected_state, video.id)
                    st.rerun()
        return SelectionResult(
            mode,
            selected_manual_video_id=selected_id if mode == "manual" else None,
            selected_video_id=selected_id,
        )

    raise ValueError("Unknown video-list mode: {}".format(mode))
