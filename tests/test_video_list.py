import inspect
import unittest
from unittest.mock import patch

from models import VideoSummary
from state.common_state import init_common_state
from ui.video_list import render_video_list, widget_key


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self, clicked_key):
        self.clicked_key = clicked_key
        self.session_state = {}

    def columns(self, spec):
        return tuple(_Column() for _ in spec)

    def container(self, **_kwargs):
        return _Column()

    def button(self, _label, **kwargs):
        return kwargs["key"] == self.clicked_key

    def rerun(self):
        pass

    def markdown(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass


class VideoListTests(unittest.TestCase):
    def test_widget_keys_are_stable_by_video_id(self):
        self.assertEqual(widget_key("video-42"), "common-video-video-42")

    def test_video_list_has_workflow_agnostic_contract(self):
        self.assertEqual(
            tuple(inspect.signature(render_video_list).parameters),
            ("videos", "session_state"),
        )

    def test_selected_common_video_is_reported(self):
        state = {}
        init_common_state(state)
        state["common.selected_video_id"] = "video-1"
        streamlit = _FakeStreamlit("not-clicked")
        video = VideoSummary(
            id="video-1",
            title="First video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            selection = render_video_list((video,), state)

        self.assertEqual(selection, "video-1")

    def test_selection_writes_only_common_state(self):
        state = {}
        streamlit = _FakeStreamlit(widget_key("video-2"))
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            render_video_list((video,), state)

        self.assertEqual(state["common.selected_video_id"], "video-2")
        self.assertNotIn("manual", state)
        self.assertNotIn("llm", state)


if __name__ == "__main__":
    unittest.main()
