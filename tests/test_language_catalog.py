import tempfile
import unittest
from pathlib import Path

from language_catalog import (
    LanguageCatalogError,
    METADATA_LANGUAGE_CATALOG_SOURCE,
    build_metadata_language_catalog,
    build_language_catalog,
    load_metadata_language_catalog,
)


class MetadataLanguageCatalogTests(unittest.TestCase):
    def test_checked_in_catalog_has_metadata_scope_and_known_variants(self):
        catalog = load_metadata_language_catalog()

        self.assertEqual(catalog.source, METADATA_LANGUAGE_CATALOG_SOURCE)
        self.assertEqual(len(catalog.languages), 238)
        self.assertTrue(all(language.english_name for language in catalog.languages))
        names = {language.code: language.english_name for language in catalog.languages}
        self.assertEqual(names["en"], "English")
        self.assertEqual(names["ru"], "Russian")
        self.assertEqual(names["km"], "Khmer")
        self.assertEqual(names["pt-BR"], "Portuguese (Brazil)")
        self.assertEqual(names["es-419"], "Spanish (Latin America)")
        self.assertIn("be", catalog.codes)
        self.assertIn("en-GB", catalog.codes)
        self.assertIn("es-419", catalog.codes)
        self.assertIn("zh-Hans", catalog.codes)
        self.assertIn("zh-Hant", catalog.codes)
        self.assertIn("sr-Latn", catalog.codes)

    def test_metadata_only_code_is_not_in_a_separate_application_fixture(self):
        application_catalog = build_language_catalog(
            {
                "items": [
                    {"id": "en", "snippet": {"hl": "en", "name": "English"}},
                    {"id": "de", "snippet": {"hl": "de", "name": "German"}},
                ]
            }
        )
        metadata_catalog = load_metadata_language_catalog()

        self.assertNotIn("be", application_catalog.codes)
        self.assertIn("be", metadata_catalog.codes)

    def test_snapshot_rejects_count_mismatch(self):
        document = {
            "scope": "YouTube video metadata localizations",
            "source": "YouTube Studio metadata language picker",
            "reviewedAt": "2026-08-29",
            "count": 2,
            "languages": [{"code": "en", "name": "English"}],
        }

        with self.assertRaisesRegex(LanguageCatalogError, "count"):
            build_metadata_language_catalog(document)

    def test_snapshot_rejects_case_insensitive_duplicate_codes(self):
        document = {
            "scope": "YouTube video metadata localizations",
            "source": "YouTube Studio metadata language picker",
            "reviewedAt": "2026-08-29",
            "count": 2,
            "languages": [
                {"code": "en", "name": "Английский", "englishName": "English"},
                {"code": "EN", "name": "Английский снова", "englishName": "English again"},
            ],
        }

        with self.assertRaisesRegex(LanguageCatalogError, "Duplicate"):
            build_metadata_language_catalog(document)

    def test_loader_fails_closed_for_malformed_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.json"
            path.write_text('{"count": 1}', encoding="utf-8")

            with self.assertRaises(LanguageCatalogError):
                load_metadata_language_catalog(path)

    def test_snapshot_rejects_missing_english_name(self):
        document = {
            "scope": "YouTube video metadata localizations",
            "source": "YouTube Studio metadata language picker",
            "reviewedAt": "2026-08-29",
            "count": 1,
            "languages": [{"code": "en", "name": "Английский"}],
        }

        with self.assertRaisesRegex(LanguageCatalogError, "englishName"):
            build_metadata_language_catalog(document)
