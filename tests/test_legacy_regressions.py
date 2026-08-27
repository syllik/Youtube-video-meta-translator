import importlib
import io
import os
import pickle
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, call, mock_open, patch

from flask import Flask, render_template

from google_translate import TranslateApi, TranslationError
import youtube_account
from youtube_account import YoutubeApi


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TemplateRegressionTests(unittest.TestCase):
    def test_all_channel_video_branch_renders_without_jinja_error(self):
        flask_app = Flask(
            "template-regression",
            template_folder=str(PROJECT_ROOT / "templates"),
        )

        with flask_app.test_request_context("/"):
            rendered = render_template(
                "home.html",
                page_videos=[],
                all_videos=[SimpleNamespace(id="video-1", video_title="A video")],
                all_language_names=[],
                channel_thumbnail="",
                channel_name="",
                num_pages=2,
                current_page=1,
                error_str="",
                per_page_index=0,
                trimmed=0,
                skipped=0,
                total_videos=1,
            )

        self.assertIn('vids.push("video-1")', rendered)
        self.assertNotIn("axios(", rendered)

    def test_rendered_inline_javascript_is_syntax_valid(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js is not installed")

        flask_app = Flask(
            "template-javascript-regression",
            template_folder=str(PROJECT_ROOT / "templates"),
        )
        with flask_app.test_request_context("/"):
            rendered = render_template(
                "home.html",
                page_videos=[
                    SimpleNamespace(
                        id="video-1",
                        video_title="A video",
                        thumbnail_url="",
                        description="",
                        num_languages=0,
                        language_names=[],
                    )
                ],
                all_videos=[],
                all_language_names=[],
                channel_thumbnail="",
                channel_name="",
                num_pages=1,
                current_page=1,
                error_str="",
                per_page_index=0,
                trimmed=0,
                skipped=0,
                total_videos=1,
            )

        scripts = re.findall(
            r'<script type="text/javascript">([\s\S]*?)</script>',
            rendered,
        )
        self.assertEqual(len(scripts), 1)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", encoding="utf-8"
        ) as script_file:
            script_file.write(scripts[0])
            script_file.flush()
            result = subprocess.run(
                [node, "--check", script_file.name],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manual_editor_appears_only_after_radio_and_validates_on_each_change(self):
        flask_app = Flask(
            "manual-editor-ui-regression",
            template_folder=str(PROJECT_ROOT / "templates"),
        )
        with flask_app.test_request_context("/"):
            rendered = render_template(
                "home.html",
                page_videos=[
                    SimpleNamespace(
                        id="video-1",
                        video_title="A video",
                        thumbnail_url="",
                        description="",
                        num_languages=0,
                        language_names=[],
                    )
                ],
                all_videos=[],
                all_language_names=[],
                channel_thumbnail="",
                channel_name="",
                num_pages=1,
                current_page=1,
                error_str="",
                per_page_index=0,
                trimmed=0,
                skipped=0,
                total_videos=1,
            )

        self.assertRegex(
            rendered,
            r'<section[^>]+id="manual-localization-editor"[^>]+hidden',
        )
        self.assertNotIn("preview-localizations-btn", rendered)
        self.assertIn("class=\"form-check-input manual-video-selector\"", rendered)
        self.assertIn('name=\"manual-video\" value=\"video-1\"', rendered)
        self.assertIn(
            "localizationsJson.addEventListener('input', scheduleManualValidation);",
            rendered,
        )
        self.assertIn(
            "selector.addEventListener('change', handleManualVideoChange);",
            rendered,
        )


class TranslationFailureTests(unittest.TestCase):
    def test_google_translate_failure_is_not_returned_as_source_text(self):
        api = object.__new__(TranslateApi)

        class BrokenClient:
            def translate(self, *args, **kwargs):
                raise RuntimeError("provider down")

        api.translate_client = BrokenClient()

        with self.assertRaises(TranslationError):
            api.translate_text("es", "Original title")


class LegacyRouteRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.modules.pop("app", None)
        with patch("youtube_account.YoutubeApi", return_value=SimpleNamespace()), patch(
            "google_translate.TranslateApi", return_value=SimpleNamespace()
        ):
            cls.app_module = importlib.import_module("app")

    def setUp(self):
        self.video_one = SimpleNamespace(
            id="video-1",
            video_title="Same title",
            description="Description one",
            language_names=[],
        )
        self.video_two = SimpleNamespace(
            id="video-2",
            video_title="Same title",
            description="Description two",
            language_names=[],
        )
        self.api = SimpleNamespace(
            page_videos=[self.video_one, self.video_two],
            all_videos_cache=[],
            results_per_page=10,
            name_to_code={"Spanish": "es"},
            errorStr="",
            videos_trimmed=0,
            videos_skipped=0,
            localization_calls=[],
        )

        def set_video_localization(video_id, *args):
            self.api.localization_calls.append(video_id)

        self.api.set_video_localization = set_video_localization
        self.api.clear_video_cache = Mock()
        self.app_module.youtube_api = self.api
        self.app_module.deepl_translator = None
        self.client = self.app_module.app.test_client()

    def test_legacy_translation_targets_video_by_id_when_titles_collide(self):
        self.app_module.translate_api = SimpleNamespace(
            all_language_codes=["es"],
            translate_text=lambda language, text: "Translated " + text,
        )

        with patch.object(self.app_module.time, "sleep"):
            response = self.client.post(
                "/",
                json={
                    "selected_videos": ["video-2"],
                    "selected_languages": ["Spanish"],
                    "overwrite": False,
                    "use_deepL": False,
                    "trim_checked": False,
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.api.localization_calls, ["video-2"])

    def test_legacy_translation_keeps_unique_title_compatibility(self):
        self.video_one.video_title = "Unique title"
        self.app_module.translate_api = SimpleNamespace(
            all_language_codes=["es"],
            translate_text=lambda language, text: "Translated " + text,
        )

        with patch.object(self.app_module.time, "sleep"):
            response = self.client.post(
                "/",
                json={
                    "selected_videos": ["Unique title"],
                    "selected_languages": ["Spanish"],
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.api.localization_calls, ["video-1"])

    def test_legacy_translation_rejects_ambiguous_title_without_update(self):
        self.app_module.translate_api = SimpleNamespace(
            all_language_codes=["es"],
            translate_text=lambda language, text: "Translated " + text,
        )

        with patch.object(self.app_module.time, "sleep"):
            response = self.client.post(
                "/",
                json={
                    "selected_videos": ["Same title"],
                    "selected_languages": ["Spanish"],
                },
            )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error_type"], "videoAmbiguous")
        self.assertEqual(self.api.localization_calls, [])

    def test_translation_failure_is_returned_as_error_without_update(self):
        def fail_translation(language, text):
            raise TranslationError("provider down")

        self.app_module.translate_api = SimpleNamespace(
            all_language_codes=["es"],
            translate_text=fail_translation,
        )

        response = self.client.post(
            "/",
            json={
                "selected_videos": ["video-1"],
                "selected_languages": ["Spanish"],
                "overwrite": False,
                "use_deepL": False,
                "trim_checked": False,
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.get_json()["status"], "error")
        self.assertEqual(self.api.localization_calls, [])

    def test_flask_debug_mode_is_off_by_default(self):
        self.assertFalse(self.app_module.DEBUG)

    def test_language_lookup_uses_video_ids_for_duplicate_titles(self):
        self.video_one.language_names = ["German"]
        self.video_two.language_names = ["French"]

        response = self.client.post(
            "/languages",
            json={"num": 1, "vidIds": ["video-2"]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["current_languages"], ["French"])

    def test_language_lookup_rejects_ambiguous_legacy_title(self):
        self.video_one.language_names = ["German"]
        self.video_two.language_names = ["French"]

        response = self.client.post(
            "/languages",
            json={"num": 1, "vidNames": ["Same title"]},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error_type"], "videoAmbiguous")

    def test_translation_does_not_update_after_localization_read_failure(self):
        self.api.localization_read_errors = {"video-1"}
        self.app_module.translate_api = SimpleNamespace(
            all_language_codes=["es"],
            translate_text=lambda language, text: "Translated " + text,
        )

        with patch.object(self.app_module.time, "sleep"):
            response = self.client.post(
                "/",
                json={
                    "selected_videos": ["video-1"],
                    "selected_languages": ["Spanish"],
                },
            )

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.get_json()["error_type"], "localizationReadFailed"
        )
        self.assertEqual(self.api.localization_calls, [])

    def test_regional_localizations_use_base_name_only_for_display(self):
        video = SimpleNamespace(current_languages=["en-GB"], language_names=[])
        self.api.code_to_name = {"en": "English"}
        self.api.page_videos = [video]

        self.app_module.set_language_names()

        self.assertEqual(video.language_names, ["English"])

    def test_invalid_legacy_post_body_returns_bad_request(self):
        response = self.client.post(
            "/",
            data="null",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error_type"], "invalidRequest")


class ConfigurationRegressionTests(unittest.TestCase):
    def test_debug_flag_honors_value_loaded_from_dotenv(self):
        sys.modules.pop("app", None)

        def load_test_environment():
            os.environ["FLASK_DEBUG"] = "true"

        with patch.dict("os.environ", {}, clear=True), patch(
            "dotenv.load_dotenv", side_effect=load_test_environment
        ), patch("youtube_account.YoutubeApi", return_value=SimpleNamespace()), patch(
            "google_translate.TranslateApi", return_value=SimpleNamespace()
        ):
            module = importlib.import_module("app")

        sys.modules.pop("app", None)
        self.assertTrue(module.DEBUG)


class LegacyYoutubeApiRegressionTests(unittest.TestCase):
    def test_token_cache_permissions_are_restricted_when_loaded(self):
        account = object.__new__(YoutubeApi)
        account.credentials = None

        with patch(
            "youtube_account.os.path.exists",
            side_effect=lambda path: path == "token.pickle",
        ), patch(
            "builtins.open", mock_open()
        ), patch(
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

        payload = pickle.dumps(MaliciousPayload())

        with self.assertRaises(pickle.UnpicklingError):
            youtube_account._load_legacy_credentials(io.BytesIO(payload))

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
            "items": [
                {
                    "localizations": {
                        "en-GB": {"title": "British", "description": "British"},
                        "pt-BR": {"title": "Brazilian", "description": "Brazilian"},
                    }
                }
            ]
        }

        self.assertEqual(
            set(account.get_video_localizations("video-1")),
            {"en-GB", "pt-BR"},
        )

    def test_insecure_oauth_transport_setting_does_not_leak_after_startup(self):
        flow = Mock()
        flow.credentials = SimpleNamespace(valid=True, to_json=lambda: "{}")

        with patch.dict("os.environ", {}, clear=True):
            with patch("youtube_account.os.path.exists", return_value=False), patch(
                "youtube_account.InstalledAppFlow.from_client_secrets_file",
                return_value=flow,
            ), patch("builtins.open", mock_open()), patch(
                "googleapiclient.discovery.build", return_value=Mock()
            ), patch.object(YoutubeApi, "set_uploads_id"), patch.object(
                YoutubeApi, "get_total_video_count"
            ), patch("youtube_account.os.chmod"):
                YoutubeApi()

            self.assertNotIn("OAUTHLIB_INSECURE_TRANSPORT", __import__("os").environ)

    def test_json_token_cache_is_preferred_to_legacy_pickle(self):
        account = object.__new__(YoutubeApi)
        account.credentials = None
        credentials = SimpleNamespace(valid=True)

        def exists(path):
            return path == "token.json"

        with patch("youtube_account.os.path.exists", side_effect=exists), patch(
            "youtube_account.Credentials", create=True
        ) as credentials_class, patch("youtube_account.pickle.load") as legacy_load, patch(
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
            "items": [
                {
                    "id": "video-1",
                    "snippet": {
                        "title": "Original",
                        "description": "Description",
                        "categoryId": "22",
                    },
                    "localizations": {},
                }
            ]
        }

        account.set_video_localization(
            "video-1",
            "es",
            "Spanish",
            "Título",
            "Descripción",
            False,
            "Original",
        )

        self.assertEqual(account.errorStr, "defaultLanguageNotSet")
        account.youtube.videos.return_value.update.assert_not_called()


if __name__ == "__main__":
    unittest.main()
