"""Supporting page for choosing LLM localization targets."""

import streamlit as st
from googleapiclient.errors import HttpError

from state.llm_state import init_llm_state, sync_llm_video
from streamlit_app import bootstrap_app_context, configure_page
from ui.llm_prompt import render_llm_prompt_page


def render_llm_prompt_support_page() -> None:
    configure_page("LLM Translation prompt")
    st.title("LLM Translation prompt")
    st.caption(
        "Choose missing languages, copy the prompt, and get a downloadable JSON file from an external LLM."
    )
    st.markdown(
        """
**How this works**

1. Select the target languages below and copy the prepared prompt.
2. Paste it into a web LLM, then download its result as a UTF-8 `.json` file.
3. The file must be a direct JSON object with one `title` and `description`
   for every requested language code — without Markdown, prose, or a wrapper.
4. Return to **LLM translate**, upload the file, and fix anything reported by
   local validation in the editable form.
5. Click **Preview changes**, review the diff, then click **Publish changes**
   to upload the translations to YouTube.

The app only needs the Google YouTube OAuth setup. It does not send your video
data to the linked LLM websites or require an LLM API key.
"""
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

    render_llm_prompt_page(state, video_resource, catalog)


render_llm_prompt_support_page()
