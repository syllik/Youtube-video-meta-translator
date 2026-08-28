import unittest
from unittest.mock import Mock

from youtube_account import YoutubeApi, YoutubeVideoNotFoundError


class YoutubeLocalizationApiTests(unittest.TestCase):
    def test_video_page_batches_metadata_and_preserves_playlist_order(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.uploads_id = "uploads-1"
        account.youtube.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "snippet": {
                        "title": "First",
                        "description": "First description",
                        "resourceId": {"videoId": "video-1"},
                        "thumbnails": {"default": {"url": "thumb-1"}},
                    }
                },
                {
                    "snippet": {
                        "title": "Second",
                        "description": "Second description",
                        "resourceId": {"videoId": "video-2"},
                        "thumbnails": {"default": {"url": "thumb-2"}},
                    }
                },
            ]
        }
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "video-2",
                    "snippet": {"defaultLanguage": "fr"},
                    "localizations": {"de": {}},
                },
                {
                    "id": "video-1",
                    "snippet": {"defaultLanguage": "en"},
                    "localizations": {"es": {}},
                },
            ]
        }

        page = account.fetch_video_page(10)

        self.assertEqual([video.id for video in page["videos"]], ["video-1", "video-2"])
        self.assertEqual(page["videos"][0].default_language_code, "en")
        self.assertEqual(page["videos"][0].current_languages, ["es"])
        self.assertEqual(page["videos"][1].default_language_code, "fr")
        self.assertEqual(page["videos"][1].current_languages, ["de"])
        account.youtube.videos.return_value.list.assert_called_once_with(
            part="snippet,localizations", id="video-1,video-2"
        )

    def test_channel_setup_reads_details_and_uploads_playlist_in_one_request(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.errorStr = ""
        account.youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": "channel-1",
                "snippet": {
                    "title": "Channel",
                    "description": "Description",
                    "thumbnails": {"default": {"url": "thumb"}},
                },
                "contentDetails": {
                    "relatedPlaylists": {"uploads": "uploads-1"}
                },
            }]
        }

        account.set_uploads_id()

        self.assertEqual(account.channel_id, "channel-1")
        self.assertEqual(account.channel_description, "Description")
        self.assertEqual(account.uploads_id, "uploads-1")
        account.youtube.channels.return_value.list.assert_called_once_with(
            part="snippet,contentDetails", mine=True
        )

    def test_video_page_reads_default_language_from_video_resource(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.uploads_id = "uploads-1"
        account.youtube.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Title",
                    "description": "Description",
                    "resourceId": {"videoId": "video-1"},
                    "thumbnails": {"default": {"url": "thumb"}},
                }
            }]
        }
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": "video-1",
                "snippet": {"defaultLanguage": "en"},
                "localizations": {"de": {"title": "DE", "description": "DE"}},
            }]
        }

        page = account.fetch_video_page(10)

        self.assertEqual(page["videos"][0].default_language_code, "en")
        account.youtube.videos.return_value.list.assert_called_once_with(
            part="snippet,localizations", id="video-1"
        )

    def test_video_page_keeps_playlist_card_when_metadata_is_missing(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.uploads_id = "uploads-1"
        account.youtube.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [{
                "snippet": {
                    "title": "Title",
                    "description": "Description",
                    "resourceId": {"videoId": "video-1"},
                    "thumbnails": {"default": {"url": "thumb"}},
                }
            }]
        }
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        page = account.fetch_video_page(10)

        self.assertEqual(len(page["videos"]), 1)
        self.assertEqual(page["videos"][0].current_languages, [])
        self.assertIsNone(page["videos"][0].default_language_code)

    def test_get_video_with_localizations_requests_both_required_parts(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "video-1", "snippet": {}, "localizations": {}}]
        }

        result = account.get_video_with_localizations("video-1")

        self.assertEqual(result["id"], "video-1")
        account.youtube.videos.return_value.list.assert_called_once_with(
            part="snippet,localizations", id="video-1"
        )

    def test_get_video_with_localizations_rejects_empty_response(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": []
        }

        with self.assertRaises(YoutubeVideoNotFoundError):
            account.get_video_with_localizations("video-1")

    def test_update_video_localizations_makes_one_write_with_supplied_payload(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.youtube.videos.return_value.update.return_value.execute.return_value = {
            "ok": True
        }
        payload = {
            "id": "video-1",
            "localizations": {"es": {"title": "x", "description": "y"}},
        }

        result = account.update_video_localizations(payload)

        self.assertEqual(result, {"ok": True})
        account.youtube.videos.return_value.update.assert_called_once_with(
            part="snippet,localizations", body=payload
        )


if __name__ == "__main__":
    unittest.main()
