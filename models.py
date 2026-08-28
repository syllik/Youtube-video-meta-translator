"""Immutable models shared by the YouTube service and Streamlit UI."""

from dataclasses import dataclass
from typing import Optional, Tuple, Union


PageLimit = Union[int, str]


@dataclass(frozen=True)
class ChannelInfo:
    id: str
    name: str
    description: str
    thumbnail_url: str
    total_videos: int


@dataclass(frozen=True)
class VideoSummary:
    id: str
    title: str
    description: str
    thumbnail_url: str
    current_language_codes: Tuple[str, ...]
    default_language_code: Optional[str] = None


@dataclass(frozen=True)
class YouTubePage:
    videos: Tuple[VideoSummary, ...]
    next_page_token: Optional[str]
