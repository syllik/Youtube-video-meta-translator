import json
import unittest

from localizations import (
    LocalizationIssue,
    LocalizationValue,
    ParsedLocalizations,
    build_localization_diff,
    build_localization_plan,
    build_video_update_payload,
    merge_localizations,
    parse_localizations_json,
)


SUPPORTED = {"en", "es", "fr", "de", "pt-BR"}

VIDEO_RESOURCE = {
    "id": "video-1",
    "snippet": {
        "title": "Original title",
        "description": "Original description",
        "categoryId": "22",
        "defaultLanguage": "en",
        "tags": ["keep-me"],
    },
    "localizations": {
        "de": {"title": "Alt", "description": "Alt"},
        "fr": {"title": "Même", "description": "Même"},
    },
}


class ParseLocalizationsTests(unittest.TestCase):
    def test_valid_object_preserves_unicode_and_newlines(self):
        raw = json.dumps(
            {"es": {"title": "Título", "description": "Línea 1\nLínea 2"}}
        )

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertTrue(result.is_valid)
        self.assertEqual(
            result.entries["es"],
            LocalizationValue("Título", "Línea 1\nLínea 2"),
        )

    def test_malformed_json_is_document_invalid(self):
        result = parse_localizations_json('{"es":', SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertIsNone(result.invalid_entries[0].language_code)
        self.assertIsNone(result.invalid_entries[0].path)

    def test_malformed_json_reports_line_and_column(self):
        result = parse_localizations_json(
            '{\n  "es": {\n    "title": "broken",\n', SUPPORTED
        )

        self.assertFalse(result.is_valid)
        self.assertRegex(result.invalid_entries[0].message, r"line \d+, column \d+")

    def test_all_invalid_entries_are_reported(self):
        raw = json.dumps(
            {
                "de-unknown": {"title": "Unsupported", "description": "x"},
                "es": {"title": "", "description": "x"},
                "fr": {"title": "Missing description"},
                "en": {"title": 123, "description": "x"},
            }
        )

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            {issue.language_code for issue in result.invalid_entries},
            {"de-unknown", "es", "fr", "en"},
        )
        self.assertEqual(result.entries, {})

    def test_valid_entries_remain_reportable_when_another_entry_is_invalid(self):
        raw = json.dumps(
            {
                "es": {"title": "Nuevo", "description": "Nuevo"},
                "de": {"title": 123, "description": "x"},
            }
        )

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.entries["es"],
            LocalizationValue("Nuevo", "Nuevo"),
        )
        self.assertEqual(
            [issue.language_code for issue in result.invalid_entries], ["de"]
        )

    def test_title_and_description_limits_are_inclusive(self):
        raw = json.dumps(
            {
                "es": {
                    "title": "t" * 100,
                    "description": "d" * 5000,
                }
            }
        )

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertTrue(result.is_valid)

    def test_empty_document_and_unknown_fields_are_invalid(self):
        empty = parse_localizations_json("{}", SUPPORTED)
        extra = parse_localizations_json(
            json.dumps(
                {"es": {"title": "x", "description": "y", "extra": "z"}}
            ),
            SUPPORTED,
        )

        self.assertFalse(empty.is_valid)
        self.assertFalse(extra.is_valid)

    def test_regional_language_code_is_normalized_without_becoming_generic(self):
        raw = json.dumps(
            {"pt-br": {"title": "Título", "description": "Descrição"}}
        )

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertTrue(result.is_valid)
        self.assertIn("pt-BR", result.entries)
        self.assertNotIn("pt", result.entries)

    def test_field_errors_include_language_and_field_path(self):
        raw = json.dumps({"es": {"title": "", "description": 4}})

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertEqual(
            {issue.path for issue in result.invalid_entries},
            {"es.title", "es.description"},
        )


class LocalizationDiffTests(unittest.TestCase):
    def test_diff_reports_added_changed_and_unchanged(self):
        existing = {
            "de": LocalizationValue("Alt", "Alt"),
            "fr": LocalizationValue("Même", "Même"),
        }
        submitted = {
            "de": LocalizationValue("Nouveau", "Alt"),
            "fr": LocalizationValue("Même", "Même"),
            "es": LocalizationValue("Nuevo", "Nuevo"),
        }

        result = build_localization_diff(existing, submitted)

        self.assertEqual(
            [(item.language_code, item.status) for item in result],
            [("de", "changed"), ("es", "added"), ("fr", "unchanged")],
        )

    def test_payload_merges_submitted_values_and_preserves_omitted_languages(self):
        submitted = {"es": LocalizationValue("Nuevo", "Nuevo")}

        payload = build_video_update_payload(VIDEO_RESOURCE, submitted)

        self.assertEqual(
            payload["localizations"]["de"], {"title": "Alt", "description": "Alt"}
        )
        self.assertEqual(
            payload["localizations"]["fr"],
            {"title": "Même", "description": "Même"},
        )
        self.assertEqual(
            payload["localizations"]["es"],
            {"title": "Nuevo", "description": "Nuevo"},
        )
        self.assertEqual(payload["snippet"]["tags"], ["keep-me"])

    def test_merge_localizations_does_not_drop_omitted_existing_values(self):
        existing = {
            "de": {"title": "Old DE", "description": "..."},
            "ru": {"title": "RU", "description": "..."},
        }
        submitted = {
            "de": LocalizationValue("New DE", "..."),
            "fr": LocalizationValue("FR", "..."),
        }

        result = merge_localizations(existing, submitted)

        self.assertEqual(result["de"]["title"], "New DE")
        self.assertEqual(result["ru"], {"title": "RU", "description": "..."})
        self.assertEqual(result["fr"], {"title": "FR", "description": "..."})

    def test_payload_does_not_mutate_the_fetched_resource(self):
        submitted = {"de": LocalizationValue("Nouveau", "Nouveau")}

        build_video_update_payload(VIDEO_RESOURCE, submitted)

        self.assertEqual(VIDEO_RESOURCE["localizations"]["de"]["title"], "Alt")

    def test_invalid_plan_has_no_payload(self):
        parsed = ParsedLocalizations(
            entries={},
            issues=(LocalizationIssue("es", "invalid title"),),
        )

        plan = build_localization_plan(VIDEO_RESOURCE, parsed)

        self.assertFalse(plan.is_valid)
        self.assertIsNone(plan.payload)

    def test_plan_records_preserved_language_codes(self):
        parsed = parse_localizations_json(
            json.dumps({"de": {"title": "Alt", "description": "Alt"}}),
            SUPPORTED,
        )

        plan = build_localization_plan(VIDEO_RESOURCE, parsed)

        self.assertTrue(plan.is_valid)
        self.assertEqual(plan.preserved_language_codes, ("fr",))


if __name__ == "__main__":
    unittest.main()
