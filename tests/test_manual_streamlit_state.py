import json
import sys
import unittest
from contextlib import nullcontext
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from codex_localization_generator import CodexGenerationError
from codex_localization_runner import CodexLocalizationError
from ui import llm_package
from state.manual_state import (
    manual_can_publish,
    manual_fingerprint,
    manual_preview_is_current,
    set_manual_json,
    sync_manual_video,
)
from state.llm_state import init_llm_state
from ui.manual_editor import render_manual_editor, select_manual_example_codes
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog


class _FakeStreamlit:
    def __init__(self, raw_json, publish_clicked):
        self.session_state = {"manual-localizations-json": raw_json}
        self.publish_clicked = publish_clicked
        self.expander_calls = []
        self.code_calls = []

    def subheader(self, *_args, **_kwargs):
        pass

    def caption(self, *_args, **_kwargs):
        pass

    def expander(self, label, **kwargs):
        self.expander_calls.append((label, kwargs))
        return nullcontext()

    def code(self, *_args, **_kwargs):
        self.code_calls.append((_args[0], _kwargs))

    def text_area(self, _label, **kwargs):
        return self.session_state[kwargs["key"]]

    def success(self, *_args, **_kwargs):
        pass

    def info(self, *_args, **_kwargs):
        pass

    def error(self, *_args, **_kwargs):
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


class _FakeProgressPlaceholder:
    def __init__(self, calls):
        self.calls = calls

    def info(self, *args, **kwargs):
        self.calls.append(("progress", args, kwargs))


def _fake_llm_streamlit(uploaded_file, generate_clicked=False):
    streamlit = ModuleType("streamlit")
    streamlit.session_state = {}
    streamlit.calls = []
    streamlit.rerun_calls = 0
    streamlit.markdown = lambda *args, **kwargs: streamlit.calls.append(
        ("markdown", args, kwargs)
    )
    streamlit.caption = lambda *args, **_kwargs: streamlit.calls.append(
        ("caption", args)
    )
    streamlit.success = lambda *args, **kwargs: streamlit.calls.append(
        ("success", args, kwargs)
    )
    streamlit.code = lambda *_args, **_kwargs: None
    streamlit.error = lambda *args, **kwargs: streamlit.calls.append(
        ("error", args, kwargs)
    )
    streamlit.info = lambda *_args, **_kwargs: None
    streamlit.page_link = lambda *args, **kwargs: streamlit.calls.append(
        ("page_link", args, kwargs)
    )
    streamlit.button = lambda *args, **kwargs: streamlit.calls.append(
        ("button", args, kwargs)
    ) or (
        generate_clicked
        and args
        and args[0] == "Generate missing translations"
    )
    streamlit.empty = lambda: _FakeProgressPlaceholder(streamlit.calls)
    streamlit.file_uploader = lambda *args, **kwargs: streamlit.calls.append(
        ("file_uploader", args, kwargs)
    ) or uploaded_file

    def rerun():
        streamlit.rerun_calls += 1
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


def _llm_generation_inputs(codes=("en", "de", "fr")):
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
        languages=tuple(YouTubeLanguage(code, code, code) for code in codes),
    )
    return video_resource, catalog


