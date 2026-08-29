"""Safe user-facing status and error messages."""

from googleapiclient.errors import HttpError

from youtube_account import YoutubeSetupError, YoutubeVideoNotFoundError

MESSAGES = {
    "oauth_required": "YouTube authorization is required. Complete the browser authorization and try again.",
    "oauth_client_missing": (
        "OAuth client file was not found at config/account_client_secrets_main.json. "
        "Download a Desktop app OAuth client JSON, save it at this exact path, "
        "then restart the app."
    ),
    "oauth_client_invalid": (
        "OAuth client file was found but cannot be used. Create a Google OAuth "
        "client of type Desktop app and replace config/account_client_secrets_main.json."
    ),
    "oauth_authorization_invalid": (
        "Authorization is no longer valid. Restart authorization; if necessary "
        "remove the local token.json and restart Streamlit."
    ),
    "oauth_callback": (
        "Google authorization could not complete on localhost:8080. Close the "
        "process using port 8080 or restart the app and complete Google authorization again."
    ),
    "quota_exceeded": "YouTube API quota is exhausted. Wait for the quota reset before trying again.",
    "video_not_found": "The selected video was not found. Refresh the list and select it again.",
    "translation_unavailable": "The selected language is not available in the configured translation providers.",
    "translation_failed": "Translation failed before the affected localization could be published.",
    "youtube_api": "YouTube could not complete this request. Check the connection and try again.",
    "youtube_network": "Could not reach YouTube/Google. Check the connection and retry.",
    "operation_in_progress": "An operation is already running. Wait for it to finish.",
}

_ERROR_KINDS = {
    "oauth_client_missing",
    "oauth_client_invalid",
    "oauth_authorization_invalid",
    "oauth_callback",
    "quota_exceeded",
    "video_not_found",
    "youtube_network",
    "youtube_api",
}

_AUTH_REASONS = {
    "authError",
    "invalidCredentials",
    "unauthorized",
    "unauthorized_client",
}


def _http_error_reason(error):
    details = getattr(error, "error_details", None) or []
    if details and isinstance(details[0], dict):
        return details[0].get("reason")
    return None


def classify_service_error(error: Exception) -> str:
    """Return a safe semantic key for common YouTube-facing failures."""
    if isinstance(error, YoutubeSetupError):
        return error.kind if error.kind in _ERROR_KINDS else "youtube_api"
    if isinstance(error, YoutubeVideoNotFoundError):
        return "video_not_found"
    if isinstance(error, HttpError):
        reason = _http_error_reason(error)
        status = str(getattr(getattr(error, "resp", None), "status", ""))
        if reason == "quotaExceeded":
            return "quota_exceeded"
        if status == "401" or reason in _AUTH_REASONS:
            return "oauth_authorization_invalid"
        if status.startswith("5"):
            return "youtube_network"
        return "youtube_api"
    if isinstance(error, (ConnectionError, TimeoutError, OSError)):
        return "youtube_network"
    return "youtube_api"


def render_feedback(message: str, kind: str = "info") -> None:
    import streamlit as st

    text = MESSAGES.get(kind, message)
    severity = (
        kind
        if kind in {"success", "warning", "error", "info"}
        else "error"
        if kind in _ERROR_KINDS
        else "info"
    )
    renderer = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
        "info": st.info,
    }[severity]
    renderer(text)


def render_service_error(error: Exception) -> None:
    """Render one actionable, non-sensitive error for a service failure."""
    render_feedback("", classify_service_error(error))
