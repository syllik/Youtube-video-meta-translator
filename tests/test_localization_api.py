import importlib
import json
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from youtube_account import YoutubeVideoNotFoundError


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
        "de": {"title": "Alt DE", "description": "Alt DE"},
        "fr": {"title": "Old FR", "description": "Old FR"},
        "it": {"title": "Italian", "description": "Italian"},
    },
}


class FakeYoutubeApi:
    def __init__(self):
        self.code_to_name = {
            "de": "German",
            "es": "Spanish",
            "fr": "French",
        }
        self.name_to_code = {value: key for key, value in self.code_to_name.items()}
        self.video = VIDEO_RESOURCE
        self.events = []
        self.update_calls = []

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return self.video

    def update_video_localizations(self, payload):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(payload)
        return {"id": payload["id"]}


class FakeTranslateApi:
    def __init__(self):
        self.all_language_codes = []


class LocalizationEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.pop("app", None)
        with patch("youtube_account.YoutubeApi", return_value=FakeYoutubeApi()), patch(
            "google_translate.TranslateApi", return_value=FakeTranslateApi()
        ):
            cls.app_module = importlib.import_module("app")

    def setUp(self):
        self.api = FakeYoutubeApi()
        self.app_module.youtube_api = self.api
        self.client = self.app_module.app.test_client()

    def test_preview_serializes_all_diff_statuses_and_never_writes(self):
        response = self.client.post(
            "/api/localizations/preview",
            json={
                "video_id": "video-1",
                "localizations": {
                    "de": {"title": "Alt DE", "description": "Alt DE"},
                    "es": {"title": "Nuevo ES", "description": "Nuevo ES"},
                    "fr": {"title": "New FR", "description": "Old FR"},
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["valid"], True)
        self.assertEqual(body["summary"], {"added": 1, "changed": 1, "unchanged": 1})
        self.assertEqual(
            [(entry["language"], entry["status"]) for entry in body["languages"]],
            [("de", "unchanged"), ("es", "added"), ("fr", "changed")],
        )
        self.assertEqual(body["preserved_language_codes"], ["it"])
        self.assertEqual(self.api.events, [("get", "video-1")])
        self.assertEqual(self.api.update_calls, [])

    def test_publish_revalidates_and_returns_write_status(self):
        response = self.client.post(
            "/api/localizations/publish",
            json={
                "video_id": "video-1",
                "localizations": {
                    "es": {"title": "Nuevo ES", "description": "Nuevo ES"}
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["wrote"])
        self.assertEqual([event[0] for event in self.api.events], ["get", "update"])
        self.assertEqual(len(self.api.update_calls), 1)
        self.assertIn("fr", self.api.update_calls[0]["localizations"])

    def test_invalid_raw_json_returns_validation_error_without_fetch_or_write(self):
        response = self.client.post(
            "/api/localizations/publish",
            json={
                "video_id": "video-1",
                "localizations_json": '{"es":',
            },
        )

        self.assertEqual(response.status_code, 422)
        body = response.get_json()
        self.assertFalse(body["valid"])
        self.assertIsNone(body["errors"][0]["path"])
        self.assertEqual(self.api.events, [])
        self.assertEqual(self.api.update_calls, [])

    def test_invalid_request_envelope_returns_bad_request(self):
        response = self.client.post(
            "/api/localizations/preview",
            data=json.dumps({"localizations": {}}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("video_id", response.get_json()["error"])
        self.assertEqual(self.api.events, [])

    def test_language_names_are_recomputed_for_a_new_page(self):
        first_video = SimpleNamespace(current_languages=["de"], language_names=[])
        self.api.page_videos = [first_video]
        self.app_module.set_language_names()
        self.assertEqual(first_video.language_names, ["German"])

        second_video = SimpleNamespace(current_languages=["es"], language_names=[])
        self.api.page_videos = [second_video]
        self.app_module.set_language_names()

        self.assertEqual(second_video.language_names, ["Spanish"])

    def test_legacy_routes_remain_registered(self):
        routes = {
            rule.rule
            for rule in self.app_module.app.url_map.iter_rules()
        }

        self.assertIn("/", routes)
        self.assertIn("/languages", routes)
        self.assertIn("/error/", routes)

    def test_youtube_failure_is_returned_without_raw_exception_details(self):
        self.api.get_video_with_localizations = Mock(
            side_effect=RuntimeError("private test detail")
        )

        response = self.client.post(
            "/api/localizations/preview",
            json={
                "video_id": "video-1",
                "localizations": {
                    "es": {"title": "New", "description": "New"}
                },
            },
        )

        self.assertEqual(response.status_code, 502)
        body = response.get_json()
        self.assertEqual(body["error_type"], "youtube_api")
        self.assertNotIn("private test detail", body["error"])

    def test_missing_youtube_video_is_returned_as_not_found(self):
        self.api.get_video_with_localizations = Mock(
            side_effect=YoutubeVideoNotFoundError("missing video")
        )

        response = self.client.post(
            "/api/localizations/preview",
            json={
                "video_id": "missing-video",
                "localizations": {
                    "es": {"title": "New", "description": "New"}
                },
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error_type"], "video_not_found")


if __name__ == "__main__":
    unittest.main()
