"""YouTube boundary for translation draft review, publishing, and reset."""

from typing import Any, Collection, Mapping

from localization_service import (
    LocalizationOperationResult,
    preview_localizations,
    publish_localizations,
)


class LocalizationService:
    """Expose neutral translation operations to Streamlit UI boundaries."""

    def __init__(
        self, youtube: Any, supported_language_codes: Collection[str] = ()
    ):
        self.youtube = youtube
        self.supported_language_codes = tuple(supported_language_codes)

    def preview(
        self, video_id: str, draft: Mapping[str, Any]
    ) -> LocalizationOperationResult:
        return preview_localizations(
            self.youtube,
            video_id,
            draft,
            self.supported_language_codes,
        )

    def publish(
        self, video_id: str, draft: Mapping[str, Any]
    ) -> LocalizationOperationResult:
        return publish_localizations(
            self.youtube,
            video_id,
            draft,
            self.supported_language_codes,
        )

    def reset(self, video_id: str):
        """Run the dedicated destructive reset operation for one video."""
        return self.youtube.reset_video_localizations(video_id)
