import sys
import unittest
from unittest.mock import patch

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from language_labels import format_language_label


class LanguageLabelTests(unittest.TestCase):
    def setUp(self):
        self.catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "Английский", "English"),
                YouTubeLanguage("ru", "ru", "Русский", "Russian"),
                YouTubeLanguage("pt-BR", "pt-BR", "Португальский (Бразилия)", "Portuguese (Brazil)"),
                YouTubeLanguage("es-419", "es-419", "Испанский (Латинская Америка)", "Spanish (Latin America)"),
            ),
        )

    def test_formats_code_before_english_name(self):
        self.assertEqual(
            format_language_label("en", self.catalog),
            "en — English",
        )
        self.assertEqual(
            format_language_label("ru", self.catalog),
            "ru — Russian",
        )

    def test_formats_regional_code_without_changing_its_casing(self):
        self.assertEqual(
            format_language_label("pt-BR", self.catalog),
            "pt-BR — Portuguese (Brazil)",
        )
        self.assertEqual(
            format_language_label("es-419", self.catalog),
            "es-419 — Spanish (Latin America)",
        )

    def test_unknown_code_falls_back_to_the_exact_code(self):
        self.assertEqual(format_language_label("xx-YY", self.catalog), "xx-YY")

    def test_formatter_does_not_use_localized_catalog_name_as_english_name(self):
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="ru",
            languages=(YouTubeLanguage("km", "km", "Кхмерский"),),
        )

        self.assertEqual(format_language_label("km", catalog), "km")

    def test_badges_use_the_same_code_first_label_format(self):
        from ui.badges import render_language_badges

        class FakeStreamlit:
            def __init__(self):
                self.messages = []

            def markdown(self, message, **_kwargs):
                self.messages.append(message)

        fake = FakeStreamlit()
        with patch.dict(sys.modules, {"streamlit": fake}):
            render_language_badges(("pt-BR",), label="Selected languages", catalog=self.catalog)

        self.assertIn("pt-BR — Portuguese (Brazil)", fake.messages[0])


if __name__ == "__main__":
    unittest.main()
