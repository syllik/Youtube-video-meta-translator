"""Native browser-confirmed reset control for sidebar video cards."""

from pathlib import Path
from typing import Optional


_COMPONENT = None


def reset_widget_key(video_id: str) -> str:
    return "common-reset-video-{}".format(video_id)


def _component():
    global _COMPONENT
    if _COMPONENT is None:
        import streamlit.components.v1 as components

        _COMPONENT = components.declare_component(
            "reset_video_button",
            path=Path(__file__).with_name("reset_video_component").resolve(),
        )
    return _COMPONENT


def render_reset_button(
    video_id: str, warning: str, key: Optional[str] = None
) -> Optional[str]:
    """Render a confirm button and return its event token after confirmation."""
    try:
        result = _component()(
            video_id=video_id,
            warning=warning,
            label="Reset languages",
            default=None,
            key=key or reset_widget_key(video_id),
        )
    except (ImportError, AttributeError):
        # Unit-test fakes can provide ``streamlit`` without its component API.
        return None
    if not isinstance(result, dict) or result.get("video_id") != video_id:
        return None
    event_id = result.get("event_id")
    return str(event_id) if event_id else None
