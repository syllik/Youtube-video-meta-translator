"""YouTube API boundary used by both Streamlit workflow pages."""

from typing import Any, Dict, Mapping, Optional

from language_catalog import YouTubeLanguageCatalog, build_language_catalog
from models import ChannelInfo, PageLimit, VideoSummary, YouTubePage
from youtube_account import YoutubeApi


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
