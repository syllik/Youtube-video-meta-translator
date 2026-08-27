import unittest

from ui.video_list import (
    checkbox_widget_kwargs,
    stateful_checkbox_kwargs,
    sync_visible_checkbox_state,
    visible_selected_video_ids,
    widget_key,
)


class VideoListTests(unittest.TestCase):
    def test_widget_keys_are_stable_by_mode_and_video_id(self):
        self.assertEqual(widget_key("machine", "video-42"), "machine-video-video-42")
        self.assertEqual(widget_key("manual", "video-42"), "manual-video-video-42")
        self.assertNotEqual(
            widget_key("machine", "video-42"), widget_key("manual", "video-42")
        )

    def test_visible_checkbox_widgets_follow_bulk_selection_state(self):
        widget_state = {}

        sync_visible_checkbox_state(
            widget_state, ("video-1", "video-2"), {"video-2"}
        )

        self.assertFalse(widget_state[widget_key("machine", "video-1")])
        self.assertTrue(widget_state[widget_key("machine", "video-2")])

    def test_visible_selection_only_contains_ids_from_the_current_page(self):
        self.assertEqual(
            visible_selected_video_ids(
                ("video-1", "video-2"), {"video-2", "video-99"}
            ),
            {"video-2"},
        )

    def test_existing_checkbox_state_is_not_combined_with_a_default_value(self):
        key = widget_key("machine", "video-1")

        self.assertNotIn(
            "value", checkbox_widget_kwargs({key: True}, "video-1", set())
        )
        self.assertFalse(checkbox_widget_kwargs({}, "video-1", set())["value"])

    def test_generic_checkbox_state_is_not_combined_with_a_default_value(self):
        self.assertNotIn(
            "value",
            stateful_checkbox_kwargs(
                {"channel-select-all": True},
                "channel-select-all",
                "Select all channel videos",
                False,
            ),
        )


if __name__ == "__main__":
    unittest.main()
