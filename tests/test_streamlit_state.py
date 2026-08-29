import unittest

from state.common_state import init_common_state, set_selected_video_id
from state.llm_state import (
    clear_llm_prompt,
    init_llm_state,
    set_llm_prompt,
    set_llm_selected_codes,
    sync_llm_video,
)
from state.translation_state import init_translation_state, sync_translation_video


class StreamlitStateTests(unittest.TestCase):
    def test_workflows_bind_to_one_common_video_selection(self):
        session = {}

        init_common_state(session)
        llm = init_llm_state(session)
        translation = init_translation_state(session)
        set_selected_video_id(session, "video-1")
        sync_llm_video(llm, session["common.selected_video_id"])
        sync_translation_video(translation, session["common.selected_video_id"])

        self.assertEqual(session["common.selected_video_id"], "video-1")
        self.assertEqual(session["llm"]["bound_video_id"], "video-1")
        self.assertEqual(session["translation"]["bound_video_id"], "video-1")
        self.assertNotIn("selected_video_id", session["llm"])
        self.assertNotIn("selected_video_id", session["translation"])
        self.assertNotIn("selected_video_ids", session["common.channel"] or {})

    def test_switching_llm_video_clears_prompt_and_uploaded_json(self):
        state = init_llm_state({})
        state.update(
            {
                "bound_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("de",),
                "selected_target_codes": ("de",),
                "prompt_text": "old prompt",
            }
        )
        translation = init_translation_state({})
        translation.update(
            {
                "bound_video_id": "video-1",
                "draft": {"de": {"title": "DE", "description": "DE"}},
                "local_validation": object(),
                "preview_result": object(),
                "preview_fingerprint": ("video-1", "fingerprint"),
                "published": True,
                "operation_status": "publishing",
                "operation_error": "youtube_api",
            }
        )

        sync_llm_video(state, "video-2")
        sync_translation_video(translation, "video-2")

        self.assertEqual(state["bound_video_id"], "video-2")
        self.assertIsNone(state["prompt_video_id"])
        self.assertEqual(state["prompt_target_codes"], ())
        self.assertEqual(state["prompt_text"], "")
        self.assertEqual(state["selected_target_codes"], ())
        self.assertTrue(state["scroll_to_form"])
        self.assertEqual(translation["draft"], {})
        self.assertIsNone(translation["draft_validation"])
        self.assertIsNone(translation["preview_result"])
        self.assertIsNone(translation["preview_fingerprint"])
        self.assertFalse(translation["published"])
        self.assertEqual(translation["operation_status"], "idle")
        self.assertIsNone(translation["operation_error"])

    def test_selecting_same_llm_video_keeps_current_prompt_and_form(self):
        state = init_llm_state({})
        state.update(
            {
                "bound_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("de",),
                "selected_target_codes": ("de",),
                "prompt_text": "current prompt",
                "scroll_to_form": False,
            }
        )
        translation = init_translation_state({})
        translation.update(
            {
                "bound_video_id": "video-1",
                "draft": {"de": {"title": "DE", "description": "DE"}},
            }
        )

        sync_llm_video(state, "video-1")
        sync_translation_video(translation, "video-1")

        self.assertEqual(state["prompt_video_id"], "video-1")
        self.assertEqual(state["prompt_target_codes"], ("de",))
        self.assertEqual(state["prompt_text"], "current prompt")
        self.assertEqual(
            translation["draft"], {"de": {"title": "DE", "description": "DE"}}
        )
        self.assertEqual(state["selected_target_codes"], ("de",))
        self.assertFalse(state["scroll_to_form"])

    def test_selected_codes_are_stored_only_for_current_llm_video(self):
        state = init_llm_state({})
        state["bound_video_id"] = "video-1"

        set_llm_selected_codes(state, "video-1", ["de", "fr"])

        self.assertEqual(state["selected_target_codes"], ("de", "fr"))

        set_llm_selected_codes(state, "video-2", ["es"])

        self.assertEqual(state["selected_target_codes"], ("de", "fr"))

    def test_setting_and_clearing_llm_prompt_keeps_prompt_metadata_together(self):
        state = init_llm_state({})
        state["selected_target_codes"] = ("de", "fr")
        state["consumed_upload_context"] = ("video-1", ("de",), "hash")
        state["upload_issue_context"] = ("video-1", ("de",), "invalid-hash")
        state["upload_issues"] = (object(),)

        set_llm_prompt(state, "video-1", ["de", "fr"], "translate this")

        self.assertEqual(state["prompt_video_id"], "video-1")
        self.assertEqual(state["prompt_target_codes"], ("de", "fr"))
        self.assertEqual(state["prompt_text"], "translate this")
        self.assertIsNone(state["consumed_upload_context"])
        self.assertIsNone(state["upload_issue_context"])
        self.assertEqual(state["upload_issues"], ())

        clear_llm_prompt(state)

        self.assertIsNone(state["prompt_video_id"])
        self.assertEqual(state["prompt_target_codes"], ())
        self.assertEqual(state["prompt_text"], "")
        self.assertEqual(state["selected_target_codes"], ())
        self.assertIsNone(state["consumed_upload_context"])
        self.assertIsNone(state["upload_issue_context"])
        self.assertEqual(state["upload_issues"], ())


if __name__ == "__main__":
    unittest.main()
