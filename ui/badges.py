"""Small shared renderers for YouTube localization language badges."""

import html
from typing import Iterable, Optional


def render_language_badges(
    codes: Iterable[str], label: Optional[str] = None
) -> None:
    """Render language codes with the shared localization badge styling."""
    import streamlit as st

    badges = " ".join(
        '<span class="localization-badge">{}</span>'.format(html.escape(str(code)))
        for code in codes
    )
    if badges:
        prefix = "{}: ".format(html.escape(label)) if label else ""
        st.markdown(prefix + badges, unsafe_allow_html=True)
