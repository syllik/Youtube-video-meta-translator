import unittest

import llm_localization_package

from language_catalog import (
    YouTubeLanguage,
    YouTubeLanguageCatalog,
    build_language_catalog,
)
from llm_localization_package import (
    LlmTranslationProgress,
    build_selected_llm_languages,
    build_llm_translation_package,
    build_llm_translation_prompt,
    calculate_llm_translation_progress,
    parse_llm_upload_json,
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

    def test_selected_codes_are_normalized_and_returned_in_catalog_order(self):
        progress = calculate_llm_translation_progress(self.video_resource, self.catalog)

        selected = build_selected_llm_languages(progress, ("FR", "es"))

        self.assertEqual([language.code for language in selected], ["es", "fr"])

    def test_selected_codes_reject_default_existing_unknown_duplicate_and_eleventh(self):
        progress = calculate_llm_translation_progress(
            self.video_resource, self.eleven_language_catalog
        )

        for codes in (("en",), ("de",), ("unknown",), ("es", "ES")):
            with self.subTest(codes=codes):
                with self.assertRaises(ValueError):
                    build_selected_llm_languages(progress, codes)

        with self.assertRaises(ValueError):
            build_selected_llm_languages(
                progress,
                tuple(language.code for language in progress.missing[:11]),
            )

    def test_selected_codes_reject_non_positive_limit_and_invalid_values(self):
        progress = calculate_llm_translation_progress(self.video_resource, self.catalog)

        for max_count, codes in ((0, ()), (-1, ()), (10, ("",)), (10, (None,))):
            with self.subTest(max_count=max_count, codes=codes):
                with self.assertRaises(ValueError):
                    build_selected_llm_languages(progress, codes, max_count=max_count)

    def test_package_contains_only_default_source_and_targets(self):
        languages = (
            YouTubeLanguage("code-0", "code-0", "Zulu"),
            YouTubeLanguage("code-1", "code-1", "English"),
        )
        package = build_llm_translation_package(
            self.video_resource, languages
        )

        self.assertEqual(package["source"]["title"], "Waterfall")
        self.assertEqual(package["source"]["description"], "Wind above the falls.")
        self.assertNotIn("existingLocalizations", package)
        self.assertEqual(package["expectedLanguageCodes"], ["code-0", "code-1"])
        self.assertEqual(package["expectedCount"], 2)

    def test_prompt_requires_downloadable_direct_json(self):
        languages = (
            YouTubeLanguage("code-0", "code-0", "Zulu"),
            YouTubeLanguage("code-1", "code-1", "English"),
        )
        package = build_llm_translation_package(
            self.video_resource, languages
        )
        prompt = build_llm_translation_prompt(package)

        self.assertIn("downloadable", prompt.lower())
        self.assertIn("expectedLanguageCodes", prompt)
        self.assertIn("Do not return a wrapper", prompt)
        self.assertNotIn("existingLocalizations", prompt)

    def test_prompt_serializes_unicode_without_ascii_escaping(self):
        video_resource = {
            "snippet": {"title": "Водопад", "description": "Ветер над водопадом."}
        }
        package = build_llm_translation_package(
            video_resource, (YouTubeLanguage("uk", "uk", "Ukrainian"),)
        )

        prompt = build_llm_translation_prompt(package)

        self.assertIn("Водопад", prompt)
        self.assertNotIn("\\u0412", prompt)

    def test_upload_parser_requires_exact_target_codes(self):
        valid = (
            '{"en-GB":{"title":"British","description":"Text"},'
            '"sr-Latn":{"title":"Serbian","description":"Text"}}'
        )
        self.assertTrue(parse_llm_upload_json(valid, ("en-GB", "sr-Latn")).is_valid)

        missing = '{"en-GB":{"title":"British","description":"Text"}}'
        wrapper = '{"languages":{"sr-Latn":{"title":"Serbian","description":"Text"}}}'
        self.assertFalse(
            parse_llm_upload_json(missing, ("en-GB", "sr-Latn")).is_valid
        )
        self.assertFalse(
            parse_llm_upload_json(wrapper, ("en-GB", "sr-Latn")).is_valid
        )

    def test_upload_parser_canonicalizes_casefolded_codes(self):
        parsed = parse_llm_upload_json(
            '{"EN-gb":{"title":"British","description":"Text"}}',
            ("en-GB",),
        )

        self.assertEqual(tuple(parsed.entries), ("en-GB",))

    def test_upload_parser_rejects_duplicate_language_keys(self):
        raw_json = (
            '{"en-GB":{"title":"First","description":"Text"},'
            '"en-GB":{"title":"Second","description":"Text"}}'
        )

        parsed = parse_llm_upload_json(raw_json, ("en-GB",))

        self.assertFalse(parsed.is_valid)
        self.assertEqual(parsed.entries, {})
        self.assertEqual(parsed.issues[0].message, "Duplicate JSON object key: en-GB")

    def test_upload_parser_rejects_duplicate_nested_fields(self):
        for field in ("title", "description"):
            with self.subTest(field=field):
                raw_json = (
                    '{{"en-GB":{{"title":"British","description":"Text",'
                    '"{field}":"Replacement"}}}}'
                ).format(field=field)

                parsed = parse_llm_upload_json(raw_json, ("en-GB",))

                self.assertFalse(parsed.is_valid)
                self.assertEqual(parsed.entries, {})
                self.assertEqual(
                    parsed.issues[0].message,
                    "Duplicate JSON object key: {}".format(field),
                )

    def test_upload_parser_rejects_invalid_json(self):
        parsed = parse_llm_upload_json('{"en-GB":', ("en-GB",))

        self.assertFalse(parsed.is_valid)
        self.assertIn("Invalid JSON", parsed.issues[0].message)

    def test_upload_parser_rejects_extra_fields_and_unknown_codes(self):
        extra_field = '{"en-GB":{"title":"British","description":"Text","note":"extra"}}'
        unknown_code = '{"fr":{"title":"French","description":"Texte"}}'

        self.assertFalse(parse_llm_upload_json(extra_field, ("en-GB",)).is_valid)
        self.assertFalse(parse_llm_upload_json(unknown_code, ("en-GB",)).is_valid)

    def test_upload_parser_rejects_missing_title_or_description(self):
        missing_title = '{"en-GB":{"description":"Text"}}'
        missing_description = '{"en-GB":{"title":"British"}}'

        self.assertFalse(parse_llm_upload_json(missing_title, ("en-GB",)).is_valid)
        self.assertFalse(
            parse_llm_upload_json(missing_description, ("en-GB",)).is_valid
        )

    def test_upload_parser_rejects_over_limit_fields(self):
        title_too_long = '{{"en-GB":{{"title":"{}","description":"Text"}}}}'.format(
            "t" * 101
        )
        description_too_long = (
            '{{"en-GB":{{"title":"British","description":"{}"}}}}'.format(
                "d" * 5001
            )
        )

        self.assertFalse(parse_llm_upload_json(title_too_long, ("en-GB",)).is_valid)
        self.assertFalse(
            parse_llm_upload_json(description_too_long, ("en-GB",)).is_valid
        )

    def test_schema_requires_exact_language_codes_and_localization_fields(self):
        self.assertTrue(
            hasattr(llm_localization_package, "build_llm_localization_schema")
        )
        schema = llm_localization_package.build_llm_localization_schema(
            ("en-GB", "pt-BR")
        )

        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["required"], ["en-GB", "pt-BR"])
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(tuple(schema["properties"]), ("en-GB", "pt-BR"))

        localization = schema["properties"]["en-GB"]
        self.assertEqual(localization["type"], "object")
        self.assertEqual(localization["required"], ["title", "description"])
        self.assertFalse(localization["additionalProperties"])
        self.assertEqual(localization["properties"]["title"]["minLength"], 1)
        self.assertEqual(localization["properties"]["title"]["maxLength"], 100)
        self.assertEqual(
            localization["properties"]["description"]["maxLength"], 5000
        )

    def test_schema_rejects_empty_invalid_and_duplicate_codes(self):
        self.assertTrue(
            hasattr(llm_localization_package, "build_llm_localization_schema")
        )
        for codes in ((), ("",), (None,), ("en-GB", "EN-gb")):
            with self.subTest(codes=codes):
                with self.assertRaises(ValueError):
                    llm_localization_package.build_llm_localization_schema(codes)


if __name__ == "__main__":
    unittest.main()
