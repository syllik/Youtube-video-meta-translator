"""Static FAQ page."""

from streamlit_app import configure_page
from ui.faq import render_faq_page


configure_page("FAQ")
render_faq_page()
