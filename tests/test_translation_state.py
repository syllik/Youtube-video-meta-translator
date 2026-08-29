import unittest
from types import SimpleNamespace

from state.translation_state import (
    init_translation_state,
    merge_translation_draft,
    store_translation_preview,
    sync_translation_video,
    translation_can_publish,
    translation_preview_is_current,
)


class TranslationStateTests(unittest.TestCase):
    def test_switching_video_clears_draft_and_preview(self):
        state = init_translation_state({})
        state.update(
            {
                "bound_video_id": "video-1",
                "target_video_id": "video-1",
                "selected_target_codes": ("de",),
                "generation_video_id": "video-1",
                "generation_completed_codes": ("de",),
                "draft": {"de": {"title": "DE", "description": "DE"}},
                "preview_result": object(),
                "preview_fingerprint": ("video-1", "fingerprint"),
                "published": True,
            }
        )

        sync_translation_video(state, "video-2")

        self.assertEqual(state["bound_video_id"], "video-2")
        self.assertEqual(state["draft"], {})
        self.assertIsNone(state["preview_result"])
        self.assertIsNone(state["preview_fingerprint"])
        self.assertFalse(state["published"])
        self.assertIsNone(state["target_video_id"])
        self.assertEqual(state["selected_target_codes"], ())
        self.assertIsNone(state["generation_video_id"])
        self.assertEqual(state["generation_completed_codes"], ())

    def test_same_video_keeps_current_draft(self):
        state = init_translation_state({})
        state.update(
            {
                "bound_video_id": "video-1",
                "draft": {"de": {"title": "DE", "description": "DE"}},
            }
        )

        sync_translation_video(state, "video-1")

        self.assertEqual(
            state["draft"], {"de": {"title": "DE", "description": "DE"}}
        )

    def test_generated_and_uploaded_entries_merge_into_one_draft(self):
        state = init_translation_state({})
        state["draft"] = {"de": {"title": "Old", "description": "Old"}}

        merge_translation_draft(
            state,
            {
                "DE": {"title": "New", "description": "New"},
                "fr": {"title": "FR", "description": "FR"},
            },
        )

        self.assertEqual(
            state["draft"],
            {
                "DE": {"title": "New", "description": "New"},
                "fr": {"title": "FR", "description": "FR"},
            },
        )

    def test_publish_requires_current_valid_preview_with_changes(self):
        state = init_translation_state({})
        state["bound_video_id"] = "video-1"
        state["draft"] = {"de": {"title": "DE", "description": "DE"}}
        result = SimpleNamespace(
            plan=SimpleNamespace(is_valid=True, has_changes=True)
        )

        store_translation_preview(state, result)

        self.assertTrue(translation_preview_is_current(state))
        self.assertTrue(translation_can_publish(state))

        state["draft"]["de"]["title"] = "Changed after preview"

        self.assertFalse(translation_preview_is_current(state))
        self.assertFalse(translation_can_publish(state))

    def test_merging_a_new_draft_entry_invalidates_preview(self):
        state = init_translation_state({})
        state["bound_video_id"] = "video-1"
        state["draft"] = {"de": {"title": "DE", "description": "DE"}}
        result = SimpleNamespace(
            plan=SimpleNamespace(is_valid=True, has_changes=True)
        )
        store_translation_preview(state, result)

        merge_translation_draft(
            state,
            {"fr": {"title": "FR", "description": "FR"}},
        )

        self.assertIsNone(state["preview_result"])
        self.assertFalse(translation_preview_is_current(state))
        self.assertFalse(translation_can_publish(state))


if __name__ == "__main__":
    unittest.main()
