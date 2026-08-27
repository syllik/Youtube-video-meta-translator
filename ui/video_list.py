"""Shared video list with mode-specific selection widgets."""

import html
from dataclasses import dataclass
from typing import Any, MutableMapping, Optional, Sequence, Tuple

from models import VideoSummary
from state.manual_state import set_manual_video


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    selected_video_ids: Tuple[str, ...] = ()
    selected_manual_video_id: Optional[str] = None


def widget_key(mode: str, video_id: str) -> str:
    if mode not in {"machine", "manual"}:
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
                '<div class="video-id">ID: {}</div>'.format(html.escape(video.id)),
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
    machine_state: MutableMapping[str, Any],
    manual_state: MutableMapping[str, Any],
) -> SelectionResult:
    """Render the same rows while isolating machine/manual selectors."""
    import streamlit as st

    if mode == "machine":
        selected = set(machine_state.setdefault("selected_video_ids", set()))
        if st.button("Select all visible", key="machine-select-all-visible"):
            selected.update(video.id for video in videos)
            machine_state["selected_video_ids"] = selected
            st.rerun()
        if selected and st.button("Clear visible selection", key="machine-clear-visible"):
            selected.difference_update(video.id for video in videos)
            machine_state["selected_video_ids"] = selected
            st.rerun()

        st.caption("{} video(s) selected".format(len(selected)))
        for video in videos:
            row_col, details_col = st.columns((1, 7))
            with row_col:
                checked = st.checkbox(
                    "Select",
                    value=video.id in selected,
                    key=widget_key("machine", video.id),
                    label_visibility="collapsed",
                )
                if checked:
                    selected.add(video.id)
                else:
                    selected.discard(video.id)
            with details_col:
                _render_video_details(video)
        machine_state["selected_video_ids"] = selected
        return SelectionResult("machine", tuple(sorted(selected)))

    if mode == "manual":
        video_by_id = {video.id: video for video in videos}
        selected_id = manual_state.get("selected_video_id")
        options = [video.id for video in videos]
        if selected_id not in video_by_id:
            selected_id = options[0] if options else None
        if options:
            selected_id = st.radio(
                "Select one video to edit",
                options,
                index=options.index(selected_id) if selected_id in options else 0,
                format_func=lambda video_id: video_by_id[video_id].title,
                key="manual-video-radio",
            )
        set_manual_video(manual_state, selected_id)
        for video in videos:
            _render_video_details(video)
        return SelectionResult("manual", selected_manual_video_id=selected_id)

    raise ValueError("Unknown video-list mode: {}".format(mode))
