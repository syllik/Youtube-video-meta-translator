"""Shared video list for the Manual and LLM workflows."""

import html
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping, Optional, Sequence, Tuple

from models import VideoSummary


MACHINE_SELECT_ALL_CHANNEL_KEY = "machine-select-all-channel"
MACHINE_SELECT_ALL_ROW_CHANGE_KEY = "machine-select-all-row-change"


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    selected_video_ids: Tuple[str, ...] = ()
    selected_manual_video_id: Optional[str] = None
    selected_video_id: Optional[str] = None


def widget_key(mode: str, video_id: str) -> str:
    if mode not in {"machine", "manual", "llm"}:
        raise ValueError("Unknown video-list mode: {}".format(mode))
    return "{}-video-{}".format(mode, video_id)


def sync_visible_checkbox_state(
    widget_state: MutableMapping[str, Any],
    video_ids: Sequence[str],
    selected_video_ids,
) -> None:
    """Synchronize rendered checkbox values after a bulk selection action."""
    selected = set(selected_video_ids)
    for video_id in video_ids:
        widget_state[widget_key("machine", video_id)] = video_id in selected


def clear_channel_select_all_widget() -> None:
    """Stop channel-wide selection when a user changes one video row."""
    import streamlit as st

    st.session_state[MACHINE_SELECT_ALL_CHANNEL_KEY] = False
    st.session_state[MACHINE_SELECT_ALL_ROW_CHANGE_KEY] = True


def checkbox_widget_kwargs(
    widget_state: Mapping[str, Any], video_id: str, selected_video_ids
):
    """Build checkbox arguments without conflicting with existing widget state."""
    return stateful_checkbox_kwargs(
        widget_state,
        widget_key("machine", video_id),
        "Select video",
        video_id in set(selected_video_ids),
    )


def stateful_checkbox_kwargs(
    widget_state: Mapping[str, Any], key: str, label: str, default: bool
):
    """Build checkbox arguments while respecting an existing widget value."""
    kwargs = {"label": label, "key": key}
    if key not in widget_state:
        kwargs["value"] = default
    return kwargs


def visible_selected_video_ids(video_ids: Sequence[str], selected_video_ids):
    """Return only selected IDs represented by the current visible page."""
    return set(video_ids).intersection(selected_video_ids)


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
    """Render Machine, Manual, and LLM cards with compatible state inputs."""
    import streamlit as st

    if mode == "machine":
        selected = set(workflow_state.setdefault("selected_video_ids", set()))
        visible_ids = tuple(video.id for video in videos)
        if st.button("Select all visible", key="machine-select-all-visible"):
            selected.update(visible_ids)
            workflow_state["selected_video_ids"] = selected
            sync_visible_checkbox_state(st.session_state, visible_ids, selected)
            st.rerun()
        if st.button(
            "Clear all visible",
            disabled=not visible_selected_video_ids(visible_ids, selected),
            key="machine-clear-visible",
        ):
            selected.difference_update(visible_ids)
            workflow_state["selected_video_ids"] = selected
            workflow_state["select_all_channel"] = False
            workflow_state["select_all_channel_reset_pending"] = True
            sync_visible_checkbox_state(st.session_state, visible_ids, selected)
            st.rerun()

        st.caption("{} video(s) selected".format(len(selected)))
        for video in videos:
            row_col, details_col = st.columns((1, 7))
            with row_col:
                checkbox_kwargs = checkbox_widget_kwargs(
                    st.session_state, video.id, selected
                )
                if workflow_state.get("select_all_channel"):
                    checkbox_kwargs["on_change"] = clear_channel_select_all_widget
                checked = st.checkbox(**checkbox_kwargs)
                if checked:
                    selected.add(video.id)
                else:
                    selected.discard(video.id)
            with details_col:
                _render_video_details(video)
        workflow_state["selected_video_ids"] = selected
        return SelectionResult("machine", tuple(sorted(selected)))

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
