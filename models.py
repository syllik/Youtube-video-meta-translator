"""Immutable models shared by the YouTube service and Streamlit UI."""

from dataclasses import dataclass
from typing import Optional, Tuple, Union


PageLimit = Union[int, str]


@dataclass(frozen=True)
class ChannelInfo:
    name: str
    thumbnail_url: str
    total_videos: int


@dataclass(frozen=True)
class VideoSummary:
    id: str
    title: str
    description: str
    thumbnail_url: str
    current_language_codes: Tuple[str, ...]


@dataclass(frozen=True)
class YouTubePage:
    videos: Tuple[VideoSummary, ...]
    next_page_token: Optional[str]


@dataclass(frozen=True)
class MachinePublishResult:
    trimmed: int = 0
    skipped: int = 0
    error_type: Optional[str] = None
