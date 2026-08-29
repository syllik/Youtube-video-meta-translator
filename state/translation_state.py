"""Translation draft and Preview state scoped to the selected video."""

import copy
import hashlib
import json
from typing import Any, Mapping, MutableMapping, Optional, Tuple

from llm_localization_package import build_selected_llm_languages


TRANSLATION_DEFAULTS = {
    "bound_video_id": None,
    "target_video_id": None,
    "selected_target_codes": (),
    "generation_video_id": None,
    "generation_target_codes": (),
    "generation_completed_codes": (),
    "generation_completed_batch_count": 0,
    "generation_total_batches": 0,
    "generation_last_batch_codes": (),
    "generation_error": None,
    "draft": {},
    "draft_validation": None,
    "preview_result": None,
    "preview_fingerprint": None,
    "published": False,
    "operation_status": "idle",
    "operation_error": None,
}


def init_translation_state(
    session_state: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    state = session_state.setdefault("translation", {})
    for key, default in TRANSLATION_DEFAULTS.items():
        state.setdefault(key, copy.deepcopy(default))
    return state


def _clear_preview(state: MutableMapping[str, Any]) -> None:
    state["preview_result"] = None
    state["preview_fingerprint"] = None
    state["published"] = False
    state["operation_error"] = None


def clear_translation_draft(state: MutableMapping[str, Any]) -> None:
    state["target_video_id"] = None
    state["selected_target_codes"] = ()
    clear_translation_generation(state)
    state["draft"] = {}
    state["draft_validation"] = None
    state["operation_status"] = "idle"
    _clear_preview(state)


def clear_translation_generation(state: MutableMapping[str, Any]) -> None:
    """Clear resumable Codex checkpoints for the active video."""
    state["generation_video_id"] = None
    state["generation_target_codes"] = ()
    state["generation_completed_codes"] = ()
    state["generation_completed_batch_count"] = 0
    state["generation_total_batches"] = 0
    state["generation_last_batch_codes"] = ()
    state["generation_error"] = None


def sync_translation_video(
    state: MutableMapping[str, Any], video_id: Optional[str]
) -> None:
    """Clear draft and Preview whenever the selected video changes."""
    if state.get("bound_video_id") != video_id:
        state["bound_video_id"] = video_id
        clear_translation_draft(state)


def _normalize_persisted_target_selection(progress, selected_codes):
    available = {
        language.code.casefold(): language.code for language in progress.missing
    }
    filtered = []
    seen = set()
    for raw_code in selected_codes or ():
        if not isinstance(raw_code, str):
            continue
        code = raw_code.strip().casefold()
        if code in available and code not in seen:
            filtered.append(available[code])
            seen.add(code)
    return tuple(
        language.code
        for language in build_selected_llm_languages(
            progress, filtered, max_count=None
        )
    )


def sync_translation_target_selection(
    state: MutableMapping[str, Any], video_id: Optional[str], progress
) -> Tuple[str, ...]:
    """Keep target choices scoped to one video and current source exclusions."""
    for key, default in TRANSLATION_DEFAULTS.items():
        state.setdefault(key, copy.deepcopy(default))
    if state.get("target_video_id") != video_id:
        state["target_video_id"] = video_id
        state["selected_target_codes"] = tuple(
            language.code for language in progress.missing
        )
    else:
        state["selected_target_codes"] = _normalize_persisted_target_selection(
            progress, state.get("selected_target_codes")
        )
    return tuple(state["selected_target_codes"])


def set_translation_target_selection(
    state: MutableMapping[str, Any],
    video_id: Optional[str],
    progress,
    selected_codes,
) -> Tuple[str, ...]:
    """Store an explicit, catalog-ordered target subset for one video."""
    if state.get("target_video_id") != video_id:
        state["target_video_id"] = video_id
    selected = build_selected_llm_languages(
        progress, selected_codes, max_count=None
    )
    state["selected_target_codes"] = tuple(language.code for language in selected)
    return tuple(state["selected_target_codes"])


def _merge_entries(
    current: Mapping[str, Any], incoming: Mapping[str, Any]
) -> dict:
    incoming_items = tuple(incoming.items())
    incoming_by_folded = {
        key.casefold(): (key, value)
        for key, value in incoming_items
        if isinstance(key, str)
    }
    merged = {}
    consumed = set()
    for key, value in current.items():
        folded = key.casefold() if isinstance(key, str) else None
        replacement = incoming_by_folded.get(folded)
        if replacement is None:
            merged[key] = copy.deepcopy(value)
            continue
        incoming_key, incoming_value = replacement
        merged[incoming_key] = copy.deepcopy(incoming_value)
        consumed.add(folded)
    for key, value in incoming_items:
        folded = key.casefold() if isinstance(key, str) else None
        if folded not in consumed:
            merged[key] = copy.deepcopy(value)
            if folded is not None:
                consumed.add(folded)
    return merged


def merge_translation_draft(
    state: MutableMapping[str, Any], incoming: Mapping[str, Any]
) -> None:
    """Merge validated entries into the selected video's internal draft."""
    current = state.get("draft") or {}
    if not isinstance(current, Mapping):
        current = {}
    if not isinstance(incoming, Mapping):
        return
    state["draft"] = _merge_entries(current, incoming)
    state["draft_validation"] = None
    _clear_preview(state)


def _draft_fingerprint(
    video_id: Optional[str], draft: Mapping[str, Any]
) -> Optional[Tuple[Optional[str], str]]:
    if not video_id:
        return None
    serialized = json.dumps(draft, ensure_ascii=False, sort_keys=True)
    return video_id, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def store_translation_preview(
    state: MutableMapping[str, Any], result: Any
) -> None:
    state["preview_result"] = result
    state["preview_fingerprint"] = _draft_fingerprint(
        state.get("bound_video_id"), state.get("draft") or {}
    )
    state["published"] = False
    state["operation_error"] = None


def translation_preview_is_current(state: Mapping[str, Any]) -> bool:
    return bool(
        state.get("preview_result") is not None
        and state.get("preview_fingerprint")
        == _draft_fingerprint(state.get("bound_video_id"), state.get("draft") or {})
    )


def translation_can_publish(state: Mapping[str, Any]) -> bool:
    if not translation_preview_is_current(state):
        return False
    result = state["preview_result"]
    return bool(
        not state.get("published")
        and result.plan.is_valid
        and result.plan.has_changes
    )
