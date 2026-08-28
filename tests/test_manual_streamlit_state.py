import sys
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import patch

from ui import llm_package
from state.manual_state import (
    manual_can_publish,
    manual_fingerprint,
    manual_preview_is_current,
    set_manual_json,
    set_manual_video,
)
from ui.manual_editor import render_manual_editor


class _FakeStreamlit:
    def __init__(self, raw_json, publish_clicked):
        self.session_state = {"manual-localizations-json": raw_json}
        self.publish_clicked = publish_clicked

    def subheader(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass

    def code(self, *_args, **_kwargs):
        pass

    def text_area(self, _label, **kwargs):
        return self.session_state[kwargs["key"]]

    def success(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def columns(self, _count):
        return nullcontext(), nullcontext()

    def button(self, _label, **kwargs):
        return self.publish_clicked and kwargs["key"].endswith("publish-changes")

    def spinner(self, *_args, **_kwargs):
        return nullcontext()


def _publishable_state(raw_json):
    return {
        "selected_video_id": "video-1",
        "raw_json": raw_json,
        "preview_fingerprint": manual_fingerprint("video-1", raw_json),
        "preview_result": SimpleNamespace(
            plan=SimpleNamespace(is_valid=True, has_changes=True, diffs=(), issues=())
        ),
        "published": False,
        "operation_status": "idle",
        "operation_error": None,
    }


class ManualStateTests(unittest.TestCase):
    def test_valid_utf8_upload_becomes_canonical_editor_json(self):
        state = {"raw_json": "old editor value"}
        apply_upload = getattr(llm_package, "apply_llm_upload", None)

        self.assertIsNotNone(apply_upload, "LLM uploads need a local handoff")
        if apply_upload is None:
            return

        result = apply_upload(
            state,
            b'{"DE":{"title":"Gr\xc3\xbc\xc3\x9fe","description":"Text"}}',
            ("de",),
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(
            state["raw_json"],
            '{\n  "de": {\n    "title": "Gr\u00fc\u00dfe",\n    "description": "Text"\n  }\n}',
        )

    def test_invalid_upload_leaves_editor_json_unchanged(self):
        state = {"raw_json": "old editor value"}
        apply_upload = getattr(llm_package, "apply_llm_upload", None)

        self.assertIsNotNone(apply_upload, "LLM uploads need a local handoff")
        if apply_upload is None:
            return

        result = apply_upload(state, b'\xff', ("de",))

        self.assertFalse(result.is_valid)
        self.assertEqual(state["raw_json"], "old editor value")

    def test_post_publish_callback_runs_after_a_write(self):
        raw_json = '{"de": {"title": "German", "description": "Text"}}'
        state = _publishable_state(raw_json)
        streamlit = _FakeStreamlit(raw_json, publish_clicked=True)
        callbacks = []
        result = SimpleNamespace(
            wrote=True,
            plan=SimpleNamespace(diffs=(), issues=(), preserved_language_codes=()),
        )
        service = SimpleNamespace(publish=lambda _video_id, _raw_json: result)

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_manual_editor(
                state,
                SimpleNamespace(id="video-1"),
                service,
                ("de",),
                on_published=lambda: callbacks.append("published"),
            )

        self.assertEqual(callbacks, ["published"])

    def test_post_publish_callback_does_not_run_without_a_write(self):
        raw_json = '{"de": {"title": "German", "description": "Text"}}'
        state = _publishable_state(raw_json)
        streamlit = _FakeStreamlit(raw_json, publish_clicked=True)
        callbacks = []
        result = SimpleNamespace(
            wrote=False,
            plan=SimpleNamespace(diffs=(), issues=(), preserved_language_codes=()),
        )
        service = SimpleNamespace(publish=lambda _video_id, _raw_json: result)

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_manual_editor(
                state,
                SimpleNamespace(id="video-1"),
                service,
                ("de",),
                on_published=lambda: callbacks.append("published"),
            )

        self.assertEqual(callbacks, [])

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
