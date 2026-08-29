"""Streamlit entry point and shared page bootstrap."""

from dataclasses import dataclass
from typing import Any, MutableMapping, Optional

import streamlit as st


PAGE_TITLES = {
    "translate": "Translate",
    "prompt": "LLM Translation prompt",
    "faq": "FAQ",
}

PAGE_DESCRIPTIONS = {
    "translate": "Generate or upload translations, preview the changes, and publish them safely.",
    "prompt": "Prepare a source-aware prompt for an external LLM when local Codex is unavailable.",
    "faq": "Answers to common questions about the YouTube localization workflow.",
}


@dataclass(frozen=True)
class AppContext:
    """Shared YouTube data and selection available to every workflow page."""

    service: Any
    channel: Any
    page: Any
    selection: Any
    selected_video_id: Optional[str]
    metadata_language_catalog: Any


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


def bootstrap_app_context() -> Optional[AppContext]:
    """Load shared YouTube data, render the sidebar, and return app context."""
    from googleapiclient.errors import HttpError

    from models import YouTubePage
    from state.common_state import (
        clamp_selection,
        get_selected_video_id,
        init_common_state,
        load_video_page,
        reset_video_cache,
    )
    from ui.feedback import render_feedback
    from ui.pagination import (
        canonical_pagination_query,
        parse_pagination_query,
    )
    from ui.sidebar import render_app_sidebar
    from ui.styles import apply_app_styles

    apply_app_styles()
    init_common_state(st.session_state)
    query = parse_pagination_query(st.query_params)
    service = None
    try:
        with st.spinner(
            "Loading YouTube channel, videos, and metadata language catalog..."
        ):
            service = get_youtube_service(st.session_state)
            channel = st.session_state.get("common.channel")
            if channel is None:
                channel = service.fetch_channel()
                st.session_state["common.channel"] = channel
            normalized = clamp_selection(query, channel.total_videos)
            previous_limit = st.session_state.get("common.active_limit")
            if previous_limit is not None and previous_limit != normalized.limit:
                reset_video_cache(st.session_state)
            st.session_state["common.active_limit"] = normalized.limit
            if canonical_pagination_query(normalized) != {
                "page": str(st.query_params.get("page", "")),
                "limit": str(st.query_params.get("limit", "")),
            }:
                st.query_params.update(canonical_pagination_query(normalized))
                st.rerun()
            catalog = service.fetch_metadata_language_catalog()
            page = (
                YouTubePage(videos=(), next_page_token=None)
                if channel.total_videos <= 0
                else load_video_page(service, st.session_state, normalized)
            )
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

    context = AppContext(
        service=service,
        channel=channel,
        page=page,
        selection=normalized,
        selected_video_id=get_selected_video_id(st.session_state),
        metadata_language_catalog=catalog,
    )
    render_app_sidebar(context, st.session_state, st.query_params)
    return AppContext(
        service=service,
        channel=channel,
        page=page,
        selection=normalized,
        selected_video_id=get_selected_video_id(st.session_state),
        metadata_language_catalog=catalog,
    )


def render_app_intro() -> None:
    """Render the small root page; workflow controls live on the two pages."""
    configure_page()
    st.title("YouTube Metadata Translator")
    st.write("Use Translate for the complete localization workflow.")
    st.page_link("pages/1_Translate.py", label="Translate")
    st.page_link("pages/2_LLM_prompt.py", label="LLM Translation prompt")
    st.page_link("pages/3_FAQ.py", label="FAQ")


if __name__ == "__main__":
    render_app_intro()
