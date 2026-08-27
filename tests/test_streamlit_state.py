import unittest

from state.common_state import init_common_state
from state.llm_state import (
    clear_llm_prompt,
    init_llm_state,
    set_llm_prompt,
    set_llm_video,
)
from state.manual_state import init_manual_state


class StreamlitStateTests(unittest.TestCase):
    def test_mode_state_is_separate_from_common_state(self):
        session = {}

        init_common_state(session)
        llm = init_llm_state(session)
        manual = init_manual_state(session)
        llm["selected_video_id"] = "video-1"
        manual["selected_video_id"] = "video-2"

        self.assertEqual(session["llm"]["selected_video_id"], "video-1")
        self.assertEqual(session["manual"]["selected_video_id"], "video-2")
        self.assertNotIn("selected_video_ids", session["common.channel"] or {})

    def test_switching_llm_video_clears_prompt_and_uploaded_json(self):
        state = init_llm_state({})
        preview = object()
        state.update(
            {
                "selected_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("de",),
                "prompt_text": "old prompt",
                "raw_json": '{"de": {}}',
                "local_validation": object(),
                "preview_result": preview,
                "preview_fingerprint": ("video-1", "fingerprint"),
                "published": True,
                "operation_status": "idle",
                "operation_error": "openai",
            }
        )

        set_llm_video(state, "video-2")

        self.assertEqual(state["selected_video_id"], "video-2")
        self.assertIsNone(state["prompt_video_id"])
        self.assertEqual(state["prompt_target_codes"], ())
        self.assertEqual(state["prompt_text"], "")
        self.assertEqual(state["raw_json"], "")
        self.assertIsNone(state["local_validation"])
        self.assertIsNone(state["preview_result"])
        self.assertIsNone(state["preview_fingerprint"])
        self.assertFalse(state["published"])
        self.assertEqual(state["operation_status"], "idle")
        self.assertIsNone(state["operation_error"])
        self.assertTrue(state["scroll_to_prompt"])

    def test_selecting_same_llm_video_keeps_current_prompt_and_form(self):
        state = init_llm_state({})
        state.update(
            {
                "selected_video_id": "video-1",
                "prompt_video_id": "video-1",
                "prompt_target_codes": ("de",),
                "prompt_text": "current prompt",
                "raw_json": '{"de": {}}',
                "scroll_to_prompt": False,
            }
        )

        set_llm_video(state, "video-1")

        self.assertEqual(state["prompt_video_id"], "video-1")
        self.assertEqual(state["prompt_target_codes"], ("de",))
        self.assertEqual(state["prompt_text"], "current prompt")
        self.assertEqual(state["raw_json"], '{"de": {}}')
        self.assertFalse(state["scroll_to_prompt"])

    def test_setting_and_clearing_llm_prompt_keeps_prompt_metadata_together(self):
        state = init_llm_state({})

        set_llm_prompt(state, "video-1", ["de", "fr"], "translate this")

        self.assertEqual(state["prompt_video_id"], "video-1")
        self.assertEqual(state["prompt_target_codes"], ("de", "fr"))
        self.assertEqual(state["prompt_text"], "translate this")

        clear_llm_prompt(state)

        self.assertIsNone(state["prompt_video_id"])
        self.assertEqual(state["prompt_target_codes"], ())
        self.assertEqual(state["prompt_text"], "")


if __name__ == "__main__":
    unittest.main()
