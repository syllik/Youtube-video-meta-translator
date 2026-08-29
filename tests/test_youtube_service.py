import unittest
from unittest.mock import Mock, call

from language_catalog import YouTubeLanguageCatalog
from models import ChannelInfo, YouTubePage
from services.youtube_service import YoutubeService, YoutubeResetError


class YoutubeServiceTests(unittest.TestCase):
    def test_fetch_channel_exposes_id_and_description(self):
        account = Mock()
        account.channel_id = "channel-1"
        account.channel_name = "My channel"
        account.channel_description = "Channel description"
        account.channel_thumbnail = "channel-thumb"
        account.total_video_count = 42
        service = YoutubeService(account)

        result = service.fetch_channel()

        self.assertEqual(
            result,
            ChannelInfo(
                id="channel-1",
                name="My channel",
                description="Channel description",
                thumbnail_url="channel-thumb",
                total_videos=42,
            ),
        )

    def test_fetch_video_page_passes_limit_and_page_token(self):
        account = Mock()
        account.fetch_video_page.return_value = {
            "videos": [],
            "next_page_token": "next-2",
        }
        service = YoutubeService(account)

        result = service.fetch_video_page(20, "next-1")

        account.fetch_video_page.assert_called_once_with(20, "next-1")
        self.assertIsInstance(result, YouTubePage)
        self.assertEqual(result.next_page_token, "next-2")

    def test_existing_video_model_is_converted_by_id(self):
        account = Mock()
        account.fetch_video_page.return_value = {
            "videos": [{
                "id": "video-1",
                "title": "Same title",
                "description": "Description",
                "thumbnail_url": "thumb",
                "current_language_codes": ["de"],
            }],
            "next_page_token": None,
        }
        service = YoutubeService(account)

        result = service.fetch_video_page(10)

        self.assertEqual(result.videos[0].id, "video-1")
        self.assertEqual(result.videos[0].current_language_codes, ("de",))

    def test_video_summary_preserves_default_language(self):
        account = Mock()
        account.fetch_video_page.return_value = {
            "videos": [{
                "id": "video-1",
                "title": "Same title",
                "description": "Description",
                "thumbnail_url": "thumb",
                "current_language_codes": ["de"],
                "default_language_code": "en",
            }],
            "next_page_token": None,
        }
        service = YoutubeService(account)

        result = service.fetch_video_page(10)

        self.assertEqual(result.videos[0].default_language_code, "en")

    def test_reset_fetches_updates_and_verifies_the_fresh_resource(self):
        account = Mock()
        source = {
            "id": "video-1",
            "snippet": {
                "title": "Title",
                "description": "Description",
                "categoryId": "22",
                "defaultLanguage": "en",
                "tags": ["keep"],
            },
            "localizations": {"de": {"title": "DE", "description": "DE"}},
        }
        verified = {
            "id": "video-1",
            "snippet": {
                "title": "Title",
                "description": "Description",
                "categoryId": "22",
                "defaultLanguage": "en",
                "tags": ["keep"],
            },
            "localizations": {
                "en": {"title": "Title", "description": "Description"}
            },
        }
        account.get_video_with_localizations.side_effect = [source, verified]
        account.update_video_localizations.return_value = {"id": "video-1"}
        service = YoutubeService(account)

        result = service.reset_video_localizations("video-1")

        self.assertEqual(result, {"id": "video-1"})
        self.assertEqual(
            account.get_video_with_localizations.call_args_list,
            [call("video-1"), call("video-1")],
        )
        account.update_video_localizations.assert_called_once()
        payload = account.update_video_localizations.call_args.args[0]
        self.assertEqual(payload["id"], "video-1")
        self.assertEqual(
            payload["localizations"],
            {"en": {"title": "Title", "description": "Description"}},
        )
        self.assertEqual(payload["snippet"]["defaultLanguage"], "en")

    def test_reset_fails_when_non_default_localization_survives_verification(self):
        account = Mock()
        source = {
            "id": "video-1",
            "snippet": {
                "title": "Title",
                "description": "Description",
                "categoryId": "22",
                "defaultLanguage": "en",
            },
            "localizations": {"de": {"title": "DE", "description": "DE"}},
        }
        verified = {
            **source,
            "localizations": {
                "en": {"title": "Title", "description": "Description"},
                "de": {"title": "DE", "description": "DE"},
            },
        }
        account.get_video_with_localizations.side_effect = [source, verified]
        account.update_video_localizations.return_value = {"id": "video-1"}
        service = YoutubeService(account)

        with self.assertRaisesRegex(YoutubeResetError, "verification"):
            service.reset_video_localizations("video-1")

        account.update_video_localizations.assert_called_once()
        self.assertEqual(account.get_video_with_localizations.call_count, 2)

    def test_reset_fails_when_default_metadata_changes_during_verification(self):
        account = Mock()
        source = {
            "id": "video-1",
            "snippet": {
                "title": "Title",
                "description": "Description",
                "categoryId": "22",
                "defaultLanguage": "en",
            },
            "localizations": {"de": {"title": "DE", "description": "DE"}},
        }
        verified = {
            **source,
            "snippet": {**source["snippet"], "title": "Changed"},
            "localizations": {
                "en": {"title": "Changed", "description": "Description"}
            },
        }
        account.get_video_with_localizations.side_effect = [source, verified]
        account.update_video_localizations.return_value = {"id": "video-1"}
        service = YoutubeService(account)

        with self.assertRaisesRegex(YoutubeResetError, "default snippet.title"):
            service.reset_video_localizations("video-1")

    def test_reset_does_not_write_without_a_safe_default_language(self):
        account = Mock()
        account.get_video_with_localizations.return_value = {
            "id": "video-1",
            "snippet": {
                "title": "Title",
                "description": "Description",
                "categoryId": "22",
            },
            "localizations": {"de": {"title": "DE", "description": "DE"}},
        }
        service = YoutubeService(account)

        with self.assertRaisesRegex(YoutubeResetError, "defaultLanguage"):
            service.reset_video_localizations("video-1")

        account.update_video_localizations.assert_not_called()

    def test_language_catalog_comes_from_youtube_and_is_cached(self):
        account = Mock()
        account.list_i18n_languages.return_value = {
            "items": [
                {"id": "es", "snippet": {"hl": "es", "name": "Spanish"}},
                {"id": "de", "snippet": {"hl": "de", "name": "German"}},
            ]
        }
        service = YoutubeService(account)

        first = service.fetch_application_language_catalog()
        second = service.fetch_application_language_catalog()

        self.assertIsInstance(first, YouTubeLanguageCatalog)
        self.assertIs(first, second)
        self.assertEqual(first.codes, ("de", "es"))
        account.list_i18n_languages.assert_called_once_with("ru")

    def test_language_catalog_can_be_refreshed(self):
        account = Mock()
        account.list_i18n_languages.side_effect = [
            {"items": [{"id": "de", "snippet": {"hl": "de", "name": "German"}}]},
            {"items": [{"id": "fr", "snippet": {"hl": "fr", "name": "French"}}]},
        ]
        service = YoutubeService(account)

        service.fetch_application_language_catalog()
        refreshed = service.fetch_application_language_catalog(refresh=True)

        self.assertEqual(refreshed.codes, ("fr",))
        self.assertEqual(account.list_i18n_languages.call_count, 2)

    def test_metadata_language_catalog_is_static_and_cached(self):
        account = Mock()
        service = YoutubeService(account)

        first = service.fetch_metadata_language_catalog()
        second = service.fetch_metadata_language_catalog()

        self.assertIs(first, second)
        self.assertIn("be", first.codes)
        account.list_i18n_languages.assert_not_called()


if __name__ == "__main__":
    unittest.main()
