"""Safe user-facing status and error messages."""


MESSAGES = {
    "oauth_required": "YouTube authorization is required. Complete the browser authorization and try again.",
    "quota_exceeded": "YouTube API quota is exhausted. Wait for the quota reset before trying again.",
    "video_not_found": "The selected video was not found. Refresh the list and select it again.",
    "translation_unavailable": "The selected language is not available in the configured translation providers.",
    "translation_failed": "Translation failed before the affected localization could be published.",
    "youtube_api": "YouTube could not complete this request. Check the connection and try again.",
    "operation_in_progress": "An operation is already running. Wait for it to finish.",
}


def render_feedback(message: str, kind: str = "info") -> None:
    import streamlit as st

    text = MESSAGES.get(kind, message)
    renderer = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
        "info": st.info,
    }.get(kind, st.info)
    renderer(text)
