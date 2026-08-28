import importlib
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

from streamlit_app import page_title
from ui.channel_header import CHANNEL_LOGO_SIZE


class StreamlitBootstrapTests(unittest.TestCase):
    def test_page_titles_are_explicit(self):
        self.assertEqual(page_title("manual"), "Manual translate")
        self.assertEqual(page_title("llm"), "LLM translate")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            page_title("legacy")

    def test_import_does_not_construct_youtube_client(self):
        sys.modules.pop("streamlit_app", None)
        with patch("youtube_account.YoutubeApi") as constructor:
            importlib.import_module("streamlit_app")
            constructor.assert_not_called()

    def test_only_manual_and_llm_workflow_pages_are_exposed(self):
        root_source = Path("streamlit_app.py").read_text()
        removed_mode = "ma" + "chine"

        self.assertIn('"manual"', root_source)
        self.assertIn('"llm"', root_source)
        self.assertNotIn('"{}"'.format(removed_mode), root_source)
        self.assertFalse(Path("pages/1_" + "Machine_translate.py").exists())
        self.assertTrue(Path("pages/1_Manual_translate.py").exists())
        self.assertTrue(Path("pages/2_LLM_translate.py").exists())

    def test_manual_page_contains_manual_components_only(self):
        source = Path("pages/1_Manual_translate.py").read_text()
        self.assertIn("render_manual_editor", source)
        self.assertIn("render_video_list", source)
        self.assertNotIn("render_llm_translation_controls", source)

    def test_llm_page_uses_live_catalog_and_editor(self):
        source = Path("pages/2_LLM_translate.py").read_text()
        self.assertIn("fetch_localization_language_catalog", source)
        self.assertIn("render_llm_translation_controls", source)
        self.assertIn("render_manual_editor", source)
        self.assertIn("catalog.codes", source)

    def test_supporting_llm_prompt_page_has_selection_and_external_links_only(self):
        prompt_source = Path("pages/3_LLM_prompt.py").read_text()
        ui_source = Path("ui/llm_prompt.py").read_text()

        self.assertIn("render_llm_prompt_page", prompt_source)
        self.assertIn("st.multiselect", ui_source)
        self.assertIn("Copy prompt", ui_source)
        self.assertNotIn("file_uploader", ui_source)
        self.assertNotIn("render_manual_editor", ui_source)
        for provider_url in (
            "https://chatgpt.com/",
            "https://gemini.google.com/",
            "https://claude.ai/",
            "https://copilot.microsoft.com/",
            "https://www.perplexity.ai/",
            "https://chat.mistral.ai/",
        ):
            self.assertIn(provider_url, ui_source)
        self.assertIn('target="_blank"', ui_source)

    def test_llm_ui_uses_local_json_upload(self):
        source = Path("ui/llm_package.py").read_text()
        removed_provider_symbols = (
            "Open" + "AITranslationService",
            "OPEN" + "AI_API_KEY",
            "responses" + ".create",
        )
        self.assertIn("st.file_uploader", source)
        self.assertIn("parse_llm_upload_json", source)
        self.assertIn("st.code", source)
        for symbol in removed_provider_symbols:
            self.assertNotIn(symbol, source)

    def test_llm_translation_controls_are_upload_only(self):
        source = Path("ui/llm_package.py").read_text()

        self.assertIn('id="llm-translation-form"', source)
        self.assertIn("st.page_link", source)
        self.assertIn("st.file_uploader", source)
        self.assertIn("parse_llm_upload_json", source)
        self.assertIn("prompt_target_codes", source)
        self.assertNotIn("Generate prompt", source)
        self.assertNotIn("build_llm_translation_package", source)
        self.assertNotIn("build_llm_translation_prompt", source)
        self.assertNotIn("select_next_llm_languages", source)

    def test_llm_guide_keeps_existing_localizations_out_of_external_context(self):
        guide = Path("docs/llm-localizations.md").read_text()

        self.assertIn(
            "Existing localizations are used only for progress and missing-target calculation.",
            guide,
        )
        self.assertNotIn("- existing `localizations`", guide)
        self.assertNotIn("supporting context", guide)

    def test_llm_page_copy_describes_external_prompt_workflow(self):
        source = Path("streamlit_app.py").read_text()

        self.assertIn("Copy a prompt for an external LLM", source)
        self.assertNotIn("Open" + "AI", source)

    def test_requirements_do_not_declare_openai(self):
        dependency_lines = Path("requirements.txt").read_text().splitlines()
        self.assertFalse(
            any(line.lstrip().startswith("openai") for line in dependency_lines)
        )

    def test_manual_video_selection_uses_card_buttons_not_radio(self):
        source = Path("ui/video_list.py").read_text()
        self.assertNotIn("st.radio", source)
        self.assertIn('"Selected" if is_selected else "Select"', source)

    def test_manual_page_explains_selection_from_another_page(self):
        source = Path("pages/1_Manual_translate.py").read_text()
        self.assertIn("selected video is on another page", source.lower())

    def test_channel_logo_is_large_enough_for_the_summary_card(self):
        self.assertGreaterEqual(CHANNEL_LOGO_SIZE, 112)
        source = Path("ui/channel_header.py").read_text()
        self.assertGreaterEqual(source.count("CHANNEL_LOGO_SIZE"), 2)


if __name__ == "__main__":
    unittest.main()
