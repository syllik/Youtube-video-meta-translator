import json
import tempfile
import unittest
from pathlib import Path

from generate_codex_localizations import main
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from llm_localization_package import parse_llm_upload_json


class EndToEndFakeYoutubeService:
    def __init__(self):
        self.video_ids = []
        self.catalog_requests = []
        self.publish_calls = []
        self.video_resource = {
            "id": "video-e2e",
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {
                "de": {"title": "Wasserfall", "description": "Wind"},
            },
        }
        languages = [
            YouTubeLanguage("en", "en", "English"),
            YouTubeLanguage("de", "de", "German"),
        ]
        languages.extend(
            YouTubeLanguage("code-{}".format(index), "code-{}".format(index), "Language {}".format(index))
            for index in range(11)
        )
        self.catalog = YouTubeLanguageCatalog(
            source="YouTube Data API v3 i18nLanguages.list",
            fetched_at="2026-08-28T00:00:00.000Z",
            hl="ru",
            languages=tuple(languages),
        )

    def get_video_with_localizations(self, video_id):
        self.video_ids.append(video_id)
        return self.video_resource

    def fetch_localization_language_catalog(self, hl="ru", refresh=False):
        self.catalog_requests.append((hl, refresh))
        return self.catalog

    def update_video_localizations(self, payload, if_match=None):
        self.publish_calls.append(payload)
        raise AssertionError("end-to-end generation must not publish")


class CodexLocalizationEndToEndTests(unittest.TestCase):
    def test_cli_generates_ordered_missing_batches_without_existing_context_or_publish(self):
        service = EndToEndFakeYoutubeService()
        login_calls = []
        codex_calls = []

        def login_checker():
            login_calls.append(True)

        def fake_codex_batch(package, schema):
            codex_calls.append((package, schema))
            self.assertNotIn("existingLocalizations", package)
            self.assertEqual(
                schema["required"], package["expectedLanguageCodes"]
            )
            return {
                code: {
                    "title": "Translated " + code,
                    "description": "Translation for " + code,
                }
                for code in package["expectedLanguageCodes"]
            }

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "localizations.json"
            result = main(
                [
                    "--video-id",
                    "video-e2e",
                    "--batch-size",
                    "10",
                    "--output",
                    str(output_path),
                ],
                service_factory=lambda: service,
                login_checker=login_checker,
                run_batch=fake_codex_batch,
            )

            self.assertEqual(result, 0)
            document = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(login_calls, [True])
        self.assertEqual(service.video_ids, ["video-e2e"])
        self.assertEqual(service.catalog_requests, [("ru", True)])
        self.assertEqual(
            [len(package["expectedLanguageCodes"]) for package, _ in codex_calls],
            [10, 1],
        )
        expected_codes = [
            code
            for package, _ in codex_calls
            for code in package["expectedLanguageCodes"]
        ]
        self.assertEqual(list(document), expected_codes)
        self.assertNotIn("en", document)
        self.assertNotIn("de", document)
        self.assertTrue(
            parse_llm_upload_json(
                json.dumps(document, ensure_ascii=False), expected_codes
            ).is_valid
        )
        self.assertEqual(service.publish_calls, [])


if __name__ == "__main__":
    unittest.main()
