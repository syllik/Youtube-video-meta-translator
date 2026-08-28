"""Prompt-only localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.llm_state import clear_llm_prompt, init_llm_state
from streamlit_app import render_common_page_context
from ui.feedback import render_feedback
from ui.llm_package import render_llm_translation_controls
from ui.manual_editor import render_manual_editor
from ui.pagination import render_pagination
from ui.video_list import render_video_list


def render_llm_page() -> None:
    context = render_common_page_context("llm")
    if context is None:
        return

    state = init_llm_state(st.session_state)
    videos_by_id = {candidate.id: candidate for candidate in context.page.videos}
    selected_video_id = state.get("selected_video_id")
    if selected_video_id is None:
        st.info("Select one video to begin.")
    elif selected_video_id not in videos_by_id:
        st.info(
            "The selected video is on another page. Select a video here to switch."
        )

    selection = render_video_list(context.page.videos, "llm", state)
    selected_video_id = selection.selected_video_id
    if selected_video_id is not None and selected_video_id in videos_by_id:
        video = videos_by_id[selected_video_id]
        try:
            catalog = context.service.fetch_localization_language_catalog(hl="ru")
            video_resource = context.service.get_video_with_localizations(video.id)
        except HttpError as error:
            details = getattr(error, "error_details", None) or []
            reason = (
                details[0].get("reason")
                if details and isinstance(details[0], dict)
                else ""
            )
            render_feedback(
                "",
                "quota_exceeded" if reason == "quotaExceeded" else "youtube_api",
            )
        except Exception:
            render_feedback("", "youtube_api")
        else:
            render_llm_translation_controls(
                state, video_resource, catalog, widget_prefix="llm"
            )
            service = ManualLocalizationService(context.service, catalog.codes)

            def refresh_after_publish() -> None:
                clear_llm_prompt(state)
                st.rerun()

            render_manual_editor(
                state,
                video,
                service,
                catalog.codes,
                widget_prefix="llm",
                on_published=refresh_after_publish,
            )
    render_pagination(context.selection, context.channel.total_videos, st.query_params)


render_llm_page()
