import importlib
import json
import tempfile
import unittest
from pathlib import Path

from codex_localization_runner import CodexLocalizationError
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from llm_localization_package import parse_llm_upload_json


try:
    generator_module = importlib.import_module("codex_localization_generator")
except ModuleNotFoundError:
    generator_module = None


class CodexLocalizationGeneratorTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(generator_module, "generator module is not implemented")
        self.video_resource = {
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {
                "DE": {"title": "Wasserfall", "description": "Wind"},
            },
        }
        self.catalog = YouTubeLanguageCatalog(
            source="live",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("en", "en", "English"),
                YouTubeLanguage("de", "de", "German"),
                YouTubeLanguage("fr", "fr", "French"),
                YouTubeLanguage("es", "es", "Spanish"),
                YouTubeLanguage("ja", "ja", "Japanese"),
            ),
        )

    @staticmethod
    def _success_batch(package, schema):
        return {
            code: {"title": "Title " + code, "description": "Text " + code}
            for code in package["expectedLanguageCodes"]
        }

    def test_selection_excludes_default_and_existing_and_preserves_order(self):
        calls = []

        def run_batch(package, schema):
            calls.append(package["expectedLanguageCodes"])
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            run_batch=run_batch,
        )

        self.assertEqual(calls, [["fr", "es", "ja"]])
        self.assertEqual(tuple(result), ("fr", "es", "ja"))
        self.assertNotIn("en", result)
        self.assertNotIn("de", result)

    def test_batch_size_two_creates_deterministic_two_plus_remainder_calls(self):
        calls = []

        def run_batch(package, schema):
            calls.append(package["expectedLanguageCodes"])
            return self._success_batch(package, schema)

        generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            batch_size=2,
            run_batch=run_batch,
        )

        self.assertEqual(calls, [["fr", "es"], ["ja"]])

    def test_max_languages_limits_targets_before_batching(self):
        calls = []

        def run_batch(package, schema):
            calls.append(package["expectedLanguageCodes"])
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            batch_size=1,
            max_languages=2,
            run_batch=run_batch,
        )

        self.assertEqual(calls, [["fr"], ["es"]])
        self.assertEqual(tuple(result), ("fr", "es"))

    def test_first_batch_failure_is_retried_exactly_once(self):
        attempts = []

        def run_batch(package, schema):
            attempts.append(tuple(package["expectedLanguageCodes"]))
            if len(attempts) == 1:
                raise CodexLocalizationError("temporary failure")
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            run_batch=run_batch,
        )

        self.assertEqual(attempts, [("fr", "es", "ja"), ("fr", "es", "ja")])
        self.assertEqual(tuple(result), ("fr", "es", "ja"))

    def test_second_batch_failure_raises_generation_error(self):
        attempts = 0

        def run_batch(package, schema):
            nonlocal attempts
            attempts += 1
            raise CodexLocalizationError("persistent failure")

        with self.assertRaises(generator_module.CodexGenerationError):
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                run_batch=run_batch,
            )

        self.assertEqual(attempts, 2)

    def test_invalid_batch_size_max_languages_and_retry_count_are_rejected(self):
        for batch_size in (0, 11):
            with self.subTest(batch_size=batch_size):
                with self.assertRaises(ValueError):
                    generator_module.generate_missing_localizations(
                        self.video_resource,
                        self.catalog,
                        batch_size=batch_size,
                    )

        for max_languages in (0, -1):
            with self.subTest(max_languages=max_languages):
                with self.assertRaises(ValueError):
                    generator_module.generate_missing_localizations(
                        self.video_resource,
                        self.catalog,
                        max_languages=max_languages,
                    )

        with self.assertRaises(ValueError):
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                retry_count=-1,
            )

    def test_no_missing_languages_returns_empty_without_calling_codex(self):
        video_resource = dict(self.video_resource)
        video_resource["localizations"] = {
            "de": {"title": "Wasserfall", "description": "Wind"},
            "fr": {"title": "Cascade", "description": "Texte"},
            "es": {"title": "Cascada", "description": "Texto"},
            "ja": {"title": "滝", "description": "風"},
        }
        calls = []

        def run_batch(package, schema):
            calls.append(package)
            return {}

        self.assertEqual(
            generator_module.generate_missing_localizations(
                video_resource,
                self.catalog,
                run_batch=run_batch,
            ),
            {},
        )
        self.assertEqual(calls, [])

    def test_merged_result_passes_existing_exact_parser(self):
        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            batch_size=2,
            run_batch=self._success_batch,
        )

        parsed = parse_llm_upload_json(json.dumps(result), tuple(result))

        self.assertTrue(parsed.is_valid)

    def test_atomic_writer_replaces_only_after_successful_serialization(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "localizations.json"
            output_path.write_text('{"old": true}\n', encoding="utf-8")

            generator_module.write_localizations_atomic(
                {"fr": {"title": "Cascade", "description": "Texte"}},
                output_path,
            )
            self.assertIn("Cascade", output_path.read_text(encoding="utf-8"))

            output_path.write_text('{"keep": true}\n', encoding="utf-8")
            with self.assertRaises(TypeError):
                generator_module.write_localizations_atomic(
                    {"fr": object()},
                    output_path,
                )
            self.assertEqual(
                output_path.read_text(encoding="utf-8"), '{"keep": true}\n'
            )
            self.assertEqual(
                list(Path(directory).glob(".localizations.json.*.tmp")), []
            )


if __name__ == "__main__":
    unittest.main()
