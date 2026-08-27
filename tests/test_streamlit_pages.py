import importlib
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

from streamlit_app import page_title
from ui.channel_header import CHANNEL_LOGO_SIZE


class StreamlitBootstrapTests(unittest.TestCase):
    def test_page_titles_are_explicit(self):
        self.assertEqual(page_title("machine"), "Machine translate")
        self.assertEqual(page_title("manual"), "Manual translate")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            page_title("legacy")

    def test_import_does_not_construct_youtube_client(self):
        sys.modules.pop("streamlit_app", None)
        with patch("youtube_account.YoutubeApi") as constructor:
            importlib.import_module("streamlit_app")
            constructor.assert_not_called()

    def test_machine_page_contains_machine_components_only(self):
        source = Path("pages/1_Machine_translate.py").read_text()
        self.assertIn("render_machine_controls", source)
        self.assertIn("render_video_list", source)
        self.assertIn("sync_visible_checkbox_state", source)
        self.assertIn("reconcile_select_all_channel", source)
        self.assertNotIn("render_manual_editor", source)

    def test_manual_page_contains_manual_components_only(self):
        source = Path("pages/2_Manual_translate.py").read_text()
        self.assertIn("render_manual_editor", source)
        self.assertIn("render_video_list", source)
        self.assertNotIn("render_machine_controls", source)

    def test_manual_video_selection_uses_card_buttons_not_radio(self):
        source = Path("ui/video_list.py").read_text()
        self.assertNotIn("st.radio", source)
        self.assertIn('"Selected" if is_selected else "Select"', source)

    def test_manual_page_explains_selection_from_another_page(self):
        source = Path("pages/2_Manual_translate.py").read_text()
        self.assertIn("selected video is on another page", source.lower())

    def test_channel_logo_is_large_enough_for_the_summary_card(self):
        self.assertGreaterEqual(CHANNEL_LOGO_SIZE, 112)
        source = Path("ui/channel_header.py").read_text()
        self.assertGreaterEqual(source.count("CHANNEL_LOGO_SIZE"), 2)


if __name__ == "__main__":
    unittest.main()
