import inspect
import unittest
from types import SimpleNamespace

from models import ChannelInfo, VideoSummary, YouTubePage
from ui.pagination import PaginationSelection
from ui.sidebar import render_app_sidebar
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
        self.assertIn("localization-badge", text)
        self.assertNotIn("Open on YouTube", text)
        self.assertTrue(
            any(
                call[0] == "button" and call[1] == "Refresh list"
                for call in fake.calls
            )
        )
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

        self.assertEqual(tuple(parameters), ("videos", "session_state"))
        self.assertEqual(widget_key("video-42"), "common-video-video-42")


if __name__ == "__main__":
    unittest.main()
