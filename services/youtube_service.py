"""YouTube API boundary used by both Streamlit workflow pages."""

from typing import Any, Mapping, Optional

from models import ChannelInfo, MachinePublishResult, PageLimit, VideoSummary, YouTubePage
from youtube_account import YoutubeApi


class YoutubeService:
    """Adapt the existing account client to stateless UI-facing operations."""

    def __init__(self, account: Optional[YoutubeApi] = None):
        self.account = account or YoutubeApi()

    @property
    def code_to_name(self):
        return self.account.code_to_name

    @property
    def name_to_code(self):
        return self.account.name_to_code

    def supported_language_codes(self):
        return set(self.code_to_name.keys()) | {"pt-BR"}

    def fetch_channel(self) -> ChannelInfo:
        return ChannelInfo(
            name=self.account.channel_name,
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

    def publish_machine_localization(
        self,
        video_id: str,
        language_code: str,
        title: str,
        description: str,
        trim: bool,
    ) -> MachinePublishResult:
        before_trimmed = getattr(self.account, "videos_trimmed", 0)
        before_skipped = getattr(self.account, "videos_skipped", 0)
        if hasattr(self.account, "errorStr"):
            self.account.errorStr = ""
        self.account.set_video_localization(
            video_id,
            language_code,
            self.code_to_name.get(language_code, language_code),
            title,
            description,
            trim,
            video_id,
        )
        return MachinePublishResult(
            trimmed=getattr(self.account, "videos_trimmed", 0) - before_trimmed,
            skipped=getattr(self.account, "videos_skipped", 0) - before_skipped,
            error_type=getattr(self.account, "errorStr", None) or None,
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
