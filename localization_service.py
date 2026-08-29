"""Orchestration for previewing and publishing translation drafts."""

from dataclasses import dataclass
from typing import Any, Collection, Mapping, Optional

from localizations import (
    LocalizationPlan,
    build_localization_diff,
    build_localization_plan,
    validate_localizations,
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


def _prepare_plan(youtube_api, video_id, draft, supported_language_codes):
    parsed = validate_localizations(draft, supported_language_codes)
    if not parsed.is_valid:
        invalid_result = _invalid_result(parsed)
        return None, invalid_result.plan

    video = youtube_api.get_video_with_localizations(video_id)
    return video, build_localization_plan(video, parsed)


def preview_localizations(
    youtube_api: Any,
    video_id: str,
    draft: Mapping[str, Any],
    supported_language_codes: Collection[str],
) -> LocalizationOperationResult:
    """Validate and preview a translation draft without writing."""
    video, plan = _prepare_plan(
        youtube_api, video_id, draft, supported_language_codes
    )
    return LocalizationOperationResult(video=video, plan=plan, wrote=False)


def publish_localizations(
    youtube_api: Any,
    video_id: str,
    draft: Mapping[str, Any],
    supported_language_codes: Collection[str],
) -> LocalizationOperationResult:
    """Validate, refetch current state, and publish at most one update."""
    video, plan = _prepare_plan(
        youtube_api, video_id, draft, supported_language_codes
    )
    if plan.is_valid and plan.has_changes:
        youtube_api.update_video_localizations(plan.payload)
        return LocalizationOperationResult(video=video, plan=plan, wrote=True)

    return LocalizationOperationResult(video=video, plan=plan, wrote=False)
