"""Persistent channel and video navigation for every Streamlit page."""

import html
from typing import Any, MutableMapping, Optional

from state.common_state import (
    can_load_more,
    clear_source_selection,
    get_selected_video_id,
    init_common_state,
    load_more_video_page,
    reset_video_cache,
)
from state.llm_state import clear_llm_prompt
from state.translation_state import clear_translation_draft
from services.localization_service import LocalizationService
from services.youtube_service import YoutubeResetError
from ui.pagination import render_page_size_control, render_pagination
from ui.video_list import render_video_list


def _render_channel_details(channel) -> None:
    import streamlit as st

    st.subheader(channel.name or "YouTube channel")
    if channel.description:
        st.markdown(
            '<div class="channel-description">{}</div>'.format(
                html.escape(channel.description)
            ),
            unsafe_allow_html=True,
        )
    st.caption("Channel ID: {}".format(channel.id or "Not available"))
    st.caption("Total videos: {}".format(channel.total_videos))
    if channel.id:
        channel_url = "https://www.youtube.com/channel/{}".format(channel.id)
        rss_url = "https://www.youtube.com/feeds/videos.xml?channel_id={}".format(
            channel.id
        )
        st.markdown(
            '<a href="{channel_url}" target="_blank" rel="noopener noreferrer">'
            "YouTube ↗</a> · "
            '<a href="{rss_url}" target="_blank" rel="noopener noreferrer">RSS ↗</a>'.format(
                channel_url=html.escape(channel_url, quote=True),
                rss_url=html.escape(rss_url, quote=True),
            ),
            unsafe_allow_html=True,
        )


def _refresh_sidebar(session_state: MutableMapping[str, Any]) -> None:
    import streamlit as st

    reset_video_cache(session_state)
    session_state["common.channel"] = None
    session_state["common.active_limit"] = None
    st.rerun()


def _catalog_codes(context: Any):
    catalog = getattr(context, "language_catalog", None)
    return tuple(getattr(catalog, "codes", ()) or ())


def _render_pending_feedback(session_state) -> None:
    import streamlit as st

    feedback = session_state.pop("common.pending_sidebar_feedback", None)
    if not feedback:
        return
    level, message = feedback
    getattr(st, level)(message)


def _consume_pending_reset(context, session_state) -> bool:
    import streamlit as st

    video_id = session_state.pop("common.pending_reset_video_id", None)
    if not video_id:
        return False
    visible_videos = {video.id: video for video in context.page.videos}
    video = visible_videos.get(video_id)
    if video is None:
        st.error("The selected video is not available. Refresh the video list and try again.")
        return True

    if session_state.get("common.video_operation_status") == "resetting":
        return True
    session_state["common.video_operation_status"] = "resetting"
    try:
        catalog_codes = _catalog_codes(context)
        reset_service = LocalizationService(context.service, catalog_codes)
        with st.spinner("Resetting YouTube localizations..."):
            reset_service.reset(video_id)
        reset_video_cache(session_state)
        clear_source_selection(session_state, video_id)
        translation_state = session_state.get("translation")
        if (
            isinstance(translation_state, dict)
            and translation_state.get("bound_video_id") == video_id
        ):
            clear_translation_draft(translation_state)
        prompt_state = session_state.get("llm")
        if (
            isinstance(prompt_state, dict)
            and prompt_state.get("bound_video_id") == video_id
        ):
            clear_llm_prompt(prompt_state)
        session_state["common.pending_sidebar_feedback"] = (
            "success",
            "All YouTube localizations were reset for '{}'.".format(
                video.title or video.id
            ),
        )
        session_state["common.video_operation_status"] = "idle"
        st.rerun()
    except YoutubeResetError as error:
        session_state["common.video_operation_status"] = "idle"
        st.error(str(error))
    except Exception:
        session_state["common.video_operation_status"] = "idle"
        st.error("YouTube could not reset this video's localizations. Try again.")
    return True


def _render_load_more(context, session_state) -> None:
    import streamlit as st

    selection = context.selection
    if not can_load_more(session_state, selection, context.channel.total_videos):
        return
    if st.button(
        "Load more",
        key="common-load-more",
        use_container_width=True,
        disabled=session_state.get("common.video_operation_status") != "idle",
    ):
        session_state["common.video_operation_status"] = "loading_more"
        try:
            with st.spinner("Loading more videos..."):
                load_more_video_page(context.service, session_state, selection)
            session_state["common.video_operation_status"] = "idle"
            st.rerun()
        except Exception:
            session_state["common.video_operation_status"] = "idle"
            st.error("YouTube could not load more videos. Try again.")


def render_app_sidebar(
    context: Any,
    session_state: MutableMapping[str, Any],
    query_params: MutableMapping[str, str],
) -> Optional[str]:
    """Render shared channel controls and return the common selected video ID."""
    import streamlit as st

    init_common_state(session_state)
    _render_pending_feedback(session_state)
    with st.sidebar:
        with st.container(border=False):
            _render_channel_details(context.channel)
            if st.button("Refresh video list",use_container_width=True, key="common-refresh-list"):
                _refresh_sidebar(session_state)

        render_page_size_control(context.selection, query_params)
        render_pagination(
            context.selection,
            context.channel.total_videos,
            query_params,
            visible_count=len(context.page.videos),
        )
        render_video_list(
            context.page.videos,
            session_state,
            supported_language_codes=_catalog_codes(context),
        )
        if _consume_pending_reset(context, session_state):
            return get_selected_video_id(session_state)
        _render_load_more(context, session_state)

    return get_selected_video_id(session_state)
