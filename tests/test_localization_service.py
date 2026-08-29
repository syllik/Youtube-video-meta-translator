import json
import unittest
from unittest.mock import Mock

from localization_service import preview_localizations, publish_localizations
from services.manual_localization_service import ManualLocalizationService


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


class FakeYoutubeApi:
    def __init__(self, video):
        self.video = video
        self.events = []
        self.update_calls = []

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return self.video

    def update_video_localizations(self, payload):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(payload)
        return {"id": payload["id"]}


class LocalizationServiceTests(unittest.TestCase):
    def test_manual_service_reset_delegates_to_dedicated_reset_operation(self):
        youtube = Mock()
        youtube.reset_video_localizations.return_value = {"id": "video-1"}
        service = ManualLocalizationService(youtube, {"de"})

        result = service.reset("video-1")

        self.assertEqual(result, {"id": "video-1"})
        youtube.reset_video_localizations.assert_called_once_with("video-1")

    def test_invalid_json_does_not_fetch_or_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)

        result = publish_localizations(
            api, "video-1", '{"es": {"title": 4}}', {"es"}
        )

        self.assertFalse(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [])
        self.assertEqual(api.update_calls, [])

    def test_valid_publish_fetches_current_data_before_one_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        raw = json.dumps({"es": {"title": "Nuevo", "description": "Nuevo"}})

        result = publish_localizations(api, "video-1", raw, {"es"})

        self.assertTrue(result.wrote)
        self.assertEqual([event[0] for event in api.events], ["get", "update"])
        self.assertEqual(len(api.update_calls), 1)
        self.assertIn("de", api.update_calls[0]["localizations"])

    def test_unchanged_publish_does_not_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        raw = json.dumps({"fr": {"title": "Même", "description": "Même"}})

        result = publish_localizations(api, "video-1", raw, {"fr"})

        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [("get", "video-1")])

    def test_preview_fetches_but_never_writes(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        raw = json.dumps({"es": {"title": "Nuevo", "description": "Nuevo"}})

        result = preview_localizations(api, "video-1", raw, {"es"})

        self.assertTrue(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [("get", "video-1")])
        self.assertEqual(api.update_calls, [])


if __name__ == "__main__":
    unittest.main()
