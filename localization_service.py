"""Orchestration for previewing and publishing translation drafts."""

import copy
from dataclasses import dataclass
from typing import Any, Collection, Mapping, Optional

from localizations import (
    LocalizationIssue,
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


def _resource_snapshot(video_resource: Mapping[str, Any]):
    if not isinstance(video_resource, Mapping):
        return None

    snippet = video_resource.get("snippet")
    if not isinstance(snippet, Mapping):
        snippet = {}

    localizations = video_resource.get("localizations")
    if not isinstance(localizations, Mapping):
        localizations = {}

    snapshot = {
        "id": video_resource.get("id"),
        "snippet": copy.deepcopy(dict(snippet)),
        "localizations": copy.deepcopy(dict(localizations)),
    }
    if video_resource.get("etag") is not None:
        snapshot["etag"] = video_resource.get("etag")
    return snapshot


def _resource_matches_video_id(
    video_resource: Mapping[str, Any], video_id: str
) -> bool:
    return isinstance(video_resource, Mapping) and video_resource.get("id") == video_id


def _conflict_plan(video_resource, parsed, message: str) -> LocalizationPlan:
    existing = {}
    if isinstance(video_resource, Mapping) and isinstance(
        video_resource.get("localizations"), Mapping
    ):
        existing = video_resource["localizations"]
    return LocalizationPlan(
        diffs=build_localization_diff(existing, parsed.entries),
        issues=(LocalizationIssue(None, message),),
        payload=None,
        preserved_language_codes=(),
    )


def _is_precondition_failed(error: Exception) -> bool:
    status = getattr(getattr(error, "resp", None), "status", None)
    if str(status) == "412":
        return True

    details = getattr(error, "error_details", None) or []
    for detail in details:
        if not isinstance(detail, Mapping):
            continue
        reason = str(detail.get("reason") or "")
        if reason in {"conditionNotMet", "preconditionFailed", "failedPrecondition"}:
            return True
    return False


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
    expected_video: Optional[Mapping[str, Any]] = None,
) -> LocalizationOperationResult:
    """Validate, refetch current state, and publish at most one update."""
    parsed = validate_localizations(draft, supported_language_codes)
    if not parsed.is_valid:
        invalid_result = _invalid_result(parsed)
        return LocalizationOperationResult(
            video=None, plan=invalid_result.plan, wrote=False
        )

    video = youtube_api.get_video_with_localizations(video_id)
    if not _resource_matches_video_id(video, video_id):
        return LocalizationOperationResult(
            video=video,
            plan=_conflict_plan(
                video,
                parsed,
                "YouTube returned a different video. Refresh the list and Preview again before publishing.",
            ),
            wrote=False,
        )
    if expected_video is not None and (
        not _resource_matches_video_id(expected_video, video_id)
        or _resource_snapshot(expected_video) != _resource_snapshot(video)
    ):
        return LocalizationOperationResult(
            video=video,
            plan=_conflict_plan(
                video,
                parsed,
                "YouTube changed after Preview. Fetch the latest video state and Preview again before publishing.",
            ),
            wrote=False,
        )

    plan = build_localization_plan(video, parsed)
    if plan.is_valid and plan.has_changes:
        try:
            youtube_api.update_video_localizations(
                plan.payload, if_match=video.get("etag")
            )
        except Exception as error:
            if _is_precondition_failed(error):
                return LocalizationOperationResult(
                    video=video,
                    plan=_conflict_plan(
                        video,
                        parsed,
                        "YouTube changed before YouTube accepted the update. Fetch the latest video state and Preview again before publishing.",
                    ),
                    wrote=False,
                )
            raise
        return LocalizationOperationResult(video=video, plan=plan, wrote=True)

    return LocalizationOperationResult(video=video, plan=plan, wrote=False)
