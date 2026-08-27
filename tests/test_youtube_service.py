import unittest
from unittest.mock import Mock

from models import YouTubePage
from services.youtube_service import YoutubeService


class YoutubeServiceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
