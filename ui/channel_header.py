"""Shared channel identity header and page-size control."""

import html
from typing import Callable, MutableMapping

from models import ChannelInfo
from ui.pagination import PaginationSelection, render_page_size_control


CHANNEL_LOGO_SIZE = 128


def render_channel_header(
    channel: ChannelInfo,
    on_refresh: Callable[[], None],
    selection: PaginationSelection,
    query_params: MutableMapping[str, str],
) -> None:
    import streamlit as st

    with st.container(border=True):
        image_col, info_col, action_col = st.columns((1, 5, 2))
        with image_col:
            if channel.thumbnail_url:
                st.markdown(
                    '<img class="channel-logo" src="{url}" alt="Channel logo" '
                    'style="width: 100%; max-width: {size}px; height: auto; '
                    'aspect-ratio: 1 / 1; object-fit: cover;" />'.format(
                        url=html.escape(channel.thumbnail_url, quote=True),
                        size=CHANNEL_LOGO_SIZE,
                    ),
                    unsafe_allow_html=True,
                )
        with info_col:
            st.caption("Your channel")
            st.subheader(channel.name or "YouTube channel")
            st.caption("Total videos: {}".format(channel.total_videos))
        with action_col:
            if st.button("Refresh list", key="common-refresh-list"):
                on_refresh()
            render_page_size_control(selection, query_params)
