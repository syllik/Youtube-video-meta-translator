import importlib
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

from streamlit_app import AppContext, bootstrap_app_context, page_title


class StreamlitBootstrapTests(unittest.TestCase):
    def test_app_context_exposes_shared_selection(self):
        self.assertIn("selected_video_id", AppContext.__annotations__)
        self.assertIn("metadata_language_catalog", AppContext.__annotations__)
        self.assertTrue(callable(bootstrap_app_context))

    def test_page_titles_are_explicit(self):
        self.assertEqual(page_title("translate"), "Translate")
        self.assertEqual(page_title("prompt"), "LLM Translation prompt")
        self.assertEqual(page_title("faq"), "FAQ")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            page_title("legacy")

    def test_import_does_not_construct_youtube_client(self):
        sys.modules.pop("streamlit_app", None)
        with patch("youtube_account.YoutubeApi") as constructor:
            importlib.import_module("streamlit_app")
            constructor.assert_not_called()

    def test_only_translate_and_prompt_workflow_pages_are_exposed(self):
        root_source = Path("streamlit_app.py").read_text()

        self.assertIn('"translate"', root_source)
        self.assertIn('"prompt"', root_source)
        self.assertIn('"faq"', root_source)
        self.assertFalse(Path("pages/1_Manual_translate.py").exists())
        self.assertFalse(Path("pages/2_LLM_translate.py").exists())
        self.assertFalse(Path("pages/3_LLM_prompt.py").exists())
        self.assertTrue(Path("pages/1_Translate.py").exists())
        self.assertTrue(Path("pages/2_LLM_prompt.py").exists())
        self.assertTrue(Path("pages/3_FAQ.py").exists())

    def test_translate_sections_are_rendered_in_the_required_order(self):
        source = Path("pages/1_Translate.py").read_text()
        section_calls = (
            "    source_codes = render_source_selection(",
            "    target_codes = render_target_selection(",
            "        render_llm_translation_controls(",
            "    render_preview_publish(",
        )
        positions = [source.index(name) for name in section_calls]

        self.assertEqual(positions, sorted(positions))

    def test_translate_page_uses_shared_bootstrap_and_translation_controls(self):
        root_source = Path("streamlit_app.py").read_text()
        source = Path("pages/1_Translate.py").read_text()
        self.assertIn("bootstrap_app_context", source)
        self.assertIn("sync_translation_video", source)
        self.assertIn("render_preview_publish", source)
        self.assertIn("render_llm_translation_controls", source)
        self.assertIn("render_source_selection", source)
        self.assertIn("render_target_selection", source)
        self.assertNotIn("Manual edit", source)
        self.assertNotIn("text_area", source)
        self.assertNotIn("localization_editor_key", source)
        self.assertNotIn("render_video_list", source)
        self.assertNotIn("render_pagination", source)
        self.assertIn("fetch_metadata_language_catalog", root_source)
        self.assertNotIn("fetch_application_language_catalog", root_source)
        self.assertIn("reset_video_cache", source)
        self.assertIn("render_service_error", source)

    def test_prompt_page_uses_shared_bootstrap_and_source_selection(self):
        source = Path("pages/2_LLM_prompt.py").read_text()
        self.assertIn("bootstrap_app_context", source)
        self.assertIn("sync_llm_video", source)
        self.assertNotIn("sync_manual_video", source)
        self.assertIn("render_source_selection", source)
        self.assertIn("metadata_language_catalog", source)
        self.assertNotIn("render_video_list", source)
        self.assertNotIn("render_pagination", source)

    def test_supporting_llm_prompt_page_has_selection_and_external_links_only(self):
        prompt_source = Path("pages/2_LLM_prompt.py").read_text()
        ui_source = Path("ui/llm_prompt.py").read_text()

        self.assertIn("render_llm_prompt_page", prompt_source)
        self.assertIn("st.multiselect", ui_source)
        self.assertIn('st.code(prompt, language="text")', ui_source)
        self.assertNotIn("Copy prompt", ui_source)
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

    def test_manual_editor_surface_and_modules_are_removed(self):
        self.assertFalse(Path("state/manual_state.py").exists())
        self.assertFalse(Path("ui/manual_editor.py").exists())
        self.assertFalse(Path("services/manual_localization_service.py").exists())
        for path in (
            "pages/1_Translate.py",
            "ui/translation_review.py",
            "ui/llm_package.py",
        ):
            source = Path(path).read_text()
            self.assertNotIn("Manual edit", source)
            self.assertNotIn("st.text_area", source)
            self.assertNotIn("render_manual_editor", source)

    def test_llm_ui_uses_local_json_upload(self):
        source = Path("ui/llm_package.py").read_text()
        removed_provider_symbols = (
            "Open" + "AITranslationService",
            "OPEN" + "AI_API_KEY",
            "responses" + ".create",
        )
        self.assertIn("st.file_uploader", source)
        self.assertIn("parse_localization_upload_json", source)
        self.assertIn("st.code", source)
        for symbol in removed_provider_symbols:
            self.assertNotIn(symbol, source)

    def test_llm_translation_controls_are_upload_only(self):
        source = Path("ui/llm_package.py").read_text()

        self.assertIn('id="translate-form"', source)
        self.assertIn("st.page_link", source)
        self.assertIn("st.file_uploader", source)
        self.assertIn("parse_localization_upload_json", source)
        self.assertNotIn("prompt_target_codes", source)
        self.assertNotIn("Generate prompt", source)
        self.assertNotIn("build_llm_translation_package", source)
        self.assertNotIn("build_llm_translation_prompt", source)
        self.assertNotIn("select_next_llm_languages", source)

    def test_external_llm_flow_is_visible_before_prompt_preparation(self):
        source = Path("ui/llm_package.py").read_text()

        self.assertIn("External LLM", source)
        self.assertIn("1. (Optional) Prepare prompt", source)
        self.assertIn("2. Generate JSON in an external LLM", source)
        self.assertIn("3. Upload JSON", source)
        self.assertIn("disabled=not upload_ready", source)

    def test_llm_guide_describes_selected_references_in_external_context(self):
        guide = Path("docs/llm-localizations.md").read_text()

        self.assertIn("selected existing localizations", guide)
        self.assertIn("reference", guide.lower())

    def test_llm_prompt_page_contains_short_source_quality_guide(self):
        source = Path("ui/llm_prompt.py").read_text()

        self.assertIn("quality guide", source.lower())
        self.assertIn("2–3", source)
        self.assertIn("st.expander", source)

    def test_faq_is_static_and_does_not_use_youtube_bootstrap(self):
        page_source = Path("pages/3_FAQ.py").read_text()
        ui_source = Path("ui/faq.py").read_text()

        self.assertIn("render_faq_page", page_source)
        self.assertNotIn("bootstrap_app_context", page_source)
        self.assertNotIn("YoutubeService", page_source)
        self.assertNotIn("fetch_", page_source)
        self.assertNotIn("bootstrap_app_context", ui_source)
        self.assertIn("st.expander", ui_source)

    def test_translate_page_copy_describes_unified_workflow(self):
        source = Path("streamlit_app.py").read_text()

        self.assertIn("Translate", source)
        self.assertIn("LLM Translation prompt", source)
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

    def test_translate_page_does_not_require_visible_page_membership(self):
        source = Path("pages/1_Translate.py").read_text()
        self.assertNotIn("selected video is on another page", source.lower())

    def test_sidebar_uses_shared_bootstrap_without_channel_logo(self):
        source = Path("ui/sidebar.py").read_text()
        bootstrap_source = Path("streamlit_app.py").read_text()
        self.assertNotIn('class="channel-logo"', source)
        self.assertIn("render_app_sidebar", bootstrap_source)


if __name__ == "__main__":
    unittest.main()
