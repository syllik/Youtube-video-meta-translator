import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from youtube_languages.fetch_youtube_languages import (
    YouTubeLanguagesError,
    build_output,
    fetch_languages,
    main,
)


class YouTubeLanguagesTests(unittest.TestCase):
    def test_build_output_maps_api_items_to_application_language_entries(self):
        response = {
            "items": [
                {
                    "id": "en",
                    "snippet": {"hl": "en", "name": "Английский"},
                },
            ],
        }

        result = build_output(response, "2026-08-27T10:00:00.000Z")

        self.assertEqual(
            result,
            {
                "source": "YouTube Data API v3 i18nLanguages.list",
                "fetchedAt": "2026-08-27T10:00:00.000Z",
                "hl": "ru",
                "count": 1,
                "languages": [
                    {"code": "en", "name": "Английский", "id": "en"},
                ],
            },
        )

    def test_build_output_sorts_languages_by_russian_collation(self):
        response = {
            "items": [
                {"id": "ja", "snippet": {"hl": "ja", "name": "Японский"}},
                {"id": "ru", "snippet": {"hl": "ru", "name": "Русский"}},
                {"id": "en", "snippet": {"hl": "en", "name": "Английский"}},
            ],
        }

        result = build_output(response, "2026-08-27T10:00:00.000Z")

        self.assertEqual(
            [language["name"] for language in result["languages"]],
            ["Английский", "Русский", "Японский"],
        )

    def test_main_reports_missing_api_key_without_writing_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "youtube-languages.json"

            with patch.dict("os.environ", {}, clear=True):
                exit_code = main(
                    environ={},
                    output_path=output_path,
                    load_environment=False,
                )

            self.assertEqual(exit_code, 1)
            self.assertFalse(output_path.exists())

    def test_build_output_rejects_response_without_items(self):
        with self.assertRaisesRegex(ValueError, "items"):
            build_output({}, "2026-08-27T10:00:00.000Z")

    def test_google_error_contains_status_and_safe_message_without_api_key(self):
        class ErrorResponse:
            status_code = 403
            text = ""

            def json(self):
                return {"error": {"message": "The API key is not valid."}}

        with self.assertRaises(YouTubeLanguagesError) as context:
            fetch_languages(
                "secret-api-key",
                http_get=lambda *args, **kwargs: ErrorResponse(),
            )

        message = str(context.exception)
        self.assertIn("403", message)
        self.assertIn("The API key is not valid.", message)
        self.assertNotIn("secret-api-key", message)


if __name__ == "__main__":
    unittest.main()
