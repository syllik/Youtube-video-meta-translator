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

    def test_explicit_target_codes_are_normalized_and_respected(self):
        calls = []

        def run_batch(package, schema):
            calls.append(package["expectedLanguageCodes"])
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            target_codes=("JA", "fr"),
            run_batch=run_batch,
        )

        self.assertEqual(calls, [["fr", "ja"]])
        self.assertEqual(tuple(result), ("fr", "ja"))

    def test_empty_explicit_target_codes_skip_generation(self):
        calls = []

        def run_batch(package, schema):
            calls.append(package)
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            target_codes=(),
            run_batch=run_batch,
        )

        self.assertEqual(result, {})
        self.assertEqual(calls, [])

    def test_explicit_target_codes_reject_unknown_existing_source_and_duplicate(self):
        for target_codes in (("unknown",), ("de",), ("en",), ("fr", "FR")):
            with self.subTest(target_codes=target_codes):
                with self.assertRaises(ValueError):
                    generator_module.generate_missing_localizations(
                        self.video_resource,
                        self.catalog,
                        target_codes=target_codes,
                        run_batch=self._success_batch,
                    )

    def test_explicit_selection_larger_than_ten_is_batched_by_llm_batch_size(self):
        languages = tuple(
            [YouTubeLanguage("en", "en", "English")]
            + [YouTubeLanguage("code-{}".format(index), "code-{}".format(index), "Language")
               for index in range(12)]
        )
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=languages,
        )
        video = {
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {},
        }
        calls = []

        def run_batch(package, schema):
            calls.append(package["expectedLanguageCodes"])
            return self._success_batch(package, schema)

        result = generator_module.generate_missing_localizations(
            video,
            catalog,
            target_codes=tuple("code-{}".format(index) for index in range(12)),
            run_batch=run_batch,
        )

        self.assertEqual(len(calls), 2)
        self.assertEqual(len(calls[0]), 10)
        self.assertEqual(len(calls[1]), 2)
        self.assertEqual(tuple(result), tuple("code-{}".format(index) for index in range(12)))

    def test_twenty_five_targets_make_ten_ten_five_calls_in_order(self):
        codes = tuple("code-{}".format(index) for index in range(25))
        catalog = YouTubeLanguageCatalog(
            source="test",
            fetched_at="2026-08-29T00:00:00Z",
            hl="en",
            languages=tuple(
                [YouTubeLanguage("en", "en", "English")]
                + [YouTubeLanguage(code, code, code) for code in codes]
            ),
        )
        video = {
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {},
        }
        calls = []

        def run_batch(package, schema):
            calls.append(tuple(package["expectedLanguageCodes"]))
            return self._success_batch(package, schema)

        generator_module.generate_missing_localizations(
            video,
            catalog,
            target_codes=codes,
            run_batch=run_batch,
        )

        self.assertEqual(calls, [codes[:10], codes[10:20], codes[20:]])

    def test_completion_callback_receives_validated_batch_and_cumulative_document(self):
        callbacks = []

        def on_batch_completed(index, total, codes, batch_document, cumulative_document):
            callbacks.append(
                (index, total, codes, batch_document, cumulative_document)
            )

        generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            batch_size=2,
            run_batch=self._success_batch,
            on_batch_completed=on_batch_completed,
        )

        self.assertEqual(
            callbacks,
            [
                (
                    1,
                    2,
                    ("fr", "es"),
                    {
                        "fr": {"title": "Title fr", "description": "Text fr"},
                        "es": {"title": "Title es", "description": "Text es"},
                    },
                    {
                        "fr": {"title": "Title fr", "description": "Text fr"},
                        "es": {"title": "Title es", "description": "Text es"},
                    },
                ),
                (
                    2,
                    2,
                    ("ja",),
                    {"ja": {"title": "Title ja", "description": "Text ja"}},
                    {
                        "fr": {"title": "Title fr", "description": "Text fr"},
                        "es": {"title": "Title es", "description": "Text es"},
                        "ja": {"title": "Title ja", "description": "Text ja"},
                    },
                ),
            ],
        )

    def test_invalid_batch_does_not_fire_completion_callback(self):
        callbacks = []

        def invalid_batch(package, schema):
            return {"fr": {"title": "missing description"}}

        with self.assertRaises(generator_module.CodexGenerationError):
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                run_batch=invalid_batch,
                retry_count=0,
                on_batch_completed=lambda *args: callbacks.append(args),
            )

        self.assertEqual(callbacks, [])

    def test_prior_completion_callback_survives_a_later_failed_batch(self):
        callbacks = []

        def run_batch(package, schema):
            if package["expectedLanguageCodes"] == ["ja"]:
                raise CodexLocalizationError("persistent failure")
            return self._success_batch(package, schema)

        with self.assertRaises(generator_module.CodexGenerationError):
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                batch_size=2,
                run_batch=run_batch,
                retry_count=0,
                on_batch_completed=lambda *args: callbacks.append(args),
            )

        self.assertEqual(len(callbacks), 1)
        self.assertEqual(callbacks[0][0:3], (1, 2, ("fr", "es")))

    def test_every_batch_receives_the_same_selected_source_context(self):
        packages = []

        def run_batch(package, schema):
            packages.append(package)
            return self._success_batch(package, schema)

        generator_module.generate_missing_localizations(
            self.video_resource,
            self.catalog,
            batch_size=2,
            selected_source_codes=("en", "de"),
            run_batch=run_batch,
        )

        self.assertEqual(len(packages), 2)
        self.assertEqual(
            [package["source"] for package in packages],
            [packages[0]["source"], packages[0]["source"]],
        )
        self.assertEqual(
            packages[0]["source"]["references"],
            [{"languageCode": "de", "title": "Wasserfall", "description": "Wind"}],
        )

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

    def test_cancellation_is_not_retried(self):
        attempts = []

        def run_batch(package, schema):
            attempts.append(tuple(package["expectedLanguageCodes"]))
            raise generator_module.CodexLocalizationCancelled("Generation stopped.")

        with self.assertRaises(generator_module.CodexLocalizationCancelled):
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                run_batch=run_batch,
                retry_count=1,
            )

        self.assertEqual(attempts, [("fr", "es", "ja")])

    def test_batch_failure_explains_scope_retry_and_no_partial_merge(self):
        def run_batch(package, schema):
            raise CodexLocalizationError("temporary Codex failure")

        with self.assertRaises(generator_module.CodexGenerationError) as context:
            generator_module.generate_missing_localizations(
                self.video_resource,
                self.catalog,
                batch_size=2,
                run_batch=run_batch,
            )

        message = str(context.exception)
        self.assertIn("batch 1 / 2", message)
        self.assertIn("fr, es", message)
        self.assertIn("temporary Codex failure", message)
        self.assertIn("retry", message.lower())
        self.assertIn("failed batch was not merged", message)
        self.assertIn("Previously completed batches remain available", message)

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

    def test_script_subtag_canonicalization_keeps_catalog_code_order(self):
        catalog = YouTubeLanguageCatalog(
            source="live",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=(
                YouTubeLanguage("sr-Latn", "sr-Latn", "Serbian Latin"),
            ),
        )
        video_resource = {
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {},
        }

        def run_batch(package, schema):
            return {
                "sr-LATN": {
                    "title": "Vodopad",
                    "description": "Vetar iznad vodopada.",
                }
            }

        try:
            result = generator_module.generate_missing_localizations(
                video_resource,
                catalog,
                run_batch=run_batch,
            )
        except KeyError as error:
            self.fail("script-subtag result must use the catalog code: {}".format(error))

        self.assertEqual(tuple(result), ("sr-Latn",))
        self.assertEqual(result["sr-Latn"]["title"], "Vodopad")

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
