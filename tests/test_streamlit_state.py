import unittest

from state.common_state import init_common_state
from state.machine_state import init_machine_state
from state.manual_state import init_manual_state


class StreamlitStateTests(unittest.TestCase):
    def test_mode_state_is_separate_from_common_state(self):
        session = {}

        init_common_state(session)
        machine = init_machine_state(session)
        manual = init_manual_state(session)
        machine["selected_video_ids"].add("video-1")
        manual["selected_video_id"] = "video-2"

        self.assertEqual(session["machine"]["selected_video_ids"], {"video-1"})
        self.assertEqual(session["manual"]["selected_video_id"], "video-2")
        self.assertNotIn("selected_video_ids", session["common.channel"] or {})


if __name__ == "__main__":
    unittest.main()
