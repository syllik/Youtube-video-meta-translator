import json
import sys
import types
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from codex_localization_generator import CodexGenerationError
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from state.translation_state import init_translation_state
from ui.llm_package import render_llm_translation_controls


class _Column:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


class _UploadedFile:
    def __init__(self, content):
        self.content = content

    def getvalue(self):
        return self.content


class _FakeStreamlit:
    def __init__(self, clicked=False, uploaded_file=None):
        self.clicked = clicked
        self.uploaded_file = uploaded_file
        self.buttons = []
        self.downloads = []
        self.file_uploaders = []
        self.messages = []
        self.rerun_called = False

    def __getattr__(self, name):
        if name in {"markdown", "caption", "success", "warning", "info", "error"}:
            return lambda message, **_kwargs: self.messages.append((name, message))
        raise AttributeError(name)

    def page_link(self, *_args, **_kwargs):
        return None

    def columns(self, _count):
        return (_Column(), _Column())

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return self.clicked and not kwargs.get("disabled", False)

    def download_button(self, label, **kwargs):
        self.downloads.append((label, kwargs))
        return False

    def empty(self):
        return self

    def spinner(self, _message):
        return nullcontext()

    def file_uploader(self, *_args, **_kwargs):
        self.file_uploaders.append((_args, _kwargs))
        return self.uploaded_file

    def code(self, *_args, **_kwargs):
        return None

    def rerun(self):
        self.rerun_called = True

    def info(self, message):
        self.messages.append(("info", message))


