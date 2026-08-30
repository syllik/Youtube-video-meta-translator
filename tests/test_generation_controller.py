import threading
import time
import unittest

from generation_controller import GenerationController


class GenerationControllerTests(unittest.TestCase):
    VIDEO = {
        "id": "video-1",
        "snippet": {"defaultLanguage": "en", "title": "Title", "description": "Text"},
        "localizations": {},
    }
    CATALOG = object()

    def _wait_for_terminal(self, controller, owner, job_id):
        deadline = time.monotonic() + 2
        events = []
        snapshot = None
        while time.monotonic() < deadline:
            snapshot, new_events = controller.poll(owner, job_id)
            events.extend(new_events)
            if snapshot is not None and snapshot.status in {"completed", "failed", "stopped"}:
                return snapshot, events
            time.sleep(0.005)
        self.fail("generation controller did not reach a terminal state")

    def test_duplicate_start_does_not_create_second_job(self):
        started = threading.Event()
        release = threading.Event()
        calls = []

        def generator(video, catalog, **kwargs):
            calls.append(tuple(kwargs["target_codes"]))
            started.set()
            release.wait(1)
            codes = tuple(kwargs["target_codes"])
            kwargs["on_batch"](1, 1, codes)
            document = {
                code: {"title": code, "description": code} for code in codes
            }
            kwargs["on_batch_completed"](1, 1, codes, document, document)
            return document

        controller = GenerationController(
            generator=generator,
            login_checker=lambda _cancel_event: None,
            runner=lambda _package, _schema, _cancel_event: {},
        )
        first = controller.start("owner-1", self.VIDEO, self.CATALOG, ("de",))
        self.assertTrue(started.wait(1))
        with self.assertRaises(controller.DuplicateGenerationError):
            controller.start("owner-1", self.VIDEO, self.CATALOG, ("fr",))
        release.set()
        snapshot, _events = self._wait_for_terminal(controller, "owner-1", first.job_id)

        self.assertEqual(snapshot.status, "completed")
        self.assertEqual(calls, [("de",)])

    def test_one_job_reports_stable_total_and_unique_completed_batches(self):
        codes = tuple("code-{}".format(index) for index in range(25))

        def generator(video, catalog, **kwargs):
            for index, start in enumerate(range(0, len(codes), 10), start=1):
                batch_codes = codes[start:start + 10]
                kwargs["on_batch"](index, 3, batch_codes)
                document = {
                    code: {"title": code, "description": code}
                    for code in batch_codes
                }
                kwargs["on_batch_completed"](
                    index, 3, batch_codes, document, document
                )
            return {}

        controller = GenerationController(
            generator=generator,
            login_checker=lambda _cancel_event: None,
            runner=lambda _package, _schema, _cancel_event: {},
        )
        first = controller.start("owner-2", self.VIDEO, self.CATALOG, codes)
        snapshot, events = self._wait_for_terminal(controller, "owner-2", first.job_id)

        completed = [event for event in events if event.kind == "batch_completed"]
        self.assertEqual(snapshot.status, "completed")
        self.assertEqual([(event.index, event.total) for event in completed], [(1, 3), (2, 3), (3, 3)])
        scheduled = tuple(code for event in completed for code in event.codes)
        self.assertEqual(scheduled, codes)
        self.assertEqual(len(scheduled), len(set(code.casefold() for code in scheduled)))

    def test_nine_batch_job_keeps_job_local_total_at_nine(self):
        codes = tuple("code-{}".format(index) for index in range(85))
        reported = []

        def generator(video, catalog, **kwargs):
            for index, start in enumerate(range(0, len(codes), 10), start=1):
                batch_codes = codes[start:start + 10]
                kwargs["on_batch"](index, 9, batch_codes)
                reported.append((index, 9))
                document = {
                    code: {"title": code, "description": code}
                    for code in batch_codes
                }
                kwargs["on_batch_completed"](
                    index, 9, batch_codes, document, document
                )

        controller = GenerationController(
            generator=generator,
            login_checker=lambda _cancel_event: None,
            runner=lambda _package, _schema, _cancel_event: {},
        )
        first = controller.start("owner-5", self.VIDEO, self.CATALOG, codes)
        snapshot, _events = self._wait_for_terminal(controller, "owner-5", first.job_id)

        self.assertEqual(reported, [(index, 9) for index in range(1, 10)])
        self.assertEqual(snapshot.current_batch_index, 9)
        self.assertEqual(snapshot.total_batches, 9)

    def test_stop_preserves_completed_event_and_discards_active_batch(self):
        first_batch = threading.Event()
        second_batch_started = threading.Event()

        def generator(video, catalog, **kwargs):
            kwargs["on_batch"](1, 2, ("de",))
            document = {"de": {"title": "DE", "description": "DE"}}
            kwargs["on_batch_completed"](1, 2, ("de",), document, document)
            first_batch.set()
            second_batch_started.wait(1)
            kwargs["on_batch"](2, 2, ("fr",))
            return {}

        controller = GenerationController(
            generator=generator,
            login_checker=lambda _cancel_event: None,
            runner=lambda _package, _schema, _cancel_event: {},
        )
        first = controller.start("owner-3", self.VIDEO, self.CATALOG, ("de", "fr"))
        self.assertTrue(first_batch.wait(1))
        self.assertTrue(controller.stop("owner-3", first.job_id))
        second_batch_started.set()
        snapshot, events = self._wait_for_terminal(controller, "owner-3", first.job_id)

        self.assertEqual(snapshot.status, "stopped")
        self.assertEqual([event.codes for event in events if event.kind == "batch_completed"], [("de",)])
        self.assertFalse(any(event.codes == ("fr",) for event in events if event.kind == "batch_completed"))

    def test_late_batch_failure_keeps_completed_event_and_finishes_failed(self):
        def generator(video, catalog, **kwargs):
            kwargs["on_batch"](1, 2, ("de",))
            document = {"de": {"title": "DE", "description": "DE"}}
            kwargs["on_batch_completed"](1, 2, ("de",), document, document)
            raise RuntimeError("late failure")

        controller = GenerationController(
            generator=generator,
            login_checker=lambda _cancel_event: None,
            runner=lambda _package, _schema, _cancel_event: {},
        )
        first = controller.start("owner-4", self.VIDEO, self.CATALOG, ("de", "fr"))
        snapshot, events = self._wait_for_terminal(controller, "owner-4", first.job_id)

        self.assertEqual(snapshot.status, "failed")
        self.assertEqual(snapshot.error, "late failure")
        self.assertEqual(
            [event.codes for event in events if event.kind == "batch_completed"],
            [("de",)],
        )


if __name__ == "__main__":
    unittest.main()
