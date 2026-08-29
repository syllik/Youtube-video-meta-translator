"""Pure pagination rules and the small Streamlit pagination control."""

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping, Tuple

from models import PageLimit


ALLOWED_LIMITS = (10, 20, 50, "all")


def page_size_options():
    return ALLOWED_LIMITS


def _update_page_size_query(
    query_params: MutableMapping[str, str],
    widget_key: str,
) -> None:
    import streamlit as st

    chosen_limit = st.session_state[widget_key]
    query_params.update(
        canonical_pagination_query(PaginationSelection(1, chosen_limit))
    )


@dataclass(frozen=True)
class PaginationSelection:
    page: int
    limit: PageLimit


def _raw_value(params: Mapping[str, str], key: str, default: str) -> str:
    value = params.get(key, default)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else default
    return str(value)


def parse_pagination_query(params: Mapping[str, str]) -> PaginationSelection:
    raw_limit = _raw_value(params, "limit", "10")
    if raw_limit == "all":
        return PaginationSelection(page=1, limit="all")
    if raw_limit not in {"10", "20", "50"}:
        limit = 10
    else:
        limit = int(raw_limit)

    try:
        page = int(_raw_value(params, "page", "1"))
    except (TypeError, ValueError):
        page = 1
    return PaginationSelection(page=max(1, page), limit=limit)


def canonical_pagination_query(selection: PaginationSelection) -> Dict[str, str]:
    page = 1 if selection.limit == "all" else max(1, selection.page)
    return {"page": str(page), "limit": str(selection.limit)}


def total_pages(limit: PageLimit, total_videos: int) -> int:
    if limit == "all":
        return 1
    return max(1, (max(0, total_videos) + int(limit) - 1) // int(limit))


def page_bounds(page: int, limit: PageLimit, total_videos: int) -> Tuple[int, int]:
    if limit == "all":
        return 0, max(0, total_videos)
    start = max(0, page - 1) * int(limit)
    return min(start, max(0, total_videos)), min(start + int(limit), max(0, total_videos))


def render_page_size_control(
    selection: PaginationSelection,
    query_params: MutableMapping[str, str],
) -> None:
    """Render the page-size selector in the channel controls."""
    import streamlit as st

    labels = {
        10: "10 videos",
        20: "20 videos",
        50: "50 videos",
        "all": "All videos",
    }
    widget_key = "common-pagination-limit-select-{}".format(selection.limit)
    options = list(page_size_options())
    st.selectbox(
        "Videos per page",
        options,
        index=options.index(selection.limit),
        format_func=lambda limit: labels[limit],
        key=widget_key,
        on_change=_update_page_size_query,
        args=(query_params, widget_key),
    )


def render_pagination(
    selection: PaginationSelection,
    total_videos: int,
    query_params: MutableMapping[str, str],
    visible_count: int = None,
) -> None:
    """Render the range summary and page controls backed by URL parameters."""
    import streamlit as st

    current = PaginationSelection(
        page=min(selection.page, total_pages(selection.limit, total_videos)),
        limit=selection.limit,
    )
    start, end = page_bounds(current.page, current.limit, total_videos)
    if current.limit == "all":
        st.caption("All videos loaded · {} total".format(total_videos))
        return

    st.caption(
        "Videos {}–{} of {} · Page {} of {} · {} per page".format(
            start + 1 if end else 0,
            min(
                start + max(0, visible_count)
                if visible_count is not None
                else end,
                total_videos,
            ),
            total_videos,
            current.page,
            total_pages(current.limit, total_videos),
            current.limit,
        )
    )
    previous_col, page_col, next_col = st.columns((1, 2, 1))
    with previous_col:
        if st.button(
            "‹",
            help="Previous page",
            disabled=current.page <= 1,
            key="common-pagination-previous",
        ):
            query_params.update(canonical_pagination_query(
                PaginationSelection(current.page - 1, current.limit)
            ))
            st.rerun()
    with page_col:
        pages = list(range(1, total_pages(current.limit, total_videos) + 1))
        chosen_page = st.selectbox(
            "Page",
            pages,
            index=pages.index(current.page),
            key="common-pagination-page-select-{}".format(current.page),
        )
        if chosen_page != current.page:
            query_params.update(canonical_pagination_query(
                PaginationSelection(chosen_page, current.limit)
            ))
            st.rerun()
    with next_col:
        if st.button(
            "›",
            help="Next page",
            disabled=current.page >= total_pages(current.limit, total_videos),
            key="common-pagination-next",
        ):
            query_params.update(canonical_pagination_query(
                PaginationSelection(current.page + 1, current.limit)
            ))
            st.rerun()
