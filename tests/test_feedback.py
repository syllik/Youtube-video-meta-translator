import sys
import unittest
from unittest.mock import patch

from googleapiclient.errors import HttpError
from httplib2 import Response

from ui.feedback import render_feedback, render_service_error
from youtube_account import YoutubeSetupError, YoutubeVideoNotFoundError


class _FakeStreamlit:
    def __init__(self):
        self.calls = []

    def error(self, message):
        self.calls.append(("error", message))

    def warning(self, message):
        self.calls.append(("warning", message))

    def info(self, message):
        self.calls.append(("info", message))

    def success(self, message):
        self.calls.append(("success", message))


def _http_error(status, reason, message="private diagnostic"):
    body = (
        '{"error":{"code":%d,"message":"%s",'
        '"errors":[{"reason":"%s"}]}}'
    ) % (status, message, reason)
    return HttpError(
        Response({"status": str(status)}),
        body.encode("utf-8"),
    )


class FeedbackTests(unittest.TestCase):
    def test_missing_oauth_client_has_exact_path_and_action(self):
        fake = _FakeStreamlit()

        with patch.dict(sys.modules, {"streamlit": fake}):
            render_service_error(YoutubeSetupError("oauth_client_missing"))

        self.assertEqual(fake.calls[0][0], "error")
        self.assertIn("config/account_client_secrets_main.json", fake.calls[0][1])
        self.assertIn("Desktop app", fake.calls[0][1])
        self.assertIn("restart the app", fake.calls[0][1])

    def test_malformed_oauth_client_does_not_show_raw_error(self):
        fake = _FakeStreamlit()
        raw = "client_secret=super-secret-token"

        with patch.dict(sys.modules, {"streamlit": fake}):
            render_service_error(YoutubeSetupError("oauth_client_invalid"))

        self.assertEqual(fake.calls[0][0], "error")
        self.assertIn("found", fake.calls[0][1])
        self.assertIn("Desktop app", fake.calls[0][1])
        self.assertNotIn(raw, fake.calls[0][1])

    def test_auth_quota_missing_video_and_network_use_error_severity(self):
        cases = (
            (
                _http_error(401, "authError"),
                "Authorization is no longer valid.",
            ),
            (
                _http_error(403, "quotaExceeded"),
                "YouTube API quota is exhausted.",
            ),
            (
                YoutubeVideoNotFoundError("private raw detail"),
                "The selected video was not found.",
            ),
            (
                ConnectionError("private token and stack detail"),
                "Could not reach YouTube/Google.",
            ),
        )

        for error, expected in cases:
            with self.subTest(type=type(error).__name__):
                fake = _FakeStreamlit()
                with patch.dict(sys.modules, {"streamlit": fake}):
                    render_service_error(error)
                self.assertEqual(fake.calls[0][0], "error")
                self.assertIn(expected, fake.calls[0][1])
                self.assertNotIn("private token", fake.calls[0][1])
                self.assertNotIn("private raw detail", fake.calls[0][1])

    def test_semantic_quota_feedback_uses_error_renderer(self):
        fake = _FakeStreamlit()

        with patch.dict(sys.modules, {"streamlit": fake}):
            render_feedback("ignored", "quota_exceeded")

        self.assertEqual(fake.calls[0][0], "error")


if __name__ == "__main__":
    unittest.main()
