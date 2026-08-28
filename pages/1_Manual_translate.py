"""Manual localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.manual_state import init_manual_state
from streamlit_app import render_common_page_context
from ui.feedback import render_feedback
from ui.manual_editor import render_manual_editor
from ui.pagination import render_pagination
from ui.video_list import render_video_list


def render_manual_page() -> None:
    context = render_common_page_context("manual")
    if context is None:
        return

    state = init_manual_state(st.session_state)
    videos_by_id = {candidate.id: candidate for candidate in context.page.videos}
    selected_video_id = state.get("selected_video_id")
    if selected_video_id is None:
        st.info("Select one video to begin.")
    elif selected_video_id not in videos_by_id:
        st.info(
            "The selected video is on another page. Select a video here to switch."
        )

    selection = render_video_list(context.page.videos, "manual", {}, state)
    selected_video_id = selection.selected_manual_video_id
    if selected_video_id in videos_by_id:
        video = videos_by_id[selected_video_id]
        try:
            catalog = context.service.fetch_localization_language_catalog(hl="ru")
        except HttpError:
            render_feedback("", "youtube_api")
        except Exception:
            render_feedback("", "youtube_api")
        else:
            service = ManualLocalizationService(context.service, catalog.codes)
            render_manual_editor(state, video, service, catalog.codes)
    render_pagination(context.selection, context.channel.total_videos, st.query_params)


render_manual_page()
