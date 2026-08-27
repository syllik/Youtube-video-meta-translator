"""Small, readable style layer for the Streamlit application."""


def apply_app_styles() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 2rem; }
        .video-row { padding: 0.75rem 0; border-bottom: 1px solid rgba(128,128,128,.25); }
        .video-title { font-size: 1.05rem; font-weight: 650; line-height: 1.35; }
        .video-description { opacity: .78; line-height: 1.45; }
        .video-id { opacity: .62; font-family: monospace; font-size: .78rem; }
        .localization-badge { display: inline-block; margin: .25rem .25rem 0 0; padding: .15rem .45rem;
                              border-radius: .35rem; background: rgba(128,128,128,.22); font-size: .78rem; }
        @media (max-width: 700px) {
            .block-container { padding: 1rem .75rem; }
            .video-title { font-size: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
