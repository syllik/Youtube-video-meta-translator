"""YouTube API boundary used by both Streamlit workflow pages."""

from typing import Any, Dict, Mapping, Optional

from language_catalog import YouTubeLanguageCatalog, build_language_catalog
from localizations import WRITABLE_SNIPPET_FIELDS, build_video_reset_update_payload
from models import ChannelInfo, PageLimit, VideoSummary, YouTubePage
from youtube_account import YoutubeApi


class YoutubeResetError(RuntimeError):
    """Raised when a localization reset cannot be completed safely."""


class YoutubeService:
    """Adapt the existing account client to stateless UI-facing operations."""

    def __init__(self, account: Optional[YoutubeApi] = None):
        self.account = account or YoutubeApi()
        self._language_catalog_cache: Dict[str, YouTubeLanguageCatalog] = {}

    def fetch_localization_language_catalog(
        self, hl: str = "ru", refresh: bool = False
    ) -> YouTubeLanguageCatalog:
        """Fetch and validate YouTube's current localization language catalog."""
        if not refresh and hl in self._language_catalog_cache:
            return self._language_catalog_cache[hl]
        catalog = build_language_catalog(self.account.list_i18n_languages(hl), hl=hl)
        self._language_catalog_cache[hl] = catalog
        return catalog

    def supported_language_codes(self):
        """Return codes from the current YouTube catalog for compatibility."""
        return set(self.fetch_localization_language_catalog().codes)

    def fetch_channel(self) -> ChannelInfo:
        return ChannelInfo(
            id=self.account.channel_id,
            name=self.account.channel_name,
            description=self.account.channel_description,
            thumbnail_url=self.account.channel_thumbnail,
            total_videos=self.account.total_video_count,
        )

    def fetch_video_page(
        self, limit: PageLimit, page_token: Optional[str] = None
    ) -> YouTubePage:
        raw_page = self.account.fetch_video_page(limit, page_token)
        raw_videos = raw_page.get("videos", ())
        videos = tuple(self._to_video_summary(video) for video in raw_videos)
        return YouTubePage(
            videos=videos,
            next_page_token=raw_page.get("next_page_token"),
        )

    def get_video_with_localizations(self, video_id: str) -> Mapping[str, Any]:
        return self.account.get_video_with_localizations(video_id)

    def update_video_localizations(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.account.update_video_localizations(payload)

    def reset_video_localizations(self, video_id: str) -> Mapping[str, Any]:
        """Delete all localizations while preserving the video's default metadata."""
        video = self.get_video_with_localizations(video_id)
        try:
            payload = build_video_reset_update_payload(video)
        except ValueError as error:
            raise YoutubeResetError(str(error)) from error

        result = self.account.update_video_localizations(payload)
        verified = self.get_video_with_localizations(video_id)
        self._verify_reset(video, verified)
        return result

    @staticmethod
    def _verify_reset(
        source: Mapping[str, Any], verified: Mapping[str, Any]
    ) -> None:
        if (
            not isinstance(source, Mapping)
            or not isinstance(verified, Mapping)
            or verified.get("id") != source.get("id")
        ):
            raise YoutubeResetError(
                "Reset verification failed: YouTube returned a different video"
            )
        source_snippet = source.get("snippet") or {}
        verified_snippet = verified.get("snippet") or {}
        if not isinstance(source_snippet, Mapping) or not isinstance(
            verified_snippet, Mapping
        ):
            raise YoutubeResetError(
                "Reset verification failed: YouTube returned invalid snippet metadata"
            )
        default_language = source_snippet.get("defaultLanguage")
        default_folded = default_language.casefold()
        localizations = verified.get("localizations") or {}
        if not isinstance(localizations, Mapping):
            raise YoutubeResetError(
                "Reset verification failed: YouTube returned invalid localizations"
            )

        remaining = tuple(
            code
            for code in localizations
            if not isinstance(code, str) or code.casefold() != default_folded
        )
        if remaining:
            raise YoutubeResetError(
                "Reset verification failed: non-default localizations remain ({})".format(
                    ", ".join(str(code) for code in remaining)
                )
            )

        for field in WRITABLE_SNIPPET_FIELDS:
            if field in source_snippet and verified_snippet.get(field) != source_snippet[field]:
                raise YoutubeResetError(
                    "Reset verification failed: default snippet.{} changed".format(
                        field
                    )
                )

    @staticmethod
    def _to_video_summary(video: Any) -> VideoSummary:
        if isinstance(video, VideoSummary):
            return video
        if isinstance(video, Mapping):
            return VideoSummary(
                id=str(video["id"]),
                title=str(video.get("title", "")),
                description=str(video.get("description", "")),
                thumbnail_url=str(video.get("thumbnail_url", "")),
                current_language_codes=tuple(video.get("current_language_codes", ())),
                default_language_code=video.get("default_language_code"),
            )
        return VideoSummary(
            id=str(video.id),
            title=str(video.video_title),
            description=str(video.description),
            thumbnail_url=str(video.thumbnail_url),
            current_language_codes=tuple(video.current_languages),
            default_language_code=getattr(video, "default_language_code", None),
        )
