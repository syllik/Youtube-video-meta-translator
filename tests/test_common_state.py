from unittest.mock import Mock

from models import YouTubePage, VideoSummary
from state.common_state import load_video_page, reset_video_cache
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
        "manual.selected_video_id": "video-1",
    }

    reset_video_cache(state)

    assert state["common.page_tokens_by_limit"] == {}
    assert state["common.video_pages_by_limit"] == {}
    assert state["manual.selected_video_id"] == "video-1"
