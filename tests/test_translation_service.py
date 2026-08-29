import unittest

from services.localization_service import LocalizationService


VIDEO_RESOURCE = {
    "id": "video-1",
    "snippet": {
        "title": "Original title",
        "description": "Original description",
        "categoryId": "22",
        "defaultLanguage": "en",
    },
    "localizations": {
        "de": {"title": "Old DE", "description": "Old DE"},
        "fr": {"title": "Old FR", "description": "Old FR"},
    },
}


class FakeYoutubeApi:
    def __init__(self):
        self.events = []
        self.update_calls = []

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return VIDEO_RESOURCE

    def update_video_localizations(self, payload, if_match=None):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(payload)
        return {"id": payload["id"]}


class TranslationServiceTests(unittest.TestCase):
    def test_preview_accepts_internal_draft_and_never_writes(self):
        youtube = FakeYoutubeApi()
        service = LocalizationService(youtube, ("de", "es", "fr"))

        result = service.preview(
            "video-1",
            {"es": {"title": "New ES", "description": "New ES"}},
        )

        self.assertTrue(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(youtube.events, [("get", "video-1")])
        self.assertEqual(youtube.update_calls, [])

    def test_publish_merges_draft_with_omitted_existing_localizations(self):
        youtube = FakeYoutubeApi()
        service = LocalizationService(youtube, ("de", "es", "fr"))

        result = service.publish(
            "video-1",
            {"es": {"title": "New ES", "description": "New ES"}},
        )

        self.assertTrue(result.wrote)
        self.assertEqual(youtube.events, [("get", "video-1"), ("update", "video-1")])
        self.assertEqual(
            youtube.update_calls[0]["localizations"]["de"],
            {"title": "Old DE", "description": "Old DE"},
        )
        self.assertEqual(
            youtube.update_calls[0]["localizations"]["es"],
            {"title": "New ES", "description": "New ES"},
        )

    def test_publish_forwards_the_preview_resource_to_stale_write_guard(self):
        youtube = FakeYoutubeApi()
        service = LocalizationService(youtube, ("de", "es", "fr"))
        draft = {"es": {"title": "New ES", "description": "New ES"}}

        result = service.publish("video-1", draft, expected_video=VIDEO_RESOURCE)

        self.assertTrue(result.wrote)


if __name__ == "__main__":
    unittest.main()
