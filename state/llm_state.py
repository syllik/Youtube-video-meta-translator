"""LLM-page session state kept separate from the Manual page."""

from typing import Any, MutableMapping, Optional, Sequence


LLM_DEFAULTS = {
    "bound_video_id": None,
    "prompt_video_id": None,
    "prompt_target_codes": (),
    "selected_target_codes": (),
    "selected_target_codes_initialized": False,
    "prompt_text": "",
    "consumed_upload_context": None,
    "upload_issue_context": None,
    "upload_issues": (),
    "scroll_to_form": False,
    "raw_json": "",
    "local_validation": None,
    "preview_result": None,
    "preview_fingerprint": None,
    "published": False,
    "operation_status": "idle",
    "operation_error": None,
}


def init_llm_state(session_state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Create the isolated LLM namespace without provider state."""
    state = session_state.setdefault("llm", {})
    state.pop("selected_video_id", None)
    state.pop("scroll_to_prompt", None)
    for key, default in LLM_DEFAULTS.items():
        state.setdefault(key, default)
    return state


def clear_llm_prompt(state: MutableMapping[str, Any]) -> None:
    """Clear prompt metadata that belongs to a previous LLM selection."""
    state["prompt_video_id"] = None
    state["prompt_target_codes"] = ()
    state["selected_target_codes"] = ()
    state["selected_target_codes_initialized"] = False
    state["prompt_text"] = ""
    _clear_llm_upload_state(state)


def _clear_llm_upload_state(state: MutableMapping[str, Any]) -> None:
    state["consumed_upload_context"] = None
    state["upload_issue_context"] = None
    state["upload_issues"] = ()


def _clear_llm_form(state: MutableMapping[str, Any]) -> None:
    state["raw_json"] = ""
    state["local_validation"] = None
    state["preview_result"] = None
    state["preview_fingerprint"] = None
    state["published"] = False
    state["operation_status"] = "idle"
    state["operation_error"] = None


def sync_llm_video(state: MutableMapping[str, Any], video_id: Optional[str]) -> None:
    """Bind LLM form state to the current shared video selection."""
    if state.get("bound_video_id") != video_id:
        state["bound_video_id"] = video_id
        clear_llm_prompt(state)
        _clear_llm_form(state)
        state["scroll_to_form"] = bool(video_id)


def set_llm_selected_codes(
    state: MutableMapping[str, Any], video_id: str, target_codes: Sequence[str]
) -> None:
    """Persist a target selection only when it belongs to the active video."""
    if state.get("bound_video_id") == video_id:
        state["selected_target_codes"] = tuple(target_codes)
        state["selected_target_codes_initialized"] = True


def set_llm_prompt(
    state: MutableMapping[str, Any],
    video_id: str,
    target_codes: Sequence[str],
    prompt: str,
) -> None:
    """Store the generated prompt with its selected video and language targets."""
    state["prompt_video_id"] = video_id
    state["prompt_target_codes"] = tuple(target_codes)
    state["selected_target_codes"] = tuple(target_codes)
    state["selected_target_codes_initialized"] = True
    state["prompt_text"] = prompt
    _clear_llm_upload_state(state)
