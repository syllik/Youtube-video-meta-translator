import unittest
from unittest.mock import Mock

from youtube_account import YoutubeApi


class VideoPaginationTests(unittest.TestCase):
    def test_changing_page_clears_previous_page_before_loading(self):
        account = object.__new__(YoutubeApi)
        account.results_per_page = 10
        account.current_page = 1
        account.page_videos = [object()]
        account.load_page_videos = Mock()

        account.set_video_page(2)

        self.assertEqual(account.current_page, 2)
        self.assertEqual(account.page_videos, [])
        account.load_page_videos.assert_called_once_with(2)


if __name__ == "__main__":
    unittest.main()
