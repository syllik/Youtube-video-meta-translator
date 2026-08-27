"""Orchestration for previewing and publishing manual localizations."""

from dataclasses import dataclass
from typing import Any, Collection, Mapping, Optional

from localizations import (
    LocalizationPlan,
    build_localization_diff,
    build_localization_plan,
    parse_localizations_json,
)


@dataclass(frozen=True)
class LocalizationOperationResult:
    video: Optional[Mapping[str, Any]]
    plan: LocalizationPlan
    wrote: bool


def _invalid_result(parsed) -> LocalizationOperationResult:
    plan = LocalizationPlan(
        diffs=build_localization_diff({}, parsed.entries),
        issues=parsed.issues,
        payload=None,
        preserved_language_codes=(),
    )
    return LocalizationOperationResult(video=None, plan=plan, wrote=False)


def _prepare_plan(youtube_api, video_id, raw_json, supported_language_codes):
    parsed = parse_localizations_json(raw_json, supported_language_codes)
    if not parsed.is_valid:
        invalid_result = _invalid_result(parsed)
        return None, invalid_result.plan

    video = youtube_api.get_video_with_localizations(video_id)
    return video, build_localization_plan(video, parsed)


def preview_localizations(
    youtube_api: Any,
    video_id: str,
    raw_json: str,
    supported_language_codes: Collection[str],
) -> LocalizationOperationResult:
    """Validate and preview a localization update without writing."""
    video, plan = _prepare_plan(
        youtube_api, video_id, raw_json, supported_language_codes
    )
    return LocalizationOperationResult(video=video, plan=plan, wrote=False)


def publish_localizations(
    youtube_api: Any,
    video_id: str,
    raw_json: str,
    supported_language_codes: Collection[str],
) -> LocalizationOperationResult:
    """Validate, fetch current state, and publish at most one update."""
    video, plan = _prepare_plan(
        youtube_api, video_id, raw_json, supported_language_codes
    )
    if plan.is_valid and plan.has_changes:
        youtube_api.update_video_localizations(plan.payload)
        return LocalizationOperationResult(video=video, plan=plan, wrote=True)

    return LocalizationOperationResult(video=video, plan=plan, wrote=False)
