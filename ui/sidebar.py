"""Persistent channel and video navigation for every Streamlit page."""

import html
from typing import Any, MutableMapping, Optional

from state.common_state import (
    get_selected_video_id,
    init_common_state,
    reset_video_cache,
)
from ui.pagination import render_page_size_control, render_pagination
from ui.video_list import render_video_list


def _render_channel_details(channel) -> None:
    import streamlit as st

    if channel.thumbnail_url:
        st.markdown(
            '<img class="channel-logo" src="{}" alt="Channel logo" />'.format(
                html.escape(channel.thumbnail_url, quote=True)
            ),
            unsafe_allow_html=True,
        )
    st.caption("Your channel")
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


def render_app_sidebar(
    context: Any,
    session_state: MutableMapping[str, Any],
    query_params: MutableMapping[str, str],
) -> Optional[str]:
    """Render shared channel controls and return the common selected video ID."""
    import streamlit as st

    init_common_state(session_state)
    with st.sidebar:
        with st.container(border=True):
            _render_channel_details(context.channel)
            if st.button("Refresh list", key="common-refresh-list"):
                _refresh_sidebar(session_state)

        render_page_size_control(context.selection, query_params)
        render_pagination(
            context.selection, context.channel.total_videos, query_params
        )
        render_video_list(context.page.videos, session_state)

    return get_selected_video_id(session_state)
