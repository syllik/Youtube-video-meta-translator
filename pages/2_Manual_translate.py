"""Manual localization workflow page."""

import streamlit as st

from services.manual_localization_service import ManualLocalizationService
from state.manual_state import init_manual_state
from streamlit_app import render_common_page_context
from ui.manual_editor import render_manual_editor
from ui.pagination import render_pagination
from ui.video_list import render_video_list


def render_manual_page() -> None:
    context = render_common_page_context("manual")
    if context is None:
        return

    state = init_manual_state(st.session_state)
    selection = render_video_list(context.page.videos, "manual", {}, state)
    video = next(
        (candidate for candidate in context.page.videos
         if candidate.id == selection.selected_manual_video_id),
        None,
    )
    if video is None:
        st.info("Select one video to begin.")
    else:
        service = ManualLocalizationService(
            context.service, context.service.supported_language_codes()
        )
        render_manual_editor(
            state,
            video,
            service,
            context.service.supported_language_codes(),
        )
    render_pagination(context.selection, context.channel.total_videos, st.query_params)


render_manual_page()
