"""Supporting page for choosing LLM localization targets."""

import streamlit as st
from googleapiclient.errors import HttpError

from streamlit_app import configure_page, get_youtube_service
from state.llm_state import init_llm_state
from ui.llm_prompt import render_llm_prompt_page


def render_llm_prompt_support_page() -> None:
    configure_page("LLM Translation prompt")
    st.title("LLM Translation prompt")
    st.caption(
        "Choose missing languages, copy the prompt, and get a downloadable JSON file from an external LLM."
    )

    state = init_llm_state(st.session_state)
    selected_video_id = state.get("selected_video_id")
    if not selected_video_id:
        st.page_link(
            "pages/2_LLM_translate.py",
            label="Select a video on LLM translate",
        )
        return

    try:
        service = get_youtube_service(st.session_state)
        video_resource = service.get_video_with_localizations(selected_video_id)
        catalog = service.fetch_localization_language_catalog(hl="ru")
    except HttpError:
        st.error("YouTube could not load the selected video or language catalog.")
        return
    except Exception:
        st.error("YouTube could not load the selected video or language catalog.")
        return

    render_llm_prompt_page(state, video_resource, catalog)


render_llm_prompt_support_page()
