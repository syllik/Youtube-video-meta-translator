"""Small, readable style layer for the Streamlit application."""


def apply_app_styles() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        .block-container { max-width: 1180px; padding-top: 2rem; }
        .channel-logo { display: block; width: 100%; max-width: none; height: auto;
                        aspect-ratio: 1 / 1; object-fit: cover; border-radius: .75rem; }
        .channel-description { opacity: .78; line-height: 1.45; white-space: pre-wrap; }
        .video-thumbnail-link { display: block; position: relative; overflow: hidden;
                                border-radius: .5rem; outline: none; }
        .video-thumbnail-link img { display: block; width: 100%; height: auto; aspect-ratio: 16 / 9;
                                    object-fit: cover; }
        .video-external-link { position: absolute; top: .45rem; right: .45rem; display: grid;
                               width: 2rem; height: 2rem; place-items: center; color: white;
                               background: rgba(0,0,0,.58); border-radius: .4rem; opacity: 1;
                               transition: background .15s ease, transform .15s ease; }
        .video-thumbnail-link:hover .video-external-link,
        .video-thumbnail-link:focus-visible .video-external-link { background: rgba(0,0,0,.78);
                                                                    transform: translateY(-1px); }
        .video-thumbnail-link:focus-visible { box-shadow: 0 0 0 .18rem rgba(66, 153, 225, .9); }
        .video-external-link svg { width: 2rem; height: 2rem; fill: none; stroke: currentColor;
                                   stroke-linecap: round; stroke-linejoin: round; stroke-width: 1.8; }
        .video-title { margin-top: .45rem; font-size: 1.05rem; font-weight: 650; line-height: 1.35; }
        .video-default-language { margin-top: .25rem; font-size: .82rem; font-weight: 600; }
        .video-localizations { font-size: .82rem; }
        .video-id { opacity: .62; font-family: monospace; font-size: .78rem; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(128,128,128,.2);
                                                            background: rgba(255,255,255,.035);
                                                            box-shadow: 0 .25rem .9rem rgba(0,0,0,.1); }
        @media (max-width: 700px) {
            .block-container { padding: 1rem .75rem; }
            .video-title { font-size: 1rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
