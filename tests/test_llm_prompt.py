import sys
import unittest
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
        self.messages = []

    def caption(self, value, **_kwargs):
        self.messages.append(("caption", value))

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

    def button(self, _label, **_kwargs):
        return self.copy_clicked

    def success(self, value, **_kwargs):
        self.messages.append(("success", value))

    def error(self, value, **_kwargs):
        self.messages.append(("error", value))


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
            source="YouTube Data API v3 i18nLanguages.list",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
                YouTubeLanguage("code-0", "code-0", "Zulu"),
                YouTubeLanguage("code-1", "code-1", "English (United Kingdom)"),
                YouTubeLanguage("code-2", "code-2", "French"),
                YouTubeLanguage("code-3", "code-3", "Italian"),
                YouTubeLanguage("code-4", "code-4", "Japanese"),
                YouTubeLanguage("code-5", "code-5", "Korean"),
                YouTubeLanguage("code-6", "code-6", "Portuguese"),
                YouTubeLanguage("code-7", "code-7", "Spanish"),
                YouTubeLanguage("code-8", "code-8", "Thai"),
                YouTubeLanguage("code-9", "code-9", "Ukrainian"),
                YouTubeLanguage("code-10", "code-10", "Vietnamese"),
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
        state = {"selected_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        options = fake.multiselect_calls[0][1]
        kwargs = fake.multiselect_calls[0][2]
        self.assertNotIn("en", options)
        self.assertNotIn("de", options)
        self.assertEqual(options, tuple(language.code for language in self.catalog.languages[2:]))
        self.assertEqual(kwargs["default"], options[:10])
        self.assertEqual(kwargs["max_selections"], 10)
        self.assertEqual(
            kwargs["format_func"]("code-2"), "French (code-2)"
        )

    def test_prompt_page_preserves_explicit_subset_and_builds_prompt_without_existing_content(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2", "code-7"))
        state = {
            "selected_video_id": "video-1",
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
            "selected_video_id": "video-1",
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

    def test_copy_prompt_requests_clipboard_and_reports_success(self):
        from ui.llm_prompt import render_llm_prompt_page

        fake = _FakeStreamlit(selected_codes=("code-2",), copy_clicked=True)
        state = {"selected_video_id": "video-1", "selected_target_codes": ()}

        with patch.dict(sys.modules, self._streamlit_modules(fake)):
            render_llm_prompt_page(state, self.video_resource, self.catalog)

        html_calls = [message for message in fake.messages if message[0] == "html"]
        self.assertEqual(len(html_calls), 1)
        self.assertIn("navigator.clipboard", html_calls[0][1][0])
        self.assertTrue(any(message[0] == "success" for message in fake.messages))


if __name__ == "__main__":
    unittest.main()