class LlmPackageUiTests(unittest.TestCase):
    def setUp(self):
        codes = ("en",) + tuple("code-{}".format(index) for index in range(12))
        self.catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=tuple(
                YouTubeLanguage(code, code, code) for code in codes
            ),
        )
        self.video = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Title",
                "description": "Description",
            },
            "localizations": {},
        }

    def _streamlit_modules(self, fake):
        streamlit = types.ModuleType("streamlit")
        streamlit.__path__ = []
        for name in (
            "markdown", "caption", "success", "warning", "info", "error",
            "page_link", "columns", "button", "download_button", "empty",
            "spinner", "file_uploader", "code", "rerun",
        ):
            setattr(streamlit, name, getattr(fake, name))
        components = types.ModuleType("streamlit.components")
        components.__path__ = []
        components_v1 = types.ModuleType("streamlit.components.v1")
        components_v1.html = lambda *_args, **_kwargs: None
        components.v1 = components_v1
        streamlit.components = components
        return {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

    def test_one_click_passes_all_selected_targets_to_generator(self):
        state = init_translation_state({})
        fake = _FakeStreamlit(clicked=True)
        calls = []

        def generate(video, catalog, **kwargs):
            calls.append(kwargs)
            codes = tuple(kwargs["target_codes"])
            document = {
                code: {"title": "Title", "description": "Description"}
                for code in codes
            }
            kwargs["on_batch_completed"](1, 1, codes, document, document)
            return document

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                login_checker=lambda: None,
                generate_localizations=generate,
                prompt_state={},
                target_codes=tuple("code-{}".format(index) for index in range(12)),
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(
            tuple(calls[0]["target_codes"]),
            tuple("code-{}".format(index) for index in range(12)),
        )
        self.assertEqual(len(state["draft"]), 12)
        self.assertEqual(state["generation_completed_batch_count"], 1)
        self.assertTrue(fake.rerun_called)
        self.assertTrue(fake.downloads[0][1]["disabled"])

    def test_one_generate_click_processes_all_remaining_batches(self):
        codes = tuple("code-{}".format(index) for index in range(25))
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=tuple(
                [YouTubeLanguage("en", "en", "English")]
                + [YouTubeLanguage(code, code, code) for code in codes]
            ),
        )
        state = init_translation_state({})
        fake = _FakeStreamlit(clicked=True)
        calls = []
        callback_batches = []

        def generate(video, catalog, **kwargs):
            calls.append(tuple(kwargs["target_codes"]))
            selected = tuple(kwargs["target_codes"])
            cumulative = {}
            for batch_index, start in enumerate(range(0, len(selected), 10), start=1):
                batch_codes = selected[start:start + 10]
                document = {
                    code: {"title": code, "description": code}
                    for code in batch_codes
                }
                cumulative.update(document)
                callback_batches.append(batch_codes)
                kwargs["on_batch_completed"](
                    batch_index,
                    3,
                    batch_codes,
                    document,
                    cumulative,
                )
            return cumulative

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                catalog,
                login_checker=lambda: None,
                generate_localizations=generate,
                prompt_state={},
                target_codes=codes,
            )

        self.assertEqual(calls, [codes])
        self.assertEqual(
            callback_batches,
            [codes[:10], codes[10:20], codes[20:]],
        )
        self.assertEqual(tuple(state["draft"]), codes)
        self.assertEqual(state["generation_completed_batch_count"], 3)

    def test_late_batch_failure_rerenders_last_checkpoint_for_download_and_retry(self):
        codes = tuple("code-{}".format(index) for index in range(25))
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=tuple(
                [YouTubeLanguage("en", "en", "English")]
                + [YouTubeLanguage(code, code, code) for code in codes]
            ),
        )
        state = init_translation_state({})
        state["preview_result"] = object()
        state["preview_fingerprint"] = ("video-1", "stale")
        first_fake = _FakeStreamlit(clicked=True)
        calls = []

        def failed_generation(video, catalog, **kwargs):
            selected = tuple(kwargs["target_codes"])
            calls.append(selected)
            cumulative = {}
            for batch_index, start in enumerate((0, 10), start=1):
                batch_codes = selected[start:start + 10]
                document = {
                    code: {"title": code, "description": code}
                    for code in batch_codes
                }
                cumulative.update(document)
                kwargs["on_batch_completed"](
                    batch_index,
                    3,
                    batch_codes,
                    document,
                    cumulative,
                )
            raise CodexGenerationError(
                "Codex batch 3 / 3 failed for [code-20]."
            )

        with patch.dict(sys.modules, self._streamlit_modules(first_fake)):
            render_llm_translation_controls(
                state,
                self.video,
                catalog,
                login_checker=lambda: None,
                generate_localizations=failed_generation,
                prompt_state={},
                target_codes=codes,
            )

        self.assertEqual(tuple(state["draft"]), codes[:20])
        self.assertEqual(state["generation_completed_batch_count"], 2)
        self.assertIsNone(state["preview_result"])
        self.assertEqual(state["operation_status"], "idle")
        self.assertTrue(first_fake.rerun_called)

        after_failure = _FakeStreamlit(clicked=False)
        with patch.dict(sys.modules, self._streamlit_modules(after_failure)):
            render_llm_translation_controls(
                state,
                self.video,
                catalog,
                login_checker=lambda: None,
                generate_localizations=failed_generation,
                prompt_state={},
                target_codes=codes,
            )

        self.assertEqual(
            json.loads(after_failure.downloads[0][1]["data"]),
            state["draft"],
        )

        retry_fake = _FakeStreamlit(clicked=True)

        def retry_generation(video, catalog, **kwargs):
            remaining = tuple(kwargs["target_codes"])
            calls.append(remaining)
            document = {
                code: {"title": code, "description": code}
                for code in remaining
            }
            kwargs["on_batch_completed"](1, 1, remaining, document, document)
            return document

        with patch.dict(sys.modules, self._streamlit_modules(retry_fake)):
            render_llm_translation_controls(
                state,
                self.video,
                catalog,
                login_checker=lambda: None,
                generate_localizations=retry_generation,
                prompt_state={},
                target_codes=codes,
            )

        self.assertEqual(calls, [codes, codes[20:]])
        self.assertEqual(tuple(state["draft"]), codes)

    def test_checkpoint_is_downloadable_and_retry_skips_it(self):
        state = init_translation_state({})
        first_fake = _FakeStreamlit(clicked=True)
        calls = []

        def generate_first(video, catalog, **kwargs):
            calls.append(tuple(kwargs["target_codes"]))
            codes = tuple(kwargs["target_codes"])
            document = {
                code: {"title": "Title", "description": "Description"}
                for code in codes
            }
            kwargs["on_batch_completed"](1, 1, codes, document, document)
            return document

        target_codes = tuple("code-{}".format(index) for index in range(12))
        with patch.dict(sys.modules, self._streamlit_modules(first_fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                login_checker=lambda: None,
                generate_localizations=generate_first,
                prompt_state={},
                target_codes=target_codes,
            )

        second_fake = _FakeStreamlit(clicked=True)

        def generate_second(video, catalog, **kwargs):
            calls.append(tuple(kwargs["target_codes"]))
            codes = tuple(kwargs["target_codes"])
            document = {
                code: {"title": "Title", "description": "Description"}
                for code in codes
            }
            kwargs["on_batch_completed"](1, 1, codes, document, document)
            return document

        with patch.dict(sys.modules, self._streamlit_modules(second_fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                login_checker=lambda: None,
                generate_localizations=generate_second,
                prompt_state={},
                target_codes=target_codes,
            )

        self.assertEqual(
            calls,
            [
                tuple("code-{}".format(index) for index in range(12)),
            ],
        )
        self.assertEqual(len(state["draft"]), 12)
        self.assertFalse(second_fake.downloads[0][1]["disabled"])
        self.assertIn('"code-0"', second_fake.downloads[0][1]["data"])
        self.assertNotIn("wrapper", second_fake.downloads[0][1]["data"])

    def test_empty_remaining_work_disables_generation_but_keeps_download(self):
        state = init_translation_state({})
        state["draft"] = {
            "code-0": {"title": "Title", "description": "Description"}
        }
        fake = _FakeStreamlit(clicked=True)
        calls = []

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                login_checker=lambda: None,
                generate_localizations=lambda *args, **kwargs: calls.append(kwargs),
                prompt_state={},
                target_codes=("code-0",),
            )

        self.assertEqual(calls, [])
        self.assertTrue(fake.buttons[0][1]["disabled"])
        self.assertFalse(fake.downloads[0][1]["disabled"])

    def test_direct_upload_is_enabled_for_selected_video_without_prompt(self):
        state = init_translation_state({})
        fake = _FakeStreamlit(
            uploaded_file=_UploadedFile(
                b'{"code-0":{"title":"Translated","description":"Text"}}'
            )
        )

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                prompt_state={},
                target_codes=(),
            )

        self.assertFalse(fake.file_uploaders[0][1]["disabled"])
        self.assertEqual(
            state["draft"],
            {"code-0": {"title": "Translated", "description": "Text"}},
        )
        self.assertTrue(fake.rerun_called)

    def test_direct_upload_rejects_the_whole_file_when_one_localization_is_invalid(self):
        state = init_translation_state({})
        state["draft"] = {
            "code-0": {"title": "Existing", "description": "Keep"}
        }
        fake = _FakeStreamlit(
            uploaded_file=_UploadedFile(
                b'{"code-1":{"title":"Valid","description":"Text"},'
                b'"unknown":{"title":"Invalid","description":"Text"}}'
            )
        )

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                prompt_state={},
                target_codes=(),
            )

        self.assertFalse(fake.file_uploaders[0][1]["disabled"])
        self.assertEqual(
            state["draft"],
            {"code-0": {"title": "Existing", "description": "Keep"}},
        )
        self.assertFalse(fake.rerun_called)
        self.assertTrue(any(name == "error" for name, _ in fake.messages))

    def test_direct_upload_replaces_matching_entries_and_preserves_other_draft_entries(self):
        state = init_translation_state({})
        state["draft"] = {
            "code-0": {"title": "Old", "description": "Old"},
            "code-2": {"title": "Keep", "description": "Keep"},
        }
        fake = _FakeStreamlit(
            uploaded_file=_UploadedFile(
                b'{"code-0":{"title":"New","description":"Updated"},'
                b'"code-1":{"title":"Added","description":"Text"}}'
            )
        )

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                prompt_state={},
                target_codes=(),
            )

        self.assertEqual(
            state["draft"],
            {
                "code-0": {"title": "New", "description": "Updated"},
                "code-1": {"title": "Added", "description": "Text"},
                "code-2": {"title": "Keep", "description": "Keep"},
            },
        )

    def test_failed_batch_keeps_an_earlier_checkpoint_in_the_draft(self):
        state = init_translation_state({})
        state["generation_video_id"] = "video-1"
        state["generation_target_codes"] = ("code-0", "code-1")
        state["generation_total_batches"] = 2
        state["generation_completed_batch_count"] = 1
        state["generation_completed_codes"] = ("code-0",)
        state["draft"] = {
            "code-0": {"title": "Title", "description": "Description"}
        }
        fake = _FakeStreamlit(clicked=True)

        def failed_generation(video, catalog, **kwargs):
            raise CodexGenerationError(
                "Codex batch 2 / 2 failed for [code-1]. "
                "The failed batch was not merged. Previously completed batches remain available in the current draft."
            )

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_translation_controls(
                state,
                self.video,
                self.catalog,
                login_checker=lambda: None,
                generate_localizations=failed_generation,
                prompt_state={},
                target_codes=("code-0", "code-1"),
            )

        self.assertEqual(tuple(state["draft"]), ("code-0",))
        self.assertIn("failed batch was not merged", state["generation_error"])
        self.assertTrue(any(name == "error" for name, _ in fake.messages))


if __name__ == "__main__":
    unittest.main()
