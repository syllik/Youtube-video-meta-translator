import unittest

from state.machine_state import init_machine_state, machine_can_submit


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


if __name__ == "__main__":
    unittest.main()