class ManualStateTests(unittest.TestCase):
    def test_manual_example_codes_prioritize_live_codes_and_exclude_default(self):
        supported = ("zh-CN", "en", "pt-BR", "fr", "de", "es", "ja")

        result = select_manual_example_codes(
            supported, default_language_code="EN", max_count=5
        )

        self.assertEqual(result, ("es", "pt-BR", "fr", "de", "ja"))
        self.assertNotIn("en", result)

    def test_manual_example_codes_fill_from_live_catalog_order(self):
        supported = ("en", "xx", "yy", "zz")

        result = select_manual_example_codes(
            supported, default_language_code="en", max_count=3
        )

        self.assertEqual(result, ("xx", "yy", "zz"))

    def test_manual_expander_is_collapsed_when_editor_is_idle(self):
        state = {"raw_json": "", "preview_result": None}
        streamlit = _FakeStreamlit("", publish_clicked=False)

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_manual_editor(state, None, SimpleNamespace(), ("de",))

        self.assertEqual(
            streamlit.expander_calls,
            [
                ("Localization JSON", {"expanded": False}),
                ("Preview & publish", {"expanded": False}),
            ],
        )

    def test_manual_expander_opens_for_json_validation_issue_or_preview(self):
        for raw_json, preview_result in (
            ('{"de": {"title": "Title", "description": "Text"}}', None),
            ("{", None),
            (
                "",
                SimpleNamespace(
                    plan=SimpleNamespace(
                        is_valid=False,
                        has_changes=False,
                        diffs=(),
                        issues=(),
                        preserved_language_codes=(),
                    )
                ),
            ),
        ):
            state = {"raw_json": raw_json, "preview_result": preview_result}
            streamlit = _FakeStreamlit(raw_json, publish_clicked=False)

            with patch.dict(sys.modules, {"streamlit": streamlit}):
                render_manual_editor(state, None, SimpleNamespace(), ("de",))

            self.assertEqual(streamlit.expander_calls[0][1], {"expanded": True})

    def test_manual_example_contains_ten_live_catalog_codes(self):
        supported_codes = (
            "en",
            "es",
            "hi",
            "pt-BR",
            "ar",
            "id",
            "fr",
            "de",
            "ja",
            "vi",
            "ru",
            "ko",
            "tr",
        )
        streamlit = _FakeStreamlit("", publish_clicked=False)

        with patch.dict(sys.modules, {"streamlit": streamlit}):
            render_manual_editor(
                {"raw_json": "", "preview_result": None},
                None,
                SimpleNamespace(),
                supported_codes,
                default_language_code="en",
            )

        example = json.loads(streamlit.code_calls[0][0])
        self.assertEqual(tuple(example), supported_codes[1:11])
        self.assertEqual(len(example), 10)

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

    def test_generated_localizations_become_one_canonical_editor_json(self):
        state = {"raw_json": "old editor value", "preview_result": object()}
        apply_generated = getattr(
            llm_package, "apply_generated_localizations", None
        )

        self.assertIsNotNone(apply_generated)
        if apply_generated is None:
            return

        canonical_json = apply_generated(
            state,
            {
                "DE": {"title": "Grüße", "description": "Text"},
                "fr": {"title": "Bonjour", "description": "Texte"},
            },
        )

        self.assertEqual(canonical_json, state["raw_json"])
        self.assertEqual(
            canonical_json,
            '{\n'
            '  "DE": {\n'
            '    "title": "Grüße",\n'
            '    "description": "Text"\n'
            '  },\n'
            '  "fr": {\n'
            '    "title": "Bonjour",\n'
            '    "description": "Texte"\n'
            '  }\n'
            '}',
        )
        self.assertNotIn("\\u00fc", canonical_json)
        self.assertEqual(tuple(json.loads(canonical_json)), ("DE", "fr"))
        self.assertNotIn("localizations", json.loads(canonical_json))

    def test_generate_button_checks_login_and_calls_generator_with_live_inputs(self):
        video_resource, catalog = _llm_generation_inputs()
        login_checker = Mock()
        generator = Mock(
            return_value={
                "de": {"title": "Wasserfall", "description": "Wind"},
            }
        )
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            with self.assertRaises(_RerunRequested):
                llm_package.render_llm_translation_controls(
                    {"raw_json": ""},
                    video_resource,
                    catalog,
                    login_checker=login_checker,
                    generate_localizations=generator,
                )

        login_checker.assert_called_once_with()
        generator.assert_called_once()
        generator_args, generator_kwargs = generator.call_args
        self.assertIs(generator_args[0], video_resource)
        self.assertIs(generator_args[1], catalog)
        self.assertNotIn("max_languages", generator_kwargs)
        self.assertTrue(callable(generator_kwargs["on_batch"]))
        self.assertTrue(
            any(
                kind == "button"
                and args[0] == "Generate missing translations"
                for kind, args, *_rest in streamlit.calls
            )
        )

    def test_generate_button_reports_generator_batch_callbacks(self):
        missing_codes = tuple("lang-{:02d}".format(index) for index in range(21))
        video_resource, catalog = _llm_generation_inputs(("en",) + missing_codes)
        callbacks = []

        def fake_generate(_video_resource, _catalog, *, on_batch):
            batches = (
                missing_codes[:10],
                missing_codes[10:20],
                missing_codes[20:],
            )
            for index, codes in enumerate(batches, start=1):
                callbacks.append((index, 3, codes))
                on_batch(index, 3, codes)
            return {}

        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                {"raw_json": "old"},
                video_resource,
                catalog,
                login_checker=lambda: None,
                generate_localizations=fake_generate,
            )

        self.assertEqual(
            [(index, total) for index, total, _codes in callbacks],
            [(1, 3), (2, 3), (3, 3)],
        )
        progress_messages = [
            args[0]
            for kind, args, *_rest in streamlit.calls
            if kind == "progress"
        ]
        self.assertEqual(
            progress_messages,
            [
                "Generating batch 1 / 3 — " + ", ".join(missing_codes[:10]),
                "Generating batch 2 / 3 — " + ", ".join(missing_codes[10:20]),
                "Generating batch 3 / 3 — " + ", ".join(missing_codes[20:]),
            ],
        )

    def test_generated_result_becomes_editor_json_and_requests_one_rerun(self):
        video_resource, catalog = _llm_generation_inputs()
        state = {"raw_json": "old editor value"}
        generated = {
            "DE": {"title": "Grüße", "description": "Text"},
            "fr": {"title": "Bonjour", "description": "Texte"},
        }
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        editor_key = "llm-localizations-json-video-1"
        streamlit.session_state[editor_key] = "old widget value"
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            with self.assertRaises(_RerunRequested):
                llm_package.render_llm_translation_controls(
                    state,
                    video_resource,
                    catalog,
                    login_checker=lambda: None,
                    generate_localizations=lambda *_args, **_kwargs: generated,
                )

        self.assertEqual(streamlit.rerun_calls, 1)
        self.assertEqual(state["raw_json"], streamlit.session_state[editor_key])
        self.assertEqual(
            state["raw_json"],
            '{\n'
            '  "DE": {\n'
            '    "title": "Grüße",\n'
            '    "description": "Text"\n'
            '  },\n'
            '  "fr": {\n'
            '    "title": "Bonjour",\n'
            '    "description": "Texte"\n'
            '  }\n'
            '}',
        )

    def test_login_error_is_shown_without_starting_generation(self):
        video_resource, catalog = _llm_generation_inputs()
        generator = Mock()
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        def missing_login():
            raise CodexLocalizationError(
                "Codex CLI is not logged in. Run `codex login`."
            )

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                {"raw_json": "old"},
                video_resource,
                catalog,
                login_checker=missing_login,
                generate_localizations=generator,
            )

        generator.assert_not_called()
        self.assertEqual(streamlit.rerun_calls, 0)
        self.assertTrue(
            any(
                kind == "error" and "codex login" in args[0]
                for kind, args, *_rest in streamlit.calls
            )
        )

    def test_generation_error_preserves_editor_json_and_does_not_rerun(self):
        video_resource, catalog = _llm_generation_inputs()
        state = {"raw_json": "existing editor value"}
        generator = Mock(side_effect=CodexGenerationError("batch failed"))
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        editor_key = "llm-localizations-json-video-1"
        streamlit.session_state[editor_key] = "existing widget value"
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state,
                video_resource,
                catalog,
                login_checker=lambda: None,
                generate_localizations=generator,
            )

        self.assertEqual(state["raw_json"], "existing editor value")
        self.assertEqual(
            streamlit.session_state[editor_key], "existing widget value"
        )
        self.assertEqual(streamlit.rerun_calls, 0)
        self.assertTrue(
            any(
                kind == "error" and "batch failed" in args[0]
                for kind, args, *_rest in streamlit.calls
            )
        )

    def test_unexpected_generation_error_is_shown_without_rerun(self):
        video_resource, catalog = _llm_generation_inputs()
        state = {"raw_json": "existing editor value"}
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            llm_package.render_llm_translation_controls(
                state,
                video_resource,
                catalog,
                login_checker=lambda: None,
                generate_localizations=Mock(
                    side_effect=RuntimeError("unexpected failure")
                ),
            )

        self.assertEqual(state["raw_json"], "existing editor value")
        self.assertEqual(streamlit.rerun_calls, 0)
        self.assertTrue(
            any(
                kind == "error" and "unexpected failure" in args[0]
                for kind, args, *_rest in streamlit.calls
            )
        )

    def test_automatic_generation_does_not_call_publish_method(self):
        video_resource, catalog = _llm_generation_inputs()
        publish = Mock()
        state = {"raw_json": "old", "publish": publish}
        streamlit, components, components_v1 = _fake_llm_streamlit(
            None, generate_clicked=True
        )
        modules = {
            "streamlit": streamlit,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

        with patch.dict(sys.modules, modules):
            with self.assertRaises(_RerunRequested):
                llm_package.render_llm_translation_controls(
                    state,
                    video_resource,
                    catalog,
                    login_checker=lambda: None,
                    generate_localizations=lambda *_args, **_kwargs: {
                        "de": {"title": "Wasserfall", "description": "Wind"}
                    },
                )

        publish.assert_not_called()

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
        missing_caption = "Missing " + "translations"
        self.assertFalse(
            any(
                kind == "caption" and missing_caption in args[0]
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

        self.assertEqual(state["raw_json"], "")
        self.assertIsNone(state["preview_result"])
        self.assertFalse(manual_preview_is_current(state))
        self.assertFalse(manual_can_publish(state))

    def test_llm_state_does_not_duplicate_universal_editor_state(self):
        state = {}

        init_llm_state(state)

        self.assertNotIn("raw_json", state["llm"])
        self.assertNotIn("preview_result", state["llm"])
        self.assertIn("prompt_text", state["llm"])

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
