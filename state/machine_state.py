"""Machine-page session state helpers."""

from typing import Any, Mapping, MutableMapping, Sequence


MACHINE_DEFAULTS = {
    "selected_video_ids": set(),
    "select_all_visible": False,
    "select_all_channel": False,
    "select_all_channel_reset_pending": False,
    "selected_language_codes": set(),
    "prefer_deepl": False,
    "overwrite": False,
    "trim": False,
    "operation_status": "idle",
    "operation_result": None,
    "operation_error": None,
}


def init_machine_state(session_state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    state = session_state.setdefault("machine", {})
    for key, default in MACHINE_DEFAULTS.items():
        if key not in state:
            state[key] = set(default) if isinstance(default, set) else default
    return state


def clear_machine_operation(session_state: MutableMapping[str, Any]) -> None:
    state = init_machine_state(session_state)
    state["operation_status"] = "idle"
    state["operation_result"] = None
    state["operation_error"] = None


def machine_can_submit(state: Mapping[str, Any]) -> bool:
    return bool(
        state.get("selected_video_ids")
        and state.get("selected_language_codes")
        and state.get("operation_status") != "running"
    )


def reconcile_select_all_channel(
    state: MutableMapping[str, Any], visible_video_ids: Sequence[str]
) -> bool:
    """Clear stale all-channel intent after selection changes elsewhere."""
    if state.get("select_all_channel") and set(
        state.get("selected_video_ids", set())
    ) != set(visible_video_ids):
        state["select_all_channel"] = False
        state["select_all_channel_reset_pending"] = True
    return bool(state.get("select_all_channel"))
