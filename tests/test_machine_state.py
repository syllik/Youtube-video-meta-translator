import unittest

from state.machine_state import (
    init_machine_state,
    machine_can_submit,
    reconcile_select_all_channel,
)


class MachineStateTests(unittest.TestCase):
    def test_machine_state_is_namespaced_and_disabled_without_inputs(self):
        session = {}
        state = init_machine_state(session)

        self.assertIn("machine", session)
        self.assertFalse(machine_can_submit(state))

    def test_machine_can_submit_requires_video_and_language(self):
        session = {}
        state = init_machine_state(session)
        state["selected_video_ids"] = {"video-1"}
        self.assertFalse(machine_can_submit(state))
        state["selected_language_codes"] = {"es"}
        self.assertTrue(machine_can_submit(state))
        state["operation_status"] = "running"
        self.assertFalse(machine_can_submit(state))

    def test_reconcile_select_all_channel_clears_stale_bulk_intent(self):
        state = {
            "select_all_channel": True,
            "selected_video_ids": {"video-1"},
        }

        self.assertFalse(
            reconcile_select_all_channel(state, ("video-1", "video-2"))
        )
        self.assertFalse(state["select_all_channel"])
        self.assertTrue(state["select_all_channel_reset_pending"])


if __name__ == "__main__":
    unittest.main()
