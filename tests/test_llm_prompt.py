import sys
import unittest
from contextlib import nullcontext
from types import ModuleType
from unittest.mock import patch

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog


class _FakeStreamlit:
    def __init__(self, selected_codes=None, copy_clicked=False):
        self.session_state = {}
        self.selected_codes = selected_codes
        self.copy_clicked = copy_clicked
        self.multiselect_calls = []
        self.text_area_calls = []
        self.code_calls = []
        self.messages = []

    def caption(self, value, **_kwargs):
        self.messages.append(("caption", value))

    def expander(self, label, **kwargs):
        self.messages.append(("expander", label))
        return nullcontext()

    def markdown(self, value, **_kwargs):
        self.messages.append(("markdown", value))

    def page_link(self, *args, **kwargs):
        self.messages.append(("page_link", args, kwargs))

    def multiselect(self, label, options, **kwargs):
        self.multiselect_calls.append((label, tuple(options), kwargs))
        return self.selected_codes if self.selected_codes is not None else kwargs["default"]

    def text_area(self, label, **kwargs):
        self.text_area_calls.append((label, kwargs))
        return kwargs.get("value", "")

    def code(self, body, **kwargs):
        self.code_calls.append((body, kwargs))

    def button(self, _label, **_kwargs):
        return self.copy_clicked

    def success(self, value, **_kwargs):
        self.messages.append(("success", value))

    def error(self, value, **_kwargs):
        self.messages.append(("error", value))


class _SourceSelectionStreamlit(_FakeStreamlit):
    def expander(self, *_args, **_kwargs):
        return nullcontext()

    def info(self, value, **_kwargs):
        self.messages.append(("info", value))


class LlmPromptPageTests(unittest.TestCase):
    def setUp(self):
        self.video_resource = {
            "id": "video-1",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {
                "de": {"title": "Wasserfall", "description": "Wind"},
            },
        }
        self.catalog = YouTubeLanguageCatalog(
            source="YouTube Studio metadata language picker",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "Английский", "English"),
                YouTubeLanguage("de", "de", "Немецкий", "German"),
                YouTubeLanguage("code-0", "code-0", "Зулу", "Zulu"),
                YouTubeLanguage("code-1", "code-1", "Английский (Великобритания)", "English (United Kingdom)"),
                YouTubeLanguage("code-2", "code-2", "Французский", "French"),
                YouTubeLanguage("code-3", "code-3", "Итальянский", "Italian"),
                YouTubeLanguage("code-4", "code-4", "Японский", "Japanese"),
                YouTubeLanguage("code-5", "code-5", "Корейский", "Korean"),
                YouTubeLanguage("code-6", "code-6", "Португальский", "Portuguese"),
                YouTubeLanguage("code-7", "code-7", "Испанский", "Spanish"),
                YouTubeLanguage("code-8", "code-8", "Тайский", "Thai"),
                YouTubeLanguage("code-9", "code-9", "Украинский", "Ukrainian"),
                YouTubeLanguage("code-10", "code-10", "Вьетнамский", "Vietnamese"),
            ),
        )

    def _streamlit_modules(self, fake):
        components = ModuleType("streamlit.components")
        components_v1 = ModuleType("streamlit.components.v1")
        components_v1.html = lambda *args, **kwargs: fake.messages.append(
            ("html", args, kwargs)
        )
        components.v1 = components_v1
        fake.components = components
        return {
            "streamlit": fake,
            "streamlit.components": components,
            "streamlit.components.v1": components_v1,
        }

    def test_prompt_page_uses_only_missing_catalog_codes_and_first_ten_defaults(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit()
        state = {"bound_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        options = fake.multiselect_calls[0][1]
        kwargs = fake.multiselect_calls[0][2]
        self.assertNotIn("en", options)
        self.assertNotIn("de", options)
        self.assertEqual(options, tuple(language.code for language in self.catalog.languages[2:]))
        self.assertEqual(kwargs["default"], options[:10])
        self.assertEqual(kwargs["max_selections"], 10)
        self.assertEqual(kwargs["format_func"]("code-2"), "code-2 — French")

    def test_prompt_page_preserves_explicit_subset_and_builds_prompt_without_existing_content(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2", "code-7"))
        state = {
            "bound_video_id": "video-1",
            "selected_target_codes": ("code-2", "code-7"),
        }

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        self.assertEqual(
            fake.multiselect_calls[0][2]["default"], ("code-2", "code-7")
        )
        self.assertEqual(state["prompt_target_codes"], ("code-2", "code-7"))
        self.assertIn("Waterfall", state["prompt_text"])
        self.assertNotIn("Wasserfall", state["prompt_text"])

    def test_eleventh_selection_does_not_replace_prompt(self):
        from ui.llm_prompt import render_llm_prompt_page

        missing_codes = tuple(
            language.code for language in self.catalog.languages[2:]
        )
        fake = _FakeStreamlit(selected_codes=missing_codes)
        state = {
            "bound_video_id": "video-1",
            "selected_target_codes": ("code-2",),
            "prompt_video_id": "video-1",
            "prompt_target_codes": ("code-2",),
            "prompt_text": "old prompt",
        }

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        self.assertEqual(state["selected_target_codes"], ("code-2",))
        self.assertEqual(state["prompt_text"], "old prompt")
        self.assertTrue(any(kind == "error" for kind, _ in fake.messages))

    def test_prompt_is_rendered_in_a_native_copyable_code_block(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2",))
        state = {"bound_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        self.assertEqual(len(fake.text_area_calls), 0)
        self.assertEqual(len(fake.code_calls), 1)
        self.assertEqual(fake.code_calls[0][1], {"language": "text"})
        self.assertEqual(fake.code_calls[0][0], state["prompt_text"])

    def test_prompt_uses_the_shared_primary_and_selected_reference_sources(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2",))
        state = {"bound_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(
                state,
                self.video_resource,
                self.catalog,
                source_codes=("en", "de"),
            )

        self.assertIn("primary", state["prompt_text"])
        self.assertIn("Wasserfall", state["prompt_text"])
        self.assertIn("references", state["prompt_text"])

    def test_prompt_page_links_back_to_translate(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2",))
        state = {"bound_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        self.assertTrue(
            any(
                call[0] == "page_link"
                and call[1][0] == "pages/1_Translate.py"
                and call[2]["label"] == "Return to Translate"
                for call in fake.messages
            )
        )

    def test_shared_source_selector_restores_default_when_removed(self):
        from ui.source_selection import render_source_selection

        fake = _SourceSelectionStreamlit(selected_codes=("de",))
        session_state = {}

        with patch.dict(sys.modules, {"streamlit": fake}):
            selected = render_source_selection(
                session_state, self.video_resource, self.catalog
            )

        self.assertEqual(selected, ("en", "de"))
        self.assertEqual(
            session_state["common.selected_source_codes"], ("en", "de")
        )


if __name__ == "__main__":
    unittest.main()
