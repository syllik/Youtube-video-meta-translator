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


class _FakeStreamlit:
    def __init__(self, clicked=False):
        self.clicked = clicked
        self.buttons = []
        self.downloads = []
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
        return None

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

    def test_one_click_checkpoints_one_batch_and_returns_to_ui(self):
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
            tuple("code-{}".format(index) for index in range(10)),
        )
        self.assertEqual(len(state["draft"]), 10)
        self.assertEqual(state["generation_completed_batch_count"], 1)
        self.assertTrue(fake.rerun_called)
        self.assertTrue(fake.downloads[0][1]["disabled"])

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
                tuple("code-{}".format(index) for index in range(10)),
                ("code-10", "code-11"),
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
