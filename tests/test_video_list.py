import unittest
from unittest.mock import patch

from models import VideoSummary
from state.llm_state import init_llm_state
from state.manual_state import init_manual_state
from ui.video_list import (
    MACHINE_SELECT_ALL_CHANNEL_KEY,
    MACHINE_SELECT_ALL_ROW_CHANGE_KEY,
    checkbox_widget_kwargs,
    render_video_list,
    stateful_checkbox_kwargs,
    sync_visible_checkbox_state,
    visible_selected_video_ids,
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

    def test_machine_widget_key_remains_stable(self):
        self.assertEqual(widget_key("machine", "video-42"), "machine-video-video-42")

    def test_machine_widget_helpers_remain_public_and_preserve_bulk_selection(self):
        widget_state = {}

        sync_visible_checkbox_state(
            widget_state, ("video-1", "video-2"), {"video-2"}
        )

        self.assertEqual(MACHINE_SELECT_ALL_CHANNEL_KEY, "machine-select-all-channel")
        self.assertEqual(
            MACHINE_SELECT_ALL_ROW_CHANGE_KEY, "machine-select-all-row-change"
        )
        self.assertFalse(widget_state[widget_key("machine", "video-1")])
        self.assertTrue(widget_state[widget_key("machine", "video-2")])
        self.assertEqual(
            visible_selected_video_ids(
                ("video-1", "video-2"), {"video-2", "video-99"}
            ),
            {"video-2"},
        )
        self.assertNotIn(
            "value", checkbox_widget_kwargs({widget_key("machine", "video-1"): True}, "video-1", set())
        )
        self.assertNotIn(
            "value",
            stateful_checkbox_kwargs(
                {"channel-select-all": True},
                "channel-select-all",
                "Select all channel videos",
                False,
            ),
        )

    def test_machine_selection_supports_the_legacy_four_argument_contract(self):
        streamlit = _FakeStreamlit("not-clicked")
        video = VideoSummary(
            id="video-1",
            title="First video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            selection = render_video_list(
                (video,), "machine", {"selected_video_ids": {"video-1"}}, {}
            )

        self.assertEqual(selection.selected_video_ids, ("video-1",))

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
        self.assertTrue(state["scroll_to_prompt"])

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
