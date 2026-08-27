import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from google_translate import TranslationError
from services.machine_translation_service import (
    MachineTranslationOptions,
    MachineTranslationService,
)


class MachineTranslationServiceTests(unittest.TestCase):
    def test_deepl_falls_back_to_google_when_deepl_is_unavailable(self):
        deepl = Mock()
        deepl.get_target_languages.return_value = [SimpleNamespace(code="ES")]
        deepl.translate_text.side_effect = RuntimeError("DeepL unavailable")
        google = Mock()
        google.all_language_codes = ["es"]
        google.translate_text.return_value = "Google result"
        youtube = Mock()
        youtube.get_video_with_localizations.return_value = {
            "id": "video-1",
            "snippet": {"title": "Original", "description": "Text", "categoryId": "22"},
            "localizations": {},
        }
        youtube.publish_machine_localization.return_value = SimpleNamespace(
            trimmed=0, skipped=0, error_type=None
        )

        service = MachineTranslationService(youtube, deepl=deepl, google=google)
        result = service.translate_and_publish(
            ["video-1"], ["es"], MachineTranslationOptions(True, False, False)
        )

        self.assertEqual(result.translated, 1)
        google.translate_text.assert_called()
        youtube.publish_machine_localization.assert_called_once_with(
            "video-1", "es", "Google result", "Google result", False
        )

    def test_existing_language_is_skipped_when_overwrite_is_off(self):
        youtube = Mock()
        youtube.get_video_with_localizations.return_value = {
            "id": "video-1",
            "snippet": {"title": "Original", "description": "Text", "categoryId": "22"},
            "localizations": {"es": {"title": "Old", "description": "Old"}},
        }
        service = MachineTranslationService(youtube, deepl=None, google=Mock())

        result = service.translate_and_publish(
            ["video-1"], ["es"], MachineTranslationOptions(False, False, False)
        )

        self.assertEqual(result.skipped, 1)
        youtube.publish_machine_localization.assert_not_called()

    def test_provider_error_is_reported_without_publishing(self):
        youtube = Mock()
        youtube.get_video_with_localizations.return_value = {
            "id": "video-1",
            "snippet": {"title": "Original", "description": "Text", "categoryId": "22"},
            "localizations": {},
        }
        google = Mock()
        google.all_language_codes = ["es"]
        google.translate_text.side_effect = TranslationError("failed")

        service = MachineTranslationService(youtube, deepl=None, google=google)
        result = service.translate_and_publish(
            ["video-1"], ["es"], MachineTranslationOptions(False, False, False)
        )

        self.assertEqual(result.errors[0].error_type, "translation_failed")
        youtube.publish_machine_localization.assert_not_called()


if __name__ == "__main__":
    unittest.main()
