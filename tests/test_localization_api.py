import unittest
from unittest.mock import Mock

from services.localization_service import LocalizationService
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


class FakeYoutubeService:
    def __init__(self):
        self.video = VIDEO_RESOURCE
        self.events = []
        self.update_calls = []

    def supported_language_codes(self):
        return ("de", "es", "fr")

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return self.video

    def update_video_localizations(self, payload, if_match=None):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(payload)
        return {"id": payload["id"]}


class LocalizationServiceApiTests(unittest.TestCase):
    def setUp(self):
        self.youtube = FakeYoutubeService()
        self.service = LocalizationService(self.youtube, ("de", "es", "fr"))

    def test_preview_serializes_all_diff_statuses_and_never_writes(self):
        result = self.service.preview(
            "video-1",
            {
                "de": {"title": "Alt DE", "description": "Alt DE"},
                "es": {"title": "Nuevo ES", "description": "Nuevo ES"},
                "fr": {"title": "New FR", "description": "Old FR"},
            },
        )

        self.assertTrue(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(
            [(entry.language_code, entry.status) for entry in result.plan.diffs],
            [("de", "unchanged"), ("es", "added"), ("fr", "changed")],
        )
        self.assertEqual(result.plan.preserved_language_codes, ("it",))
        self.assertEqual(self.youtube.events, [("get", "video-1")])
        self.assertEqual(self.youtube.update_calls, [])

    def test_publish_revalidates_and_returns_write_status(self):
        result = self.service.publish(
            "video-1",
            {"es": {"title": "Nuevo ES", "description": "Nuevo ES"}},
        )

        self.assertTrue(result.wrote)
        self.assertEqual([event[0] for event in self.youtube.events], ["get", "update"])
        self.assertEqual(len(self.youtube.update_calls), 1)
        self.assertIn("fr", self.youtube.update_calls[0]["localizations"])

    def test_invalid_draft_returns_validation_error_without_fetch_or_write(self):
        result = self.service.publish("video-1", {"es": {"title": 4}})

        self.assertFalse(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(result.plan.issues[0].path, "es.description")
        self.assertEqual(self.youtube.events, [])
        self.assertEqual(self.youtube.update_calls, [])

    def test_youtube_failure_is_not_replaced_with_raw_exception_details(self):
        self.youtube.get_video_with_localizations = Mock(
            side_effect=RuntimeError("private test detail")
        )

        with self.assertRaises(RuntimeError) as error:
            self.service.preview(
                "video-1",
                {"es": {"title": "New", "description": "New"}},
            )

        self.assertEqual(str(error.exception), "private test detail")

    def test_missing_youtube_video_is_kept_as_domain_error(self):
        self.youtube.get_video_with_localizations = Mock(
            side_effect=YoutubeVideoNotFoundError("missing video")
        )

        with self.assertRaises(YoutubeVideoNotFoundError):
            self.service.preview(
                "missing-video",
                {"es": {"title": "New", "description": "New"}},
            )


if __name__ == "__main__":
    unittest.main()
