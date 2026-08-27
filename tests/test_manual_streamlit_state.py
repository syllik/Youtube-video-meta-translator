import unittest
from types import SimpleNamespace

from state.manual_state import (
    manual_can_publish,
    manual_fingerprint,
    manual_preview_is_current,
    set_manual_json,
    set_manual_video,
)


class ManualStateTests(unittest.TestCase):
    def test_switching_video_invalidates_preview(self):
        state = {
            "selected_video_id": "video-1",
            "raw_json": '{"es": {"title": "A", "description": "B"}}',
            "preview_fingerprint": ("video-1", "hash-1"),
            "preview_result": object(),
        }

        set_manual_video(state, "video-2")

        self.assertIsNone(state["preview_result"])
        self.assertFalse(manual_preview_is_current(state))
        self.assertFalse(manual_can_publish(state))

    def test_json_change_invalidates_preview_even_for_same_video(self):
        state = {
            "selected_video_id": "video-1",
            "raw_json": "old",
            "preview_fingerprint": ("video-1", "old-hash"),
            "preview_result": object(),
        }

        set_manual_json(state, "new")

        self.assertIsNone(state["preview_result"])
        self.assertFalse(manual_can_publish(state))

    def test_published_preview_cannot_be_submitted_again(self):
        state = {
            "selected_video_id": "video-1",
            "raw_json": "new",
            "preview_fingerprint": manual_fingerprint("video-1", "new"),
            "preview_result": SimpleNamespace(
                plan=SimpleNamespace(is_valid=True, has_changes=True)
            ),
            "published": True,
        }

        self.assertFalse(manual_can_publish(state))


if __name__ == "__main__":
    unittest.main()
