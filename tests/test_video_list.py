import inspect
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

from models import VideoSummary
from state.common_state import init_common_state
from ui.video_list import render_video_list, video_localization_counts, widget_key


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class _FakeStreamlit:
    def __init__(self, clicked_key):
        self.clicked_key = clicked_key
        self.session_state = {}
        self.button_calls = []
        self.columns_calls = []
        self.markdown_calls = []

    def columns(self, spec):
        self.columns_calls.append(spec)
        return tuple(_Column() for _ in spec)

    def container(self, **_kwargs):
        return _Column()

    def button(self, _label, **kwargs):
        self.button_calls.append(kwargs)
        return kwargs["key"] == self.clicked_key

    def rerun(self):
        pass

    def markdown(self, *_args, **_kwargs):
        self.markdown_calls.append((_args, _kwargs))

    def caption(self, *_args, **_kwargs):
        pass


class VideoListTests(unittest.TestCase):
    def test_localization_counts_exclude_default_and_use_live_catalog(self):
        video = VideoSummary(
            id="video-1",
            title="Video",
            description="",
            thumbnail_url="",
            current_language_codes=("en", "de"),
            default_language_code="en",
        )

        self.assertEqual(
            video_localization_counts(video, ("en", "de", "fr", "ja")),
            (1, 2),
        )

    def test_localization_counts_do_not_count_out_of_catalog_existing_codes(self):
        video = VideoSummary(
            id="video-1",
            title="Video",
            description="",
            thumbnail_url="",
            current_language_codes=("en", "de", "xx"),
            default_language_code="en",
        )

        self.assertEqual(
            video_localization_counts(video, ("en", "de", "fr")),
            (1, 1),
        )

    def test_widget_keys_are_stable_by_video_id(self):
        self.assertEqual(widget_key("video-42"), "common-video-video-42")

    def test_video_list_has_workflow_agnostic_contract(self):
        parameters = tuple(inspect.signature(render_video_list).parameters)
        self.assertEqual(parameters[:2], ("videos", "session_state"))
        self.assertIn("supported_language_codes", parameters)

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

    def test_select_button_is_below_details_and_full_width(self):
        state = {}
        streamlit = _FakeStreamlit("not-clicked")
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            render_video_list((video,), state)

        self.assertEqual(streamlit.columns_calls, [])
        self.assertEqual(len(streamlit.button_calls), 1)
        self.assertTrue(streamlit.button_calls[0]["use_container_width"])

    def test_video_cards_show_compact_live_catalog_metadata_and_reset(self):
        state = {}
        streamlit = _FakeStreamlit("not-clicked")
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="This description must not render",
            thumbnail_url="",
            current_language_codes=("en", "de"),
            default_language_code="en",
        )

        with patch.dict("sys.modules", {"streamlit": streamlit}):
            render_video_list(
                (video,),
                state,
                supported_language_codes=("en", "de", "fr", "ja"),
            )

        text = "\n".join(args[0] for args, _kwargs in streamlit.markdown_calls)
        self.assertIn("Default language: en", text)
        self.assertIn("Localizations: 1 / 2", text)
        self.assertIn("Video ID: video-2", text)
        self.assertNotIn("This description must not render", text)
        self.assertNotIn("localization-badge", text)

    def test_confirmed_reset_uses_a_component_event_without_url_navigation(self):
        state = {}
        streamlit = _FakeStreamlit("not-clicked")
        render_reset_button = Mock(return_value="event-1")
        reset_control = SimpleNamespace(
            render_reset_button=render_reset_button,
            reset_widget_key=lambda video_id: "common-reset-{}".format(video_id),
        )
        video = VideoSummary(
            id="video-2",
            title="Second video",
            description="",
            thumbnail_url="",
            current_language_codes=(),
        )

        with patch.dict(
            "sys.modules",
            {"streamlit": streamlit, "ui.reset_control": reset_control},
        ):
            render_video_list(
                (video,),
                state,
            )

        render_reset_button.assert_called_once_with(
            "video-2",
            ANY,
            key="common-reset-video-2",
        )
        self.assertNotIn("reset_video=", Path("ui/video_list.py").read_text())
        self.assertEqual(state.get("common.pending_reset_video_id"), "video-2")

    def test_reset_component_confirms_in_browser_and_does_not_navigate(self):
        source = Path("ui/reset_video_component/index.html").read_text()

        self.assertIn("window.confirm", source)
        self.assertIn("streamlit:setComponentValue", source)
        self.assertNotIn("window.location", source)
        self.assertNotIn("href=", source)


if __name__ == "__main__":
    unittest.main()
