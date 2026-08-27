"""Streamlit entry point for the YouTube metadata translator."""

from typing import Any, MutableMapping

import streamlit as st


PAGE_TITLES = {
    "machine": "Machine translate",
    "manual": "Manual translate",
}


def page_title(mode: str) -> str:
    """Return the user-facing title for a supported workflow."""
    try:
        return PAGE_TITLES[mode]
    except KeyError:
        raise ValueError("Unknown application mode: {}".format(mode)) from None


def configure_page(title: str = "YouTube Metadata Translator") -> None:
    """Configure the shared Streamlit page shell."""
    st.set_page_config(
        page_title=title,
        page_icon="▶",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def get_youtube_service(session_state: MutableMapping[str, Any]):
    """Create the YouTube service only when a page first needs it."""
    service = session_state.get("common.youtube_service")
    if service is None:
        from services.youtube_service import YoutubeService

        service = YoutubeService()
        session_state["common.youtube_service"] = service
    return service


def render_app_intro() -> None:
    """Render the small root page; workflow controls live on the two pages."""
    configure_page()
    st.title("YouTube Metadata Translator")
    st.write("Choose a workflow from the navigation panel.")
    st.page_link("pages/1_Machine_translate.py", label="Machine translate")
    st.page_link("pages/2_Manual_translate.py", label="Manual translate")


if __name__ == "__main__":
    render_app_intro()
