"""Universal Translate editor state and stale-preview rules."""

import hashlib
from typing import Any, Mapping, MutableMapping, Optional, Tuple

from localizations import build_manual_draft_json


MANUAL_DEFAULTS = {
    "bound_video_id": None,
    "draft_video_id": None,
    "reload_requested": False,
    "scroll_to_form": False,
    "raw_json": "",
    "pending_editor_json": None,
    "local_validation": None,
    "preview_result": None,
    "preview_fingerprint": None,
    "published": False,
    "operation_status": "idle",
    "operation_error": None,
}


def init_manual_state(session_state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    state = session_state.setdefault("manual", {})
    state.pop("selected_video_id", None)
    for key, default in MANUAL_DEFAULTS.items():
        state.setdefault(key, default)
    return state


def manual_fingerprint(video_id: Optional[str], raw_json: str) -> Optional[Tuple[Optional[str], str]]:
    if not video_id:
        return None
    digest = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()
    return video_id, digest


def _clear_preview(state: MutableMapping[str, Any]) -> None:
    state["preview_result"] = None
    state["preview_fingerprint"] = None
    state["published"] = False
    state["operation_error"] = None


def _clear_translation_form(state: MutableMapping[str, Any]) -> None:
    state["raw_json"] = ""
    state["pending_editor_json"] = None
    state["local_validation"] = None
    state["operation_status"] = "idle"
    _clear_preview(state)


def sync_manual_video(state: MutableMapping[str, Any], video_id: Optional[str]) -> None:
    """Bind Manual form state to the current shared video selection."""
    if state.get("bound_video_id") != video_id:
        state["bound_video_id"] = video_id
        state["draft_video_id"] = None
        state["reload_requested"] = False
        _clear_translation_form(state)
        state["scroll_to_form"] = bool(video_id)


def request_manual_reload(state: MutableMapping[str, Any]) -> None:
    """Request a fresh live draft on the next selected-video load."""
    state["reload_requested"] = True
    _clear_preview(state)


def load_manual_draft(
    state: MutableMapping[str, Any],
    video_resource: Mapping[str, Any],
    force: bool = False,
) -> bool:
    """Load live localizations only when the draft lifecycle requires it."""
    video_id = video_resource.get("id")
    if not video_id:
        return False
    if (
        not force
        and not state.get("reload_requested")
        and state.get("draft_video_id") == video_id
    ):
        return False

    state["raw_json"] = build_manual_draft_json(video_resource)
    state["draft_video_id"] = video_id
    state["reload_requested"] = False
    state["local_validation"] = None
    state["operation_status"] = "idle"
    _clear_preview(state)
    return True


def set_manual_json(state: MutableMapping[str, Any], raw_json: str) -> None:
    if state.get("raw_json") != raw_json:
        state["raw_json"] = raw_json
        _clear_preview(state)


def request_manual_editor_update(
    state: MutableMapping[str, Any], raw_json: str
) -> None:
    """Queue a widget update for the next render before the editor is created."""
    set_manual_json(state, raw_json)
    state["pending_editor_json"] = raw_json


def store_manual_preview(state: MutableMapping[str, Any], result: Any) -> None:
    state["preview_result"] = result
    state["preview_fingerprint"] = manual_fingerprint(
        state.get("bound_video_id"), state.get("raw_json", "")
    )
    state["published"] = False
    state["operation_error"] = None


def manual_preview_is_current(state: Mapping[str, Any]) -> bool:
    return bool(
        state.get("preview_result") is not None
        and state.get("preview_fingerprint")
        == manual_fingerprint(state.get("bound_video_id"), state.get("raw_json", ""))
    )


def manual_can_publish(state: Mapping[str, Any]) -> bool:
    if not manual_preview_is_current(state):
        return False
    result = state["preview_result"]
    return bool(
        not state.get("published")
        and result.plan.is_valid
        and result.plan.has_changes
    )
