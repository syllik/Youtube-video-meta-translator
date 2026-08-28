import unittest
from unittest.mock import patch

from models import VideoSummary
from state.llm_state import init_llm_state
from state.manual_state import init_manual_state
from ui.video_list import (
    render_video_list,
    widget_key,
)


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self, clicked_key):
        self.clicked_key = clicked_key
        self.session_state = {}

    def columns(self, _spec):
        return _Column(), _Column()

    def container(self):
        return _Column()

    def button(self, _label, **kwargs):
        return kwargs["key"] == self.clicked_key

    def checkbox(self, **kwargs):
        return self.session_state.get(kwargs["key"], kwargs.get("value", False))

    def rerun(self):
        pass

    def image(self, *_args, **_kwargs):
        pass

    def markdown(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass


class VideoListTests(unittest.TestCase):
    def test_widget_keys_are_stable_by_mode_and_video_id(self):
        self.assertEqual(widget_key("manual", "video-42"), "manual-video-video-42")
        self.assertEqual(widget_key("llm", "video-42"), "llm-video-video-42")
        self.assertNotEqual(
            widget_key("llm", "video-42"), widget_key("manual", "video-42")
        )

    def test_removed_video_list_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            widget_key("ma" + "chine", "video-42")

    def test_manual_selection_supports_legacy_four_argument_contract_and_result(self):
        state = init_manual_state({})
        state["selected_video_id"] = "video-1"
        streamlit = _FakeStreamlit("not-clicked")
        video = VideoSummary(
            id="video-1",
            title="First video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            selection = render_video_list((video,), "manual", {}, state)

        self.assertEqual(selection.selected_manual_video_id, "video-1")

    def test_llm_selection_uses_llm_state_reset_instead_of_manual_state(self):
        state = init_llm_state({})
        state.update(
            {
                "selected_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("de",),
                "prompt_text": "old prompt",
                "raw_json": '{"de": {}}',
            }
        )
        streamlit = _FakeStreamlit(widget_key("llm", "video-2"))
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            render_video_list((video,), "llm", state)

        self.assertEqual(state["selected_video_id"], "video-2")
        self.assertEqual(state["prompt_target_codes"], ())
        self.assertEqual(state["raw_json"], "")
        self.assertTrue(state["scroll_to_form"])

    def test_manual_selection_keeps_manual_form_contents(self):
        state = init_manual_state({})
        state.update(
            {
                "selected_video_id": "video-1",
                "raw_json": '{"de": {}}',
                "preview_result": object(),
            }
        )
        streamlit = _FakeStreamlit(widget_key("manual", "video-2"))
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            render_video_list((video,), "manual", state)

        self.assertEqual(state["selected_video_id"], "video-2")
        self.assertEqual(state["raw_json"], '{"de": {}}')
        self.assertIsNone(state["preview_result"])


if __name__ == "__main__":
    unittest.main()
