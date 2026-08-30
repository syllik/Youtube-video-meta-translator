"""Supporting page for preparing a source-aware external-LLM prompt."""

import streamlit as st

from state.common_state import get_selected_video_resource
from state.llm_state import init_llm_state, sync_llm_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.feedback import render_service_error
from ui.llm_prompt import render_llm_prompt_page, render_source_quality_guide
from ui.source_selection import render_source_selection


def render_llm_prompt_support_page() -> None:
    configure_page("LLM Translation prompt")
    st.title("LLM Translation prompt")
    st.caption(
        "Prepare a prompt for an external LLM, then return to Translate to upload its JSON result."
    )
    with st.expander("How to use this page", expanded=False):
        st.markdown(
            """
1. Select source and target languages and copy the prepared prompt.
2. Paste it into a web LLM and download its UTF-8 `.json` result.
3. Return to **Translate** and upload the file.
4. Preview the changes, then publish them to YouTube.

The app needs only the Google YouTube OAuth setup. It does not send your video
data to linked LLM websites or require an LLM API key.
"""
        )
    render_source_quality_guide()

    context = bootstrap_app_context()
    if context is None:
        return

    prompt_state = init_llm_state(st.session_state)
    sync_llm_video(prompt_state, context.selected_video_id)
    if not context.selected_video_id:
        st.info("Select one video from the sidebar to begin.")
        return

    try:
        with st.spinner("Loading selected video and metadata language catalog..."):
            video_resource = get_selected_video_resource(
                context.service, st.session_state, context.selected_video_id
            )
            catalog = context.metadata_language_catalog
    except Exception as error:
        render_service_error(error)
        return

    source_codes = render_source_selection(st.session_state, video_resource, catalog)
    render_llm_prompt_page(
        prompt_state, video_resource, catalog, source_codes=source_codes
    )


render_llm_prompt_support_page()
