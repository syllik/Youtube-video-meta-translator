"""Unified YouTube localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.localization_service import LocalizationService
from state.common_state import reset_video_cache
from state.llm_state import clear_llm_prompt, init_llm_state, sync_llm_video
from state.translation_state import init_translation_state, sync_translation_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_feedback
from ui.llm_package import render_llm_translation_controls
from ui.source_selection import render_source_selection
from ui.translation_review import render_preview_publish


def render_translate_page() -> None:
    configure_page("Translate")
    st.title("Translate")
    st.caption(
        "Generate missing translations with Codex or upload external-LLM JSON, then preview and publish safely."
    )
    context = bootstrap_app_context()
    if context is None:
        return

    translation_state = init_translation_state(st.session_state)
    prompt_state = init_llm_state(st.session_state)
    sync_translation_video(translation_state, context.selected_video_id)
    sync_llm_video(prompt_state, context.selected_video_id)
    if not context.selected_video_id:
        st.info("Select one video from the sidebar to begin.")
        return

    try:
        with st.spinner("Loading selected video and metadata language catalog..."):
            catalog = context.metadata_language_catalog
            video_resource = context.service.get_video_with_localizations(
                context.selected_video_id
            )
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
        return
    except Exception:
        render_feedback("", "youtube_api")
        return

    source_codes = render_source_selection(st.session_state, video_resource, catalog)
    service = LocalizationService(context.service, catalog.codes)
    with st.expander("Generate translations", expanded=True):
        render_llm_translation_controls(
            translation_state,
            video_resource,
            catalog,
            widget_prefix="translate",
            prompt_state=prompt_state,
            source_codes=source_codes,
        )

    def refresh_after_publish() -> None:
        reset_video_cache(st.session_state)
        clear_llm_prompt(prompt_state)
        st.rerun()

    render_preview_publish(
        translation_state,
        context.selected_video_id,
        service,
        catalog.codes,
        widget_prefix="translate",
        on_published=refresh_after_publish,
    )


render_translate_page()
