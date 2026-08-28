import sys
import unittest
from contextlib import nullcontext
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from ui import llm_package
from state.manual_state import (
    manual_can_publish,
    manual_fingerprint,
    manual_preview_is_current,
    set_manual_json,
    sync_manual_video,
)
from ui.manual_editor import render_manual_editor
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog


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


class _RerunRequested(Exception):
    pass


class _FakeUploadedFile:
    def __init__(self, content):
        self.content = content

    def getvalue(self):
        return self.content


def _fake_llm_streamlit(uploaded_file):
    streamlit = ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit.calls = []
    streamlit.markdown = lambda *args, **kwargs: streamlit.calls.append(
        ("markdown", args, kwargs)
    )
    streamlit.caption = lambda *args, **_kwargs: streamlit.calls.append(
        ("caption", args)
    )
    streamlit.success = lambda *_args, **_kwargs: None
    streamlit.code = lambda *_args, **_kwargs: None
    streamlit.error = lambda *_args, **_kwargs: None
    streamlit.info = lambda *_args, **_kwargs: None
    streamlit.page_link = lambda *args, **kwargs: streamlit.calls.append(
        ("page_link", args, kwargs)
    )
    streamlit.button = lambda *_args, **_kwargs: False
    streamlit.file_uploader = lambda *args, **kwargs: streamlit.calls.append(
        ("file_uploader", args, kwargs)
    ) or uploaded_file

    def rerun():
        raise _RerunRequested()

    streamlit.rerun = rerun
    components = ModuleType("streamlit.components")
    components_v1 = ModuleType("streamlit.components.v1")
    components_v1.html = lambda *_args, **_kwargs: None
    components.v1 = components_v1
    streamlit.components = components
    return streamlit, components, components_v1


def _publishable_state(raw_json):
    return {
        "bound_video_id": "video-1",
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

    def test_persisted_valid_upload_is_consumed_once_then_editor_can_render(self):
        state = {
            "prompt_video_id": "video-1",
            "prompt_target_codes": ("de",),
            "prompt_text": "translate this",
            "raw_json": "",
        }
        video_resource = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind",
            },
            "localizations": {},
        }
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
            ),
        )
        uploaded_file = _FakeUploadedFile(
            b'{"de":{"title":"Wasserfall","description":"Wind"}}'
        )
        streamlit, components, components_v1 = _fake_llm_streamlit(uploaded_file)
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            with self.assertRaises(_RerunRequested):
                llm_package.render_llm_translation_controls(state, video_resource, catalog)

            try:
                llm_package.render_llm_translation_controls(state, video_resource, catalog)
            except _RerunRequested:
                self.fail("persisted upload requested another rerun before the editor")

        self.assertEqual(
            state["raw_json"],
            '{\n  "de": {\n    "title": "Wasserfall",\n    "description": "Wind"\n  }\n}',
        )

    def test_llm_controls_show_exact_prompt_batch_and_uploader_only_after_prompt(self):
        state = {
            "bound_video_id": "video-1",
            "prompt_video_id": "video-1",
            "prompt_target_codes": ("fr", "de"),
            "prompt_text": "prompt",
            "raw_json": "",
        }
        video_resource = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind",
            },
            "localizations": {},
        }
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
                YouTubeLanguage("fr", "fr", "French"),
            ),
        )
        streamlit, components, components_v1 = _fake_llm_streamlit(None)
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state, video_resource, catalog
            )

        self.assertTrue(
            any(
                kind == "markdown" and "localization-badge" in args[0]
                for kind, args, *_rest in streamlit.calls
            )
        )
        self.assertFalse(
            any(
                kind == "caption" and "Missing translations" in args[0]
                for kind, args, *_rest in streamlit.calls
            )
        )
        self.assertTrue(any(call[0] == "file_uploader" for call in streamlit.calls))

    def test_llm_controls_do_not_show_uploader_without_current_prompt_batch(self):
        state = {
            "bound_video_id": "video-1",
            "prompt_video_id": "video-2",
            "prompt_target_codes": ("de",),
            "prompt_text": "other video prompt",
            "raw_json": "old",
        }
        video_resource = {
            "id": "video-1",
            "snippet": {"defaultLanguage": "en"},
            "localizations": {},
        }
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(YouTubeLanguage("en", "en", "English"),),
        )
        streamlit, components, components_v1 = _fake_llm_streamlit(None)
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state, video_resource, catalog
            )

        self.assertFalse(any(call[0] == "file_uploader" for call in streamlit.calls))

    def test_invalid_llm_uploads_leave_existing_editor_json_unchanged(self):
        state = {
            "prompt_video_id": "video-1",
            "prompt_target_codes": ("de",),
            "prompt_text": "translate",
            "raw_json": "existing editor value",
        }
        video_resource = {
            "id": "video-1",
            "snippet": {"defaultLanguage": "en"},
            "localizations": {},
        }
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
            ),
        )
        streamlit, components, components_v1 = _fake_llm_streamlit(
            _FakeUploadedFile(b'{"languages": {}}')
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state, video_resource, catalog
            )

        self.assertEqual(state["raw_json"], "existing editor value")

    def test_llm_progress_uses_fresh_youtube_localizations_after_publish(self):
        state = {
            "bound_video_id": "video-1",
            "prompt_video_id": "video-1",
            "prompt_target_codes": ("de",),
            "prompt_text": "translate",
            "raw_json": '{"de": {"title": "German", "description": "Text"}}',
        }
        first_resource = {
            "id": "video-1",
            "snippet": {"defaultLanguage": "en"},
            "localizations": {},
        }
        published_resource = {
            "id": "video-1",
            "snippet": {"defaultLanguage": "en"},
            "localizations": {
                "de": {"title": "German", "description": "Text"}
            },
        }
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
            ),
        )

        streamlit, components, components_v1 = _fake_llm_streamlit(None)
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }
        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state, first_resource, catalog
            )
            llm_package.render_llm_translation_controls(
                state, published_resource, catalog
            )

        progress_captions = [
            args[0]
            for kind, args, *rest in streamlit.calls
            if kind == "caption" and args and args[0].startswith("YouTube translations")
        ]
        self.assertEqual(progress_captions, ["YouTube translations: 0 / 1", "YouTube translations: 1 / 1"])

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
            "bound_video_id": "video-1",
            "raw_json": '{"es": {"title": "A", "description": "B"}}',
            "preview_fingerprint": ("video-1", "hash-1"),
            "preview_result": object(),
        }

        sync_manual_video(state, "video-2")

        self.assertIsNone(state["preview_result"])
        self.assertFalse(manual_preview_is_current(state))
        self.assertFalse(manual_can_publish(state))

    def test_json_change_invalidates_preview_even_for_same_video(self):
        state = {
            "bound_video_id": "video-1",
            "raw_json": "old",
            "preview_fingerprint": ("video-1", "old-hash"),
            "preview_result": object(),
        }

        set_manual_json(state, "new")

        self.assertIsNone(state["preview_result"])
        self.assertFalse(manual_can_publish(state))

    def test_published_preview_cannot_be_submitted_again(self):
        state = {
            "bound_video_id": "video-1",
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
