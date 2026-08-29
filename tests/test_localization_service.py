import copy
import unittest
from unittest.mock import Mock

from localization_service import preview_localizations, publish_localizations


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
        self.video = copy.deepcopy(video)
        self.events = []
        self.update_calls = []
        self.update_if_matches = []
        self.update_error = None

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return copy.deepcopy(self.video)

    def update_video_localizations(self, payload, if_match=None):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(copy.deepcopy(payload))
        self.update_if_matches.append(if_match)
        if self.update_error is not None:
            raise self.update_error
        return {"id": payload["id"]}


class _Response:
    def __init__(self, status):
        self.status = status


class _PreconditionFailedError(Exception):
    def __init__(self):
        super().__init__("precondition failed")
        self.resp = _Response(412)


class LocalizationServiceTests(unittest.TestCase):
    def test_invalid_json_does_not_fetch_or_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)

        result = publish_localizations(
            api, "video-1", {"es": {"title": 4}}, {"es"}
        )

        self.assertFalse(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [])
        self.assertEqual(api.update_calls, [])

    def test_valid_publish_fetches_current_data_before_one_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        draft = {"es": {"title": "Nuevo", "description": "Nuevo"}}

        result = publish_localizations(api, "video-1", draft, {"es"})

        self.assertTrue(result.wrote)
        self.assertEqual([event[0] for event in api.events], ["get", "update"])
        self.assertEqual(len(api.update_calls), 1)
        self.assertIn("de", api.update_calls[0]["localizations"])

    def test_unchanged_publish_does_not_write(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        draft = {"fr": {"title": "Même", "description": "Même"}}

        result = publish_localizations(api, "video-1", draft, {"fr"})

        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [("get", "video-1")])

    def test_preview_fetches_but_never_writes(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        draft = {"es": {"title": "Nuevo", "description": "Nuevo"}}

        result = preview_localizations(api, "video-1", draft, {"es"})

        self.assertTrue(result.plan.is_valid)
        self.assertFalse(result.wrote)
        self.assertEqual(api.events, [("get", "video-1")])
        self.assertEqual(api.update_calls, [])

    def test_stale_preview_conflict_does_not_overwrite_new_youtube_state(self):
        api = FakeYoutubeApi(VIDEO_RESOURCE)
        draft = {"de": {"title": "New", "description": "New"}}
        preview = preview_localizations(api, "video-1", draft, {"de"})
        api.video["localizations"]["de"] = {
            "title": "Collaborator",
            "description": "Collaborator",
        }

        result = publish_localizations(
            api,
            "video-1",
            draft,
            {"de"},
            expected_video=preview.video,
        )

        self.assertFalse(result.wrote)
        self.assertFalse(result.plan.is_valid)
        self.assertIsNone(result.plan.payload)
        self.assertEqual(api.update_calls, [])
        self.assertIn("changed after Preview", result.plan.issues[0].message)

    def test_matching_preview_writes_once_with_fresh_etag(self):
        api = FakeYoutubeApi({**VIDEO_RESOURCE, "etag": "etag-1"})
        draft = {"de": {"title": "New", "description": "New"}}
        preview = preview_localizations(api, "video-1", draft, {"de"})

        result = publish_localizations(
            api,
            "video-1",
            draft,
            {"de"},
            expected_video=preview.video,
        )

        self.assertTrue(result.wrote)
        self.assertEqual(api.update_if_matches, ["etag-1"])
        self.assertEqual(len(api.update_calls), 1)

    def test_api_precondition_conflict_does_not_report_a_successful_write(self):
        api = FakeYoutubeApi({**VIDEO_RESOURCE, "etag": "etag-1"})
        api.update_error = _PreconditionFailedError()
        draft = {"de": {"title": "New", "description": "New"}}
        preview = preview_localizations(api, "video-1", draft, {"de"})

        result = publish_localizations(
            api,
            "video-1",
            draft,
            {"de"},
            expected_video=preview.video,
        )

        self.assertFalse(result.wrote)
        self.assertFalse(result.plan.is_valid)
        self.assertIn("changed before YouTube accepted", result.plan.issues[0].message)


if __name__ == "__main__":
    unittest.main()
