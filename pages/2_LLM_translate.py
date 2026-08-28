"""Prompt-only localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.llm_state import clear_llm_prompt, init_llm_state, sync_llm_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_feedback
from ui.llm_package import render_llm_translation_controls
from ui.manual_editor import render_manual_editor


def render_llm_page() -> None:
    configure_page("LLM translate")
    st.title("LLM translate")
    st.caption(
        "Copy a prompt for an external LLM, upload its JSON result, and publish it safely."
    )
    context = bootstrap_app_context()
    if context is None:
        return

    state = init_llm_state(st.session_state)
    sync_llm_video(state, context.selected_video_id)
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
            context.selected_video_id,
            service,
            catalog.codes,
            widget_prefix="llm",
            on_published=refresh_after_publish,
            default_language_code=(video_resource.get("snippet") or {}).get(
                "defaultLanguage"
            ),
        )


render_llm_page()
