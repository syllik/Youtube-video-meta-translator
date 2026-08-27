"""Machine translation workflow page."""

import streamlit as st

from services.machine_translation_service import MachineTranslationService
from state.machine_state import init_machine_state
from streamlit_app import render_common_page_context
from ui.feedback import render_feedback
from ui.machine_controls import render_machine_controls
from ui.pagination import render_pagination
from ui.video_list import render_video_list


def get_machine_translation_service(session_state, youtube_service):
    service = session_state.get("machine.translation_service")
    if service is None:
        from deepl import Translator
        from google_translate import TranslateApi
        from dotenv import load_dotenv
        import os

        load_dotenv()
        deepl = None
        api_key = os.getenv("DEEPL_API_KEY")
        if api_key:
            try:
                deepl = Translator(api_key)
            except Exception:
                deepl = None
        service = MachineTranslationService(
            youtube_service,
            deepl=deepl,
            google=TranslateApi(),
        )
        session_state["machine.translation_service"] = service
    return service


def _render_result(result):
    if result.translated:
        st.success("Published {} localization(s).".format(result.translated))
    if result.skipped:
        st.warning("Skipped {} localization(s).".format(result.skipped))
    if result.trimmed:
        st.info("Trimmed {} text value(s).".format(result.trimmed))
    for error in result.errors:
        render_feedback(error.message, error.error_type)


def render_machine_page() -> None:
    context = render_common_page_context("machine")
    if context is None:
        return

    state = init_machine_state(st.session_state)
    if context.selection.limit == "all":
        previous_select_all = bool(state.get("select_all_channel"))
        select_all_channel = st.checkbox(
            "Select all channel videos",
            value=bool(state.get("select_all_channel")),
            key="machine-select-all-channel",
        )
        state["select_all_channel"] = select_all_channel
        if previous_select_all and not select_all_channel:
            state["selected_video_ids"] = set()
        if select_all_channel:
            state["selected_video_ids"] = {video.id for video in context.page.videos}

    language_options = context.service.code_to_name
    options, clicked = render_machine_controls(
        state,
        language_options,
        disabled=state.get("operation_status") == "running",
    )
    render_video_list(context.page.videos, "machine", state, {})
    if state.get("select_all_channel") and state.get("selected_video_ids") != {
        video.id for video in context.page.videos
    }:
        state["select_all_channel"] = False
    render_pagination(context.selection, context.channel.total_videos, st.query_params)

    if clicked:
        state["operation_status"] = "running"
        try:
            with st.spinner("Translating selected videos..."):
                result = get_machine_translation_service(
                    st.session_state, context.service
                ).translate_and_publish(
                    sorted(state["selected_video_ids"]),
                    sorted(state["selected_language_codes"]),
                    options,
                )
            state["operation_result"] = result
            state["operation_status"] = "idle"
            from state.common_state import reset_video_cache

            reset_video_cache(st.session_state)
            st.rerun()
        except Exception:
            state["operation_status"] = "idle"
            state["operation_error"] = "translation_failed"
            render_feedback("", "translation_failed")

    if state.get("operation_result") is not None:
        _render_result(state["operation_result"])


render_machine_page()
