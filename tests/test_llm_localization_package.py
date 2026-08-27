import unittest

from language_catalog import (
    YouTubeLanguage,
    YouTubeLanguageCatalog,
    build_language_catalog,
)
from llm_localization_package import (
    LlmTranslationProgress,
    calculate_llm_translation_progress,
    select_next_llm_languages,
)


class LlmLocalizationPackageTests(unittest.TestCase):
    def setUp(self):
        self.video_resource = {
            "id": "video-1",
            "snippet": {
                "title": "Waterfall",
                "description": "Wind above the falls.",
                "defaultLanguage": "EN",
            },
            "localizations": {
                "de": {"title": "Wasserfall", "description": "Wind"},
                "PT-br": {"title": "Cachoeira", "description": "Vento"},
            },
        }
        self.catalog = YouTubeLanguageCatalog(
            source="YouTube Data API v3 i18nLanguages.list",
            fetched_at="2026-08-27T16:30:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
                YouTubeLanguage("pt-BR", "pt-BR", "Portuguese (Brazil)"),
                YouTubeLanguage("es", "es", "Spanish"),
                YouTubeLanguage("fr", "fr", "French"),
            ),
        )
        self.eleven_language_catalog = build_language_catalog(
            {
                "items": [
                    {"id": "code-0", "snippet": {"hl": "code-0", "name": "Zulu"}},
                    {"id": "code-1", "snippet": {"hl": "code-1", "name": "English"}},
                    {"id": "code-2", "snippet": {"hl": "code-2", "name": "German"}},
                    {"id": "code-3", "snippet": {"hl": "code-3", "name": "French"}},
                    {"id": "code-4", "snippet": {"hl": "code-4", "name": "Spanish"}},
                    {"id": "code-5", "snippet": {"hl": "code-5", "name": "Portuguese (Brazil)"}},
                    {"id": "code-6", "snippet": {"hl": "code-6", "name": "Arabic"}},
                    {"id": "code-7", "snippet": {"hl": "code-7", "name": "Japanese"}},
                    {"id": "code-8", "snippet": {"hl": "code-8", "name": "Korean"}},
                    {"id": "code-9", "snippet": {"hl": "code-9", "name": "Italian"}},
                    {"id": "code-10", "snippet": {"hl": "code-10", "name": "Chinese (Simplified)"}},
                ]
            }
        )

    def test_progress_excludes_default_and_canonicalizes_existing_codes(self):
        progress = calculate_llm_translation_progress(self.video_resource, self.catalog)

        self.assertEqual(progress.current, 2)
        self.assertEqual(progress.total, 4)
        self.assertEqual(
            [language.code for language in progress.missing], ["es", "fr"]
        )

    def test_next_selection_is_limited_to_ten(self):
        progress = calculate_llm_translation_progress(
            self.video_resource, self.eleven_language_catalog
        )

        self.assertEqual(
            [language.code for language in select_next_llm_languages(progress)],
            [
                "code-6", "code-10", "code-1", "code-3", "code-2",
                "code-9", "code-7", "code-8", "code-5", "code-4",
            ],
        )

    def test_next_selection_rejects_non_positive_batch_sizes(self):
        progress = LlmTranslationProgress(0, 0, ())

        for batch_size in (0, -1):
            with self.assertRaises(ValueError):
                select_next_llm_languages(progress, batch_size=batch_size)


if __name__ == "__main__":
    unittest.main()
