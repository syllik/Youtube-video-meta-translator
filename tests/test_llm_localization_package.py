import json
import unittest

from language_catalog import (
    YouTubeLanguage,
    YouTubeLanguageCatalog,
    build_language_catalog,
)
from llm_localization_package import (
    LlmResponseError,
    build_llm_output_schema,
    build_llm_translation_package,
    build_llm_translation_prompt,
    calculate_llm_translation_progress,
    parse_llm_translation_output,
    select_next_llm_languages,
    split_languages_into_batches,
)


class LlmLocalizationPackageTests(unittest.TestCase):
    def setUp(self):
        self.video_resource = {
            "id": "video-1",
            "snippet": {
                "title": "Waterfall",
                "description": "Wind above the falls.",
                "defaultLanguage": "en",
            },
            "localizations": {
                "de": {
                    "title": "Wasserfall",
                    "description": "Wind über den Wasserfällen.",
                }
            },
        }
        self.catalog = YouTubeLanguageCatalog(
            source="YouTube Data API v3 i18nLanguages.list",
            fetched_at="2026-08-27T16:30:00.000Z",
            hl="ru",
            languages=tuple(
                YouTubeLanguage(
                    "code-{}".format(index),
                    "code-{}".format(index),
                    "Language {}".format(index),
                )
                for index in range(11)
            ),
        )
        self.progress_catalog = YouTubeLanguageCatalog(
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
        self.progress_video_resource = {
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
        self.expected_next_ten_codes = [
            "code-6", "code-10", "code-1", "code-3", "code-2",
            "code-9", "code-7", "code-8", "code-5", "code-4"
        ]

    def test_progress_excludes_default_and_canonicalizes_existing_codes(self):
        progress = calculate_llm_translation_progress(
            self.progress_video_resource, self.progress_catalog
        )

        self.assertEqual(progress.current, 2)
        self.assertEqual(progress.total, 4)
        self.assertEqual(
            [language.code for language in progress.missing], ["es", "fr"]
        )

    def test_next_selection_is_limited_to_ten(self):
        progress = calculate_llm_translation_progress(
            self.progress_video_resource, self.eleven_language_catalog
        )

        self.assertEqual(
            [language.code for language in select_next_llm_languages(progress)],
            self.expected_next_ten_codes,
        )

    def test_package_uses_video_default_fields_and_existing_localizations(self):
        package = build_llm_translation_package(
            self.video_resource, self.catalog, self.catalog.languages[:2]
        )

        self.assertEqual(
            package["source"],
            {
                "videoId": "video-1",
                "title": "Waterfall",
                "description": "Wind above the falls.",
                "defaultLanguage": "en",
            },
        )
        self.assertEqual(package["existingLocalizations"]["de"]["title"], "Wasserfall")
        self.assertEqual(
            [item["code"] for item in package["languages"]], ["code-0", "code-1"]
        )

    def test_catalog_is_split_into_batches_of_ten(self):
        batches = split_languages_into_batches(self.catalog.languages, batch_size=10)

        self.assertEqual([len(batch) for batch in batches], [10, 1])
        self.assertEqual(batches[0][0].code, "code-0")
        self.assertEqual(batches[1][0].code, "code-10")

    def test_prompt_requires_direct_youtube_map_without_file_wrapper(self):
        package = build_llm_translation_package(
            self.video_resource, self.catalog, self.catalog.languages[:2]
        )

        prompt = build_llm_translation_prompt(package)

        self.assertIn("source.title", prompt)
        self.assertIn("existingLocalizations", prompt)
        self.assertIn("directly by the exact language codes", prompt)
        self.assertIn("Do not return a wrapper", prompt)
        self.assertNotIn("downloadable file", prompt.lower())
        self.assertNotIn("youtube-localizations.json", prompt)

    def test_output_schema_has_only_expected_language_keys(self):
        schema = build_llm_output_schema(("en-GB", "sr-Latn"))

        self.assertEqual(schema["required"], ["en-GB", "sr-Latn"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["properties"]), {"en-GB", "sr-Latn"})
        self.assertFalse(schema["properties"]["en-GB"]["additionalProperties"])

    def test_output_parser_rejects_wrapper_missing_and_extra_codes(self):
        valid = json.dumps(
            {
                "en-GB": {"title": "British", "description": "Text"},
                "sr-Latn": {"title": "Serbian", "description": "Text"},
            }
        )
        parsed = parse_llm_translation_output(valid, ("en-GB", "sr-Latn"))

        self.assertEqual(set(parsed), {"en-GB", "sr-Latn"})

        for document in (
            {"languages": {}},
            {"en-GB": {"title": "British", "description": "Text"}},
            {
                "en-GB": {"title": "British", "description": "Text"},
                "sr-Latn": {"title": "Serbian", "description": "Text"},
                "catalog": {"title": "Wrong", "description": "Wrong"},
            },
        ):
            with self.assertRaises(LlmResponseError):
                parse_llm_translation_output(json.dumps(document), ("en-GB", "sr-Latn"))


if __name__ == "__main__":
    unittest.main()
