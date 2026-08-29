import inspect
import unittest
from types import SimpleNamespace

from models import ChannelInfo, VideoSummary, YouTubePage
from ui.pagination import PaginationSelection
from ui.sidebar import _consume_pending_reset, render_app_sidebar
from ui.video_list import render_video_list, widget_key


class _Block:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self, clicked_key=None):
        self.clicked_key = clicked_key
        self.sidebar = _Block()
        self.calls = []

    def container(self, **kwargs):
        self.calls.append(("container", kwargs))
        return _Block()

    def columns(self, spec):
        self.calls.append(("columns", spec))
        return tuple(_Block() for _ in spec)

    def markdown(self, value, **kwargs):
        self.calls.append(("markdown", value, kwargs))

    def caption(self, value, **kwargs):
        self.calls.append(("caption", value, kwargs))

    def subheader(self, value, **kwargs):
        self.calls.append(("subheader", value, kwargs))

    def button(self, label, **kwargs):
        self.calls.append(("button", label, kwargs))
        return kwargs.get("key") == self.clicked_key

    def selectbox(self, label, options, **kwargs):
        self.calls.append(("selectbox", label, tuple(options), kwargs))
        return options[kwargs.get("index", 0)]

    def rerun(self):
        self.calls.append(("rerun",))

    def spinner(self, message):
        self.calls.append(("spinner", message))
        return _Block()

    def success(self, message):
        self.calls.append(("success", message))

    def error(self, message):
        self.calls.append(("error", message))


class SidebarTests(unittest.TestCase):
    def setUp(self):
        self.context = SimpleNamespace(
            channel=ChannelInfo(
                id="channel-1",
                name="My channel",
                description="A channel description",
                thumbnail_url="https://img.test/channel.jpg",
                total_videos=42,
            ),
            page=YouTubePage(
                videos=(
                    VideoSummary(
                        id="video-1",
                        title="First video",
                        description="First description",
                        thumbnail_url="https://img.test/video.jpg",
                        current_language_codes=("de", "fr"),
                        default_language_code="en",
                    ),
                ),
                next_page_token=None,
            ),
            selection=PaginationSelection(page=1, limit=10),
            metadata_language_catalog=SimpleNamespace(
                codes=("en", "de", "fr"),
            ),
        )

    def test_sidebar_renders_channel_controls_links_and_video_card(self):
        import sys
        from unittest.mock import patch

        fake = _FakeStreamlit()
        with patch.dict(sys.modules, {"streamlit": fake}):
            render_app_sidebar(self.context, {}, {})

        text = "\n".join(
            call[1]
            for call in fake.calls
            if call[0] in {"markdown", "caption", "subheader"}
        )
        self.assertIn("My channel", text)
        self.assertIn("A channel description", text)
        self.assertIn("channel-1", text)
        self.assertIn("42", text)
        self.assertIn("https://www.youtube.com/channel/channel-1", text)
        self.assertIn(
            "https://www.youtube.com/feeds/videos.xml?channel_id=channel-1",
            text,
        )
        self.assertIn("First video", text)
        self.assertIn("video-1", text)
        self.assertIn("Default language: en", text)
        self.assertIn("Localizations: 2 / 0", text)
        self.assertNotIn("First description", text)
        self.assertNotIn("Open " + "on YouTube", text)
        refresh_calls = [
            call for call in fake.calls
            if call[0] == "button" and call[1] == "Refresh video list"
        ]
        self.assertEqual(len(refresh_calls), 1)
        self.assertTrue(refresh_calls[0][2]["use_container_width"])
        self.assertTrue(
            any(
                call[0] == "selectbox" and call[1] == "Videos per page"
                for call in fake.calls
            )
        )
        self.assertTrue(
            any(call[0] == "selectbox" and call[1] == "Page" for call in fake.calls)
        )

    def test_selecting_sidebar_video_updates_common_state(self):
        import sys
        from unittest.mock import patch

        self.context.page = YouTubePage(
            videos=(
                self.context.page.videos[0],
                VideoSummary("video-2", "Second", "", "", ()),
            ),
            next_page_token=None,
        )
        state = {}
        fake = _FakeStreamlit(clicked_key=widget_key("video-2"))
        with patch.dict(sys.modules, {"streamlit": fake}):
            render_app_sidebar(self.context, state, {})

        self.assertEqual(state["common.selected_video_id"], "video-2")

    def test_video_list_has_workflow_agnostic_contract(self):
        parameters = inspect.signature(render_video_list).parameters

        self.assertEqual(tuple(parameters)[:2], ("videos", "session_state"))
        self.assertEqual(widget_key("video-42"), "common-video-video-42")

    def test_sidebar_contract_contains_load_more_after_video_cards(self):
        from pathlib import Path

        source = Path("ui/sidebar.py").read_text()

        self.assertIn("Load more", source)
        self.assertIn("load_more_video_page", source)
        self.assertIn(
            "window.confirm",
            Path("ui/reset_video_component/index.html").read_text(),
        )

    def test_confirmed_reset_targets_card_id_and_invalidates_sidebar_state(self):
        import sys
        from unittest.mock import Mock, patch

        reset = Mock()
        context = SimpleNamespace(
            service=SimpleNamespace(
                reset_video_localizations=reset,
                supported_language_codes=lambda: (),
            ),
            metadata_language_catalog=SimpleNamespace(codes=("en", "de")),
            page=self.context.page,
        )
        state = {
            "common.selected_video_id": "video-1",
            "common.source_video_id": "video-1",
            "common.selected_source_codes": ("en", "de"),
            "common.page_tokens_by_limit": {10: {2: "token"}},
            "common.video_pages_by_limit": {10: {1: self.context.page}},
            "common.video_accumulation": {"page": 1, "limit": 10, "through_page": 1},
            "common.pending_reset_video_id": "video-1",
            "translation": {
                "bound_video_id": "video-1",
                "draft": {"de": {"title": "DE", "description": "DE"}},
                "preview_result": object(),
            },
            "llm": {
                "bound_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("fr",),
                "selected_target_codes": ("fr",),
                "prompt_text": "translate",
            },
        }
        query_params = {"page": "1", "limit": "10"}
        fake = _FakeStreamlit()

        with patch.dict(sys.modules, {"streamlit": fake}):
            handled = _consume_pending_reset(context, state)

        self.assertTrue(handled)
        reset.assert_called_once_with("video-1")
        self.assertEqual(state["common.page_tokens_by_limit"], {})
        self.assertEqual(state["common.video_pages_by_limit"], {})
        self.assertIsNone(state["common.source_video_id"])
        self.assertEqual(state["common.selected_source_codes"], ())
        self.assertEqual(state["translation"]["draft"], {})
        self.assertIsNone(state["translation"]["preview_result"])
        self.assertIsNone(state["llm"]["prompt_video_id"])
        self.assertEqual(state["llm"]["prompt_text"], "")
        self.assertEqual(query_params, {"page": "1", "limit": "10"})


if __name__ == "__main__":
    unittest.main()
