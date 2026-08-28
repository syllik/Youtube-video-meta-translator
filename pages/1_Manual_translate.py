"""Manual localization workflow page."""

import streamlit as st
from googleapiclient.errors import HttpError

from services.manual_localization_service import ManualLocalizationService
from state.manual_state import init_manual_state, sync_manual_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_feedback
from ui.manual_editor import render_manual_editor


def render_manual_page() -> None:
    configure_page("Manual translate")
    st.title("Manual translate")
    st.caption(
        "Review prepared localization JSON for one video before publishing it."
    )
    context = bootstrap_app_context()
    if context is None:
        return

    state = init_manual_state(st.session_state)
    sync_manual_video(state, context.selected_video_id)
    if not context.selected_video_id:
        st.info("Select one video from the sidebar to begin.")
        return

    try:
        catalog = context.service.fetch_localization_language_catalog(hl="ru")
    except HttpError:
        render_feedback("", "youtube_api")
    except Exception:
        render_feedback("", "youtube_api")
    else:
        service = ManualLocalizationService(context.service, catalog.codes)
        render_manual_editor(
            state,
            context.selected_video_id,
            service,
            catalog.codes,
        )


render_manual_page()
