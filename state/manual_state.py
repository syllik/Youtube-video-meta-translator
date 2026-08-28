"""Manual-page session state and stale-preview rules."""

import hashlib
from typing import Any, Mapping, MutableMapping, Optional, Tuple


MANUAL_DEFAULTS = {
    "selected_video_id": None,
    "scroll_to_form": False,
    "raw_json": "",
    "local_validation": None,
    "preview_result": None,
    "preview_fingerprint": None,
    "published": False,
    "operation_status": "idle",
    "operation_error": None,
}


def init_manual_state(session_state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    state = session_state.setdefault("manual", {})
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


def set_manual_video(state: MutableMapping[str, Any], video_id: Optional[str]) -> None:
    if state.get("selected_video_id") != video_id:
        state["selected_video_id"] = video_id
        _clear_preview(state)
        state["scroll_to_form"] = True


def set_manual_json(state: MutableMapping[str, Any], raw_json: str) -> None:
    if state.get("raw_json") != raw_json:
        state["raw_json"] = raw_json
        _clear_preview(state)


def store_manual_preview(state: MutableMapping[str, Any], result: Any) -> None:
    state["preview_result"] = result
    state["preview_fingerprint"] = manual_fingerprint(
        state.get("selected_video_id"), state.get("raw_json", "")
    )
    state["published"] = False
    state["operation_error"] = None


def manual_preview_is_current(state: Mapping[str, Any]) -> bool:
    return bool(
        state.get("preview_result") is not None
        and state.get("preview_fingerprint")
        == manual_fingerprint(state.get("selected_video_id"), state.get("raw_json", ""))
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
