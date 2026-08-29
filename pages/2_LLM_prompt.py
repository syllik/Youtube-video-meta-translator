"""Supporting page for preparing a source-aware external-LLM prompt."""

import streamlit as st
from googleapiclient.errors import HttpError

from state.llm_state import init_llm_state, sync_llm_video
from state.manual_state import init_manual_state, sync_manual_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.llm_prompt import render_llm_prompt_page
from ui.source_selection import render_source_selection


def render_llm_prompt_support_page() -> None:
    configure_page("LLM Translation prompt")
    st.title("LLM Translation prompt")
    st.caption(
        "Prepare a prompt for an external LLM, then return to Translate to upload or edit its JSON result."
    )
    st.markdown(
        """
**How this works**

1. Select source and target languages below and copy the prepared prompt.
2. Paste it into a web LLM, then download its result as a UTF-8 `.json` file.
3. Return to **Translate**, upload the file, and fix anything reported by
   local validation in the editable form.
4. Click **Preview changes**, review the diff, then click **Publish changes**
   to upload the translations to YouTube.

The app only needs the Google YouTube OAuth setup. It does not send your video
data to the linked LLM websites or require an LLM API key.
"""
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
        video_resource = context.service.get_video_with_localizations(
            context.selected_video_id
        )
        catalog = context.service.fetch_localization_language_catalog(hl="ru")
    except HttpError:
        st.error("YouTube could not load the selected video or language catalog.")
        return
    except Exception:
        st.error("YouTube could not load the selected video or language catalog.")
        return

    source_codes = render_source_selection(st.session_state, video_resource, catalog)
    render_llm_prompt_page(
        prompt_state, video_resource, catalog, source_codes=source_codes
    )


render_llm_prompt_support_page()
