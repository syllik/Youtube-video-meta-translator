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

        self.assertIn('"manual"', root_source)
        self.assertIn('"llm"', root_source)
        self.assertNotIn('"machine"', root_source)
        self.assertFalse(Path("pages/1_Machine_translate.py").exists())
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

    def test_llm_ui_uses_prompt_generation_and_local_json_upload(self):
        source = Path("ui/llm_package.py").read_text()
        self.assertIn("st.file_uploader", source)
        self.assertIn("Generate prompt for next 10 languages", source)
        self.assertIn("parse_llm_upload_json", source)
        self.assertIn("st.code", source)
        self.assertNotIn("OpenAITranslationService", source)
        self.assertNotIn("OPENAI_API_KEY", source)

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
