"""Unified YouTube localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.llm_state import clear_llm_prompt, init_llm_state, sync_llm_video
from state.manual_state import init_manual_state, load_manual_draft, sync_manual_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_feedback
from ui.llm_package import render_llm_translation_controls
from ui.manual_editor import (
    localization_editor_key,
    render_localization_json_example,
    render_manual_editor,
    render_preview_publish,
)
from ui.source_selection import render_source_selection


def render_translate_page() -> None:
    configure_page("Translate")
    st.title("Translate")
    st.caption(
        "Generate translations with Codex or provide localization JSON, then validate, preview, and publish safely."
    )
    context = bootstrap_app_context()
    if context is None:
        return

    translation_state = init_manual_state(st.session_state)
    prompt_state = init_llm_state(st.session_state)
    sync_manual_video(translation_state, context.selected_video_id)
    sync_llm_video(prompt_state, context.selected_video_id)
    if not context.selected_video_id:
        st.info("Select one video from the sidebar to begin.")
        return

    try:
        with st.spinner("Loading selected video and language catalog..."):
            catalog = context.language_catalog
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

    pending_reload_id = st.session_state.get("common.manual_reload_video_id")
    if pending_reload_id is not None:
        st.session_state["common.manual_reload_video_id"] = None
    draft_loaded = load_manual_draft(
        translation_state,
        video_resource,
        force=pending_reload_id == context.selected_video_id,
    )
    if draft_loaded:
        st.session_state[localization_editor_key(
            "translate", context.selected_video_id
        )] = translation_state["raw_json"]

    render_localization_json_example(
        catalog.codes,
        default_language_code=(video_resource.get("snippet") or {}).get(
            "defaultLanguage"
        ),
    )
    service = ManualLocalizationService(context.service, catalog.codes)
    render_manual_editor(
        translation_state,
        context.selected_video_id,
        service,
        catalog.codes,
        widget_prefix="translate",
        default_language_code=(video_resource.get("snippet") or {}).get(
            "defaultLanguage"
        ),
    )

    source_codes = render_source_selection(st.session_state, video_resource, catalog)
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
