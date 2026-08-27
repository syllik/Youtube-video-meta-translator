import importlib
import sys
import unittest
from unittest.mock import patch

from streamlit_app import page_title


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


if __name__ == "__main__":
    unittest.main()
