"""Shared channel identity header."""

from typing import Callable

from models import ChannelInfo


def render_channel_header(channel: ChannelInfo, on_refresh: Callable[[], None]) -> None:
    import streamlit as st

    with st.container(border=True):
        image_col, info_col, action_col = st.columns((1, 5, 1))
        with image_col:
            if channel.thumbnail_url:
                st.image(channel.thumbnail_url, width=72)
        with info_col:
            st.caption("Your channel")
            st.subheader(channel.name or "YouTube channel")
            st.caption("Total videos: {}".format(channel.total_videos))
        with action_col:
            if st.button("Refresh list", key="common-refresh-list"):
                on_refresh()
