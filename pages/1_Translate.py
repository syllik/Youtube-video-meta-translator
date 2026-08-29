"""Unified YouTube localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.llm_state import clear_llm_prompt, init_llm_state, sync_llm_video
from state.manual_state import init_manual_state, sync_manual_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_feedback
from ui.llm_package import render_llm_translation_controls
from ui.manual_editor import render_manual_editor
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
        catalog = context.service.fetch_localization_language_catalog(hl="ru")
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
    with st.expander("Generate translations", expanded=True):
        render_llm_translation_controls(
            translation_state,
            video_resource,
            catalog,
            widget_prefix="translate",
            prompt_state=prompt_state,
            source_codes=source_codes,
        )

    service = ManualLocalizationService(context.service, catalog.codes)

    def refresh_after_publish() -> None:
        clear_llm_prompt(prompt_state)
        st.rerun()

    render_manual_editor(
        translation_state,
        context.selected_video_id,
        service,
        catalog.codes,
        widget_prefix="translate",
        on_published=refresh_after_publish,
        default_language_code=(video_resource.get("snippet") or {}).get(
            "defaultLanguage"
        ),
    )


render_translate_page()
