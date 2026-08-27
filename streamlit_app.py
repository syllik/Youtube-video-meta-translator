"""Streamlit entry point and shared page bootstrap."""

import os
from typing import Any, MutableMapping

import streamlit as st
from dotenv import load_dotenv


PAGE_TITLES = {
    "machine": "Machine translate",
    "manual": "Manual translate",
}


def page_title(mode: str) -> str:
    """Return the user-facing title for a supported workflow."""
    try:
        return PAGE_TITLES[mode]
    except KeyError:
        raise ValueError("Unknown application mode: {}".format(mode)) from None


def configure_page(title: str = "YouTube Metadata Translator") -> None:
    """Configure the shared Streamlit page shell."""
    st.set_page_config(
        page_title=title,
        page_icon="▶",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def get_youtube_service(session_state: MutableMapping[str, Any]):
    """Create the YouTube service only when a page first needs it."""
    service = session_state.get("common.youtube_service")
    if service is None:
        from services.youtube_service import YoutubeService

        service = YoutubeService()
        session_state["common.youtube_service"] = service
    return service


def render_common_page_context(mode: str):
    """Load channel and one URL-selected page for either workflow."""
    from dataclasses import dataclass

    from googleapiclient.errors import HttpError

    from state.common_state import clamp_selection, init_common_state, load_video_page
    from ui.channel_header import render_channel_header
    from ui.feedback import render_feedback
    from ui.pagination import (
        canonical_pagination_query,
        parse_pagination_query,
    )
    from ui.styles import apply_app_styles

    if mode not in {"machine", "manual"}:
        raise ValueError("Unknown application mode: {}".format(mode))
    configure_page(page_title(mode))
    apply_app_styles()
    init_common_state(st.session_state)
    query = parse_pagination_query(st.query_params)
    service = None
    try:
        service = get_youtube_service(st.session_state)
        channel = st.session_state.get("common.channel")
        if channel is None:
            channel = service.fetch_channel()
            st.session_state["common.channel"] = channel
        normalized = clamp_selection(query, channel.total_videos)
        if canonical_pagination_query(normalized) != {
            "page": str(st.query_params.get("page", "")),
            "limit": str(st.query_params.get("limit", "")),
        }:
            st.query_params.update(canonical_pagination_query(normalized))
            st.rerun()
        page = load_video_page(service, st.session_state, normalized)
    except HttpError as error:
        reason = ""
        details = getattr(error, "error_details", None) or []
        if details and isinstance(details[0], dict):
            reason = details[0].get("reason", "")
        if reason == "quotaExceeded":
            render_feedback("", "quota_exceeded")
        else:
            render_feedback("", "youtube_api")
        return None
    except Exception:
        render_feedback("", "youtube_api")
        return None

    @dataclass(frozen=True)
    class CommonPageContext:
        service: Any
        channel: Any
        page: Any
        selection: Any

    def refresh():
        from state.common_state import reset_video_cache

        reset_video_cache(st.session_state)
        st.session_state["common.channel"] = None
        st.rerun()

    render_channel_header(channel, refresh)
    return CommonPageContext(service, channel, page, normalized)


def render_app_intro() -> None:
    """Render the small root page; workflow controls live on the two pages."""
    configure_page()
    st.title("YouTube Metadata Translator")
    st.write("Choose a workflow from the navigation panel.")
    st.page_link("pages/1_Machine_translate.py", label="Machine translate")
    st.page_link("pages/2_Manual_translate.py", label="Manual translate")


if __name__ == "__main__":
    render_app_intro()
