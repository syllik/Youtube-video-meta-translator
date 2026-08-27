import io
import os
import pickle
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, call, mock_open, patch

from google_translate import TranslateApi, TranslationError
from youtube_account import YoutubeApi
import youtube_account


class TranslationProviderTests(unittest.TestCase):
    def test_google_translate_failure_is_not_returned_as_source_text(self):
        api = object.__new__(TranslateApi)

        class BrokenClient:
            def translate(self, *args, **kwargs):
                raise RuntimeError("provider down")

        api.translate_client = BrokenClient()

        with self.assertRaises(TranslationError):
            api.translate_text("es", "Original title")


class YoutubeAccountSecurityTests(unittest.TestCase):
    def test_token_cache_permissions_are_restricted_when_loaded(self):
        account = object.__new__(YoutubeApi)
        account.credentials = None

        with patch(
            "youtube_account.os.path.exists",
            side_effect=lambda path: path == "token.pickle",
        ), patch("builtins.open", mock_open()), patch(
            "youtube_account._load_legacy_credentials",
            return_value=SimpleNamespace(valid=True, to_json=lambda: "{}"),
        ), patch("youtube_account.os.chmod") as chmod:
            account.check_credentials()

        self.assertEqual(
            chmod.call_args_list,
            [call("token.pickle", 0o600), call("token.json", 0o600)],
        )

    def test_legacy_credential_loader_rejects_executable_pickle_globals(self):
        class MaliciousPayload:
            def __reduce__(self):
                return (eval, ("1 + 1",))

        with self.assertRaises(pickle.UnpicklingError):
            youtube_account._load_legacy_credentials(
                io.BytesIO(pickle.dumps(MaliciousPayload()))
            )

    def test_localization_read_failure_is_recorded_for_the_video(self):
        from googleapiclient.errors import HttpError
        from httplib2 import Response

        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.errorStr = ""
        account.youtube.videos.return_value.list.return_value.execute.side_effect = (
            HttpError(
                Response({"status": "403"}),
                b'{"error":{"code":403,"message":"forbidden","errors":[{"reason":"forbidden"}]}}',
            )
        )

        self.assertEqual(account.get_video_localizations("video-1"), [])
        self.assertEqual(account.errorStr, "forbidden")
        self.assertEqual(account.localization_read_errors, {"video-1"})

    def test_regional_localization_codes_are_not_collapsed_to_generic_codes(self):
        account = object.__new__(YoutubeApi)
        account.youtube = Mock()
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{
                "localizations": {
                    "en-GB": {"title": "British", "description": "British"},
                    "pt-BR": {"title": "Brazilian", "description": "Brazilian"},
                }
            }]
        }

        self.assertEqual(
            set(account.get_video_localizations("video-1")), {"en-GB", "pt-BR"}
        )

    def test_insecure_oauth_transport_setting_does_not_leak_after_startup(self):
        flow = Mock()
        flow.credentials = SimpleNamespace(valid=True, to_json=lambda: "{}")

        with patch.dict(os.environ, {}, clear=True), patch(
            "youtube_account.os.path.exists", return_value=False
        ), patch(
            "youtube_account.InstalledAppFlow.from_client_secrets_file",
            return_value=flow,
        ), patch("builtins.open", mock_open()), patch(
            "googleapiclient.discovery.build", return_value=Mock()
        ), patch.object(YoutubeApi, "set_uploads_id"), patch.object(
            YoutubeApi, "get_total_video_count"
        ), patch("youtube_account.os.chmod"):
            YoutubeApi()

        self.assertNotIn("OAUTHLIB_INSECURE_TRANSPORT", os.environ)

    def test_json_token_cache_is_preferred_to_legacy_pickle(self):
        account = object.__new__(YoutubeApi)
        account.credentials = None
        credentials = SimpleNamespace(valid=True)

        with patch(
            "youtube_account.os.path.exists",
            side_effect=lambda path: path == "token.json",
        ), patch("youtube_account.Credentials", create=True) as credentials_class, patch(
            "youtube_account.pickle.load"
        ) as legacy_load, patch(
            "youtube_account.InstalledAppFlow.from_client_secrets_file"
        ) as oauth_flow, patch("youtube_account.pickle.dump"), patch(
            "youtube_account.os.chmod"
        ) as chmod:
            credentials_class.from_authorized_user_file.return_value = credentials
            account.check_credentials()

        legacy_load.assert_not_called()
        oauth_flow.assert_not_called()
        chmod.assert_called_once_with("token.json", 0o600)

    def test_missing_default_language_does_not_get_replaced_with_english(self):
        account = object.__new__(YoutubeApi)
        account.videos_trimmed = 0
        account.videos_skipped = 0
        account.errorStr = ""
        account.youtube = Mock()
        account.youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": "video-1",
                "snippet": {
                    "title": "Original",
                    "description": "Description",
                    "categoryId": "22",
                },
                "localizations": {},
            }]
        }

        account.set_video_localization(
            "video-1", "es", "Spanish", "Título", "Descripción", False, "Original"
        )

        self.assertEqual(account.errorStr, "defaultLanguageNotSet")
        account.youtube.videos.return_value.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
