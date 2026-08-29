"""Shared Streamlit state for channel data and cursor-backed video pages."""

from typing import Any, MutableMapping, Optional

from models import PageLimit, YouTubePage
from ui.pagination import PaginationSelection, total_pages


def init_common_state(state: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Create the common namespace without constructing external clients."""
    state.setdefault("common.page_tokens_by_limit", {})
    state.setdefault("common.video_pages_by_limit", {})
    state.setdefault("common.channel", None)
    state.setdefault("common.active_limit", None)
    state.setdefault("common.load_error", None)
    state.setdefault("common.selected_video_id", None)
    state.setdefault("common.source_video_id", None)
    state.setdefault("common.selected_source_codes", ())
    return state


def sync_source_selection(
    state: MutableMapping[str, Any],
    video_id: Optional[str],
    default_source_code: Optional[str],
    available_source_codes,
):
    """Keep required primary source selection scoped to one selected video."""
    init_common_state(state)
    available = tuple(
        code.strip()
        for code in available_source_codes
        if isinstance(code, str) and code.strip()
    )
    available_by_folded = {code.casefold(): code for code in available}
    default_code = (
        default_source_code.strip()
        if isinstance(default_source_code, str) and default_source_code.strip()
        else None
    )
    if default_code is not None:
        default_code = available_by_folded.get(default_code.casefold(), default_code)

    if state.get("common.source_video_id") != video_id:
        state["common.source_video_id"] = video_id
        state["common.selected_source_codes"] = (
            (default_code,) if default_code is not None else ()
        )
    else:
        selected = state.get("common.selected_source_codes") or ()
        normalized = []
        seen = set()
        for code in selected:
            if not isinstance(code, str):
                continue
            canonical = available_by_folded.get(code.strip().casefold())
            if canonical is not None and canonical.casefold() not in seen:
                normalized.append(canonical)
                seen.add(canonical.casefold())
        if default_code is not None and default_code.casefold() not in seen:
            normalized.insert(0, default_code)
        elif default_code is not None:
            normalized = [
                default_code,
                *[code for code in normalized if code.casefold() != default_code.casefold()],
            ]
        state["common.selected_source_codes"] = tuple(normalized)

    return tuple(state["common.selected_source_codes"])


def set_source_selection(
    state: MutableMapping[str, Any],
    video_id: Optional[str],
    selected_source_codes,
    default_source_code: Optional[str],
    available_source_codes,
):
    """Store a normalized source selection while always retaining the primary."""
    current = sync_source_selection(
        state, video_id, default_source_code, available_source_codes
    )
    available = tuple(
        code.strip()
        for code in available_source_codes
        if isinstance(code, str) and code.strip()
    )
    available_by_folded = {code.casefold(): code for code in available}
    default_code = (
        next(
            (
                code
                for code in available
                if isinstance(default_source_code, str)
                and code.casefold() == default_source_code.strip().casefold()
            ),
            default_source_code.strip()
            if isinstance(default_source_code, str) and default_source_code.strip()
            else None,
        )
    )
    selected = []
    seen = set()
    for code in current if selected_source_codes is None else selected_source_codes:
        if not isinstance(code, str):
            continue
        canonical = available_by_folded.get(code.strip().casefold())
        if canonical is not None and canonical.casefold() not in seen:
            selected.append(canonical)
            seen.add(canonical.casefold())
    if default_code is not None:
        selected = [
            default_code,
            *[code for code in selected if code.casefold() != default_code.casefold()],
        ]
    state["common.selected_source_codes"] = tuple(selected)
    return tuple(selected)


def get_selected_video_id(state: MutableMapping[str, Any]) -> Optional[str]:
    """Return the video selected across all workflows."""
    init_common_state(state)
    return state.get("common.selected_video_id")


def set_selected_video_id(
    state: MutableMapping[str, Any], video_id: Optional[str]
) -> bool:
    """Set the shared selected video and report whether it changed."""
    init_common_state(state)
    if state.get("common.selected_video_id") == video_id:
        return False
    state["common.selected_video_id"] = video_id
    return True


def reset_video_cache(state: MutableMapping[str, Any]) -> None:
    """Clear only page-derived data; mode-specific state is untouched."""
    state["common.page_tokens_by_limit"] = {}
    state["common.video_pages_by_limit"] = {}
    state["common.load_error"] = None


def _page_state(state: MutableMapping[str, Any], limit: PageLimit):
    token_cache = state.setdefault("common.page_tokens_by_limit", {})
    page_cache = state.setdefault("common.video_pages_by_limit", {})
    token_cache.setdefault(limit, {1: None})
    page_cache.setdefault(limit, {})
    return token_cache[limit], page_cache[limit]


def _load_numeric_page(service, state, selection: PaginationSelection) -> YouTubePage:
    token_cache, page_cache = _page_state(state, selection.limit)
    if selection.page in page_cache:
        return page_cache[selection.page]

    current_page = max((page_cache.keys() or [0])) + 1
    if current_page > selection.page:
        current_page = 1
    page_token = token_cache.get(current_page)

    while current_page <= selection.page:
        if current_page in page_cache:
            result = page_cache[current_page]
        else:
            result = service.fetch_video_page(selection.limit, page_token)
            page_cache[current_page] = result
            if result.next_page_token:
                token_cache[current_page + 1] = result.next_page_token

        if current_page == selection.page:
            return result
        if not result.next_page_token:
            return YouTubePage(videos=(), next_page_token=None)
        current_page += 1
        page_token = token_cache.get(current_page)

    return YouTubePage(videos=(), next_page_token=None)


def _load_all_pages(service, state) -> YouTubePage:
    token_cache, page_cache = _page_state(state, "all")
    if "combined" in page_cache:
        return page_cache["combined"]

    combined = []
    page_number = 1
    page_token = token_cache.get(1)
    while True:
        if page_number in page_cache:
            result = page_cache[page_number]
        else:
            result = service.fetch_video_page("all", page_token)
            page_cache[page_number] = result
            if result.next_page_token:
                token_cache[page_number + 1] = result.next_page_token
        combined.extend(result.videos)
        if not result.next_page_token:
            break
        page_number += 1
        page_token = token_cache.get(page_number)

    combined_result = YouTubePage(videos=tuple(combined), next_page_token=None)
    page_cache["combined"] = combined_result
    return combined_result


def load_video_page(service, state: MutableMapping[str, Any], selection: PaginationSelection) -> YouTubePage:
    """Load a numeric or explicit all page using cached YouTube cursors."""
    init_common_state(state)
    if selection.limit == "all":
        return _load_all_pages(service, state)
    return _load_numeric_page(service, state, selection)


def clamp_selection(selection: PaginationSelection, total_videos: int) -> PaginationSelection:
    """Clamp a URL selection after the channel count is known."""
    if selection.limit == "all":
        return PaginationSelection(page=1, limit="all")
    last_page = total_pages(selection.limit, total_videos)
    return PaginationSelection(
        page=min(max(selection.page, 1), last_page),
        limit=selection.limit,
    )
