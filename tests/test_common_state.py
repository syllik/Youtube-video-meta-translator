from unittest.mock import Mock

from models import YouTubePage, VideoSummary
from state.common_state import (
    get_selected_video_id,
    init_common_state,
    can_load_more,
    load_accumulated_video_page,
    load_more_video_page,
    load_video_page,
    sync_source_selection,
    reset_video_cache,
    set_source_selection,
    set_selected_video_id,
)
from ui.pagination import PaginationSelection


def test_page_three_walks_from_the_nearest_known_token():
    service = Mock()
    service.fetch_video_page.side_effect = [
        YouTubePage((VideoSummary("1", "One", "", "", ()),), "token-2"),
        YouTubePage((VideoSummary("2", "Two", "", "", ()),), "token-3"),
        YouTubePage((VideoSummary("3", "Three", "", "", ()),), None),
    ]
    state = {}

    page = load_video_page(service, state, PaginationSelection(3, 10))

    assert page.videos[0].id == "3"
    assert service.fetch_video_page.call_count == 3


def test_reset_clears_tokens_and_pages_only():
    state = {
        "common.page_tokens_by_limit": {10: {2: "token-2"}},
        "common.video_pages_by_limit": {10: {1: object()}},
        "common.selected_video_id": "video-1",
    }

    reset_video_cache(state)

    assert state["common.page_tokens_by_limit"] == {}
    assert state["common.video_pages_by_limit"] == {}
    assert state["common.selected_video_id"] == "video-1"


def test_common_video_selection_initializes_to_none():
    state = {}

    init_common_state(state)

    assert get_selected_video_id(state) is None


def test_setting_common_video_selection_reports_only_real_changes():
    state = {}

    assert set_selected_video_id(state, "video-1") is True
    assert get_selected_video_id(state) == "video-1"
    assert set_selected_video_id(state, "video-1") is False


def test_common_video_selection_survives_video_cache_reset():
    state = {}
    init_common_state(state)
    set_selected_video_id(state, "video-1")

    reset_video_cache(state)

    assert state["common.selected_video_id"] == "video-1"


def test_source_selection_defaults_to_primary_and_resets_for_new_video():
    state = {}

    assert sync_source_selection(state, "video-a", "en", ("en", "ru")) == ("en",)
    state["common.selected_source_codes"] = ("en", "ru")

    assert sync_source_selection(state, "video-a", "en", ("en", "ru")) == (
        "en",
        "ru",
    )
    assert sync_source_selection(state, "video-b", "de", ("de", "fr")) == ("de",)
    assert state["common.source_video_id"] == "video-b"


def test_source_selection_cannot_remove_required_primary_source():
    state = {}

    selected = set_source_selection(
        state, "video-a", ("ru",), "en", ("en", "ru")
    )

    assert selected == ("en", "ru")
    assert state["common.selected_source_codes"] == ("en", "ru")


def test_empty_source_multiselect_clears_old_references_but_keeps_primary():
    state = {"common.source_video_id": "video-a", "common.selected_source_codes": ("en", "ru")}

    selected = set_source_selection(
        state, "video-a", (), "en", ("en", "ru")
    )

    assert selected == ("en",)


def test_load_more_appends_cursor_pages_once_without_duplicates():
    service = Mock()
    service.fetch_video_page.side_effect = [
        YouTubePage(
            (VideoSummary("1", "One", "", "", ()),),
            "token-2",
        ),
        YouTubePage(
            (VideoSummary("2", "Two", "", "", ()),),
            "token-3",
        ),
        YouTubePage(
            (VideoSummary("3", "Three", "", "", ()),),
            None,
        ),
    ]
    state = {}
    selection = PaginationSelection(1, 10)

    first = load_accumulated_video_page(service, state, selection)
    second = load_more_video_page(service, state, selection)
    repeated = load_more_video_page(service, state, selection)

    assert [video.id for video in first.videos] == ["1"]
    assert [video.id for video in second.videos] == ["1", "2"]
    assert [video.id for video in repeated.videos] == ["1", "2", "3"]
    assert [video.id for video in load_more_video_page(service, state, selection).videos] == [
        "1",
        "2",
        "3",
    ]
    assert service.fetch_video_page.call_count == 3


def test_page_navigation_starts_accumulation_from_selected_page():
    service = Mock()
    service.fetch_video_page.side_effect = [
        YouTubePage((VideoSummary("1", "One", "", "", ()),), "token-2"),
        YouTubePage((VideoSummary("2", "Two", "", "", ()),), "token-3"),
        YouTubePage((VideoSummary("3", "Three", "", "", ()),), None),
    ]
    state = {}
    load_accumulated_video_page(service, state, PaginationSelection(1, 10))
    load_more_video_page(service, state, PaginationSelection(1, 10))

    page_two = load_accumulated_video_page(service, state, PaginationSelection(2, 10))
    page_two_more = load_more_video_page(service, state, PaginationSelection(2, 10))

    assert [video.id for video in page_two.videos] == ["2"]
    assert [video.id for video in page_two_more.videos] == ["2", "3"]


def test_all_limit_never_exposes_load_more():
    state = {}

    assert not can_load_more(state, PaginationSelection(1, "all"), 100)
