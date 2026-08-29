"""Localization preview and publish boundary used by the Translate page."""

from typing import Any, Collection, Optional

from localization_service import (
    LocalizationOperationResult,
    preview_localizations,
    publish_localizations,
)


class ManualLocalizationService:
    def __init__(
        self,
        youtube_service: Any,
        supported_language_codes: Optional[Collection[str]] = None,
    ):
        self.youtube = youtube_service
        self.supported_language_codes = set(
            supported_language_codes or youtube_service.supported_language_codes()
        )

    def preview(self, video_id: str, raw_json: str) -> LocalizationOperationResult:
        return preview_localizations(
            self.youtube,
            video_id,
            raw_json,
            self.supported_language_codes,
        )

    def publish(self, video_id: str, raw_json: str) -> LocalizationOperationResult:
        return publish_localizations(
            self.youtube,
            video_id,
            raw_json,
            self.supported_language_codes,
        )
