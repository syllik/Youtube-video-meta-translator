import importlib
import json
import tempfile
import unittest
from pathlib import Path

from codex_localization_runner import CodexLocalizationError
from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog


try:
    cli_module = importlib.import_module("generate_codex_localizations")
except ModuleNotFoundError:
    cli_module = None


class FakeYoutubeService:
    def __init__(self):
        self.video_ids = []
        self.catalog_requests = []
        self.publish_calls = []
        self.video_resource = {
            "snippet": {
                "defaultLanguage": "en",
                "title": "Waterfall",
                "description": "Wind above the falls.",
            },
            "localizations": {
                "de": {"title": "Wasserfall", "description": "Wind"},
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
            ),
        )

    def get_video_with_localizations(self, video_id):
        self.video_ids.append(video_id)
        return self.video_resource

    def fetch_metadata_language_catalog(self, refresh=False):
        self.catalog_requests.append(refresh)
        return self.catalog

    def update_video_localizations(self, payload, if_match=None):
        self.publish_calls.append(payload)
        raise AssertionError("CLI must never publish localizations")


class GenerateCodexLocalizationsTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(cli_module, "CLI module is not implemented")

    @staticmethod
    def _success_batch(package, schema):
        return {
            code: {"title": "Title " + code, "description": "Text " + code}
            for code in package["expectedLanguageCodes"]
        }

    def test_main_fetches_requested_video_and_static_metadata_catalog(self):
        service = FakeYoutubeService()
        login_calls = []

        def login_checker():
            login_calls.append(True)

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "localizations.json"
            result = cli_module.main(
                ["--video-id", "video-123", "--output", str(output_path)],
                service_factory=lambda: service,
                login_checker=login_checker,
                run_batch=self._success_batch,
            )

            self.assertEqual(result, 0)
            document = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(login_calls, [True])
        self.assertEqual(service.video_ids, ["video-123"])
        self.assertEqual(service.catalog_requests, [True])
        self.assertEqual(tuple(document), ("fr", "es"))
        self.assertNotIn("en", document)
        self.assertNotIn("de", document)
        self.assertEqual(service.publish_calls, [])

    def test_max_languages_produces_only_one_missing_target(self):
        service = FakeYoutubeService()

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "localizations.json"
            result = cli_module.main(
                [
                    "--video-id",
                    "video-123",
                    "--max-languages",
                    "1",
                    "--output",
                    str(output_path),
                ],
                service_factory=lambda: service,
                login_checker=lambda: None,
                run_batch=self._success_batch,
            )

            self.assertEqual(result, 0)
            self.assertEqual(
                tuple(json.loads(output_path.read_text(encoding="utf-8"))),
                ("fr",),
            )

    def test_failed_generation_preserves_existing_output(self):
        service = FakeYoutubeService()

        def failing_batch(package, schema):
            raise CodexLocalizationError("Codex unavailable")

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "localizations.json"
            output_path.write_text('{"keep": true}\n', encoding="utf-8")

            result = cli_module.main(
                ["--video-id", "video-123", "--output", str(output_path)],
                service_factory=lambda: service,
                login_checker=lambda: None,
                run_batch=failing_batch,
            )

            self.assertEqual(result, 1)
            self.assertEqual(
                output_path.read_text(encoding="utf-8"), '{"keep": true}\n'
            )
        self.assertEqual(service.publish_calls, [])

    def test_package_json_exposes_codex_command(self):
        package = json.loads(Path("package.json").read_text(encoding="utf-8"))

        self.assertEqual(
            package["scripts"]["youtube:codex-localize"],
            "python3 generate_codex_localizations.py",
        )


if __name__ == "__main__":
    unittest.main()
