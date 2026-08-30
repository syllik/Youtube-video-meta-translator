"""Unified YouTube localization workflow page."""

from typing import Mapping

import streamlit as st

from services.localization_service import LocalizationService
from state.common_state import (
    get_selected_video_resource,
    reset_video_cache,
    update_selected_video_resource,
)
from state.llm_state import clear_llm_prompt, init_llm_state, sync_llm_video
from state.translation_state import init_translation_state, sync_translation_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_service_error
from ui.llm_package import render_llm_translation_controls
from ui.source_selection import render_source_selection
from ui.target_selection import render_target_selection
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
            video_resource = get_selected_video_resource(
                context.service, st.session_state, context.selected_video_id
            )
    except Exception as error:
        render_service_error(error)
        return

    source_codes = render_source_selection(st.session_state, video_resource, catalog)
    target_codes = render_target_selection(
        st.session_state, video_resource, catalog, source_codes=source_codes
    )
    service = LocalizationService(context.service, catalog.codes)
    with st.expander("Generate translations", expanded=True):
        render_llm_translation_controls(
            translation_state,
            video_resource,
            catalog,
            widget_prefix="translate",
            prompt_state=prompt_state,
            source_codes=source_codes,
            target_codes=target_codes,
        )

    def refresh_after_publish() -> None:
        reset_video_cache(st.session_state)
        clear_llm_prompt(prompt_state)
        st.rerun()

    def cache_fresh_video(resource) -> None:
        if (
            isinstance(resource, Mapping)
            and resource.get("id") == context.selected_video_id
        ):
            update_selected_video_resource(st.session_state, resource)

    render_preview_publish(
        translation_state,
        context.selected_video_id,
        service,
        catalog.codes,
        widget_prefix="translate",
        on_published=refresh_after_publish,
        language_catalog=catalog,
        on_video_refreshed=cache_fresh_video,
    )


render_translate_page()
