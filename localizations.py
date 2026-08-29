"""Pure parsing, validation, diff, and merge helpers for YouTube localizations."""

import copy
import json
from dataclasses import dataclass
from typing import Any, Collection, Dict, Mapping, Optional, Tuple


MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 5000
LOCALIZATION_FIELDS = frozenset(("title", "description"))
WRITABLE_SNIPPET_FIELDS = (
    "title",
    "description",
    "categoryId",
    "tags",
    "defaultLanguage",
    "defaultAudioLanguage",
)


def build_video_reset_update_payload(
    video_resource: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build a safe update that removes every localization from one video."""
    issues = _source_issues(video_resource)
    if issues:
        raise ValueError(issues[0].message)

    resource = copy.deepcopy(dict(video_resource))
    snippet = resource["snippet"]
    default_language = snippet.get("defaultLanguage")
    if not isinstance(default_language, str) or not default_language.strip():
        raise ValueError(
            "Cannot reset localizations safely: snippet.defaultLanguage is missing"
        )
    payload = {
        "id": resource["id"],
        "snippet": {},
        "localizations": {
            default_language: {
                "title": snippet["title"],
                "description": snippet["description"],
            }
        },
    }
    for field in WRITABLE_SNIPPET_FIELDS:
        if field in snippet:
            payload["snippet"][field] = copy.deepcopy(snippet[field])
    return payload


@dataclass(frozen=True)
class LocalizationValue:
    title: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        return {"title": self.title, "description": self.description}


@dataclass(frozen=True)
class LocalizationIssue:
    language_code: Optional[str]
    message: str
    path: Optional[str] = None


@dataclass(frozen=True)
class ParsedLocalizations:
    entries: Mapping[str, LocalizationValue]
    issues: Tuple[LocalizationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues and bool(self.entries)

    @property
    def invalid_entries(self) -> Tuple[LocalizationIssue, ...]:
        return self.issues


@dataclass(frozen=True)
class LocalizationDiff:
    language_code: str
    status: str
    submitted: LocalizationValue
    existing: Optional[LocalizationValue]


@dataclass(frozen=True)
class LocalizationPlan:
    diffs: Tuple[LocalizationDiff, ...]
    issues: Tuple[LocalizationIssue, ...]
    payload: Optional[Dict[str, Any]]
    preserved_language_codes: Tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues and self.payload is not None

    @property
    def has_changes(self) -> bool:
        return any(item.status in ("added", "changed") for item in self.diffs)


def _catalog_lookup_key(language_code: str) -> str:
    """Build a case-insensitive lookup key for a catalog language code."""
    return language_code.strip().casefold()


def _supported_language_map(
    supported_language_codes: Collection[str],
) -> Dict[str, str]:
    return {
        _catalog_lookup_key(code): code.strip()
        for code in supported_language_codes
        if isinstance(code, str) and _catalog_lookup_key(code)
    }


def _document_issue(message: str) -> ParsedLocalizations:
    return ParsedLocalizations(
        entries={},
        issues=(LocalizationIssue(None, message),),
    )


def parse_localizations_json(
    raw_json: str,
    supported_language_codes: Collection[str],
) -> ParsedLocalizations:
    """Parse and validate a localization-map JSON document."""
    try:
        document = json.loads(raw_json)
    except json.JSONDecodeError as error:
        return _document_issue(
            "Invalid JSON at line {}, column {}: {}".format(
                error.lineno, error.colno, error.msg
            )
        )
    except (TypeError, ValueError) as error:
        message = "Invalid JSON"
        if getattr(error, "msg", None):
            message = "{}: {}".format(message, error.msg)
        return _document_issue(message)

    return validate_localizations(document, supported_language_codes)


def validate_localizations(
    document: Any,
    supported_language_codes: Collection[str],
) -> ParsedLocalizations:
    """Validate an already-decoded localization map."""
    if not isinstance(document, dict):
        return _document_issue("Localization document must be a JSON object")

    if not document:
        return _document_issue("At least one localization is required")

    supported = _supported_language_map(supported_language_codes)
    entries: Dict[str, LocalizationValue] = {}
    issues = []

    for raw_language_code in sorted(document.keys(), key=lambda value: str(value)):
        if not isinstance(raw_language_code, str):
            issues.append(
                LocalizationIssue(
                    None,
                    "Language code must be a string",
                    path=str(raw_language_code),
                )
            )
            continue

        catalog_key = _catalog_lookup_key(raw_language_code)
        language_code = supported.get(catalog_key)
        if language_code is None:
            issues.append(
                LocalizationIssue(
                    raw_language_code,
                    "Unsupported language code: {}".format(raw_language_code),
                    path=raw_language_code,
                )
            )
            continue

        if language_code in entries:
            issues.append(
                LocalizationIssue(
                    raw_language_code,
                    "Duplicate language code after normalization: {}".format(
                        language_code
                    ),
                    path=raw_language_code,
                )
            )
            continue

        value = document[raw_language_code]
        if not isinstance(value, dict):
            issues.append(
                LocalizationIssue(
                    raw_language_code,
                    "Localization must be an object",
                    path=language_code,
                )
            )
            continue

        entry_issues = []
        missing_fields = sorted(LOCALIZATION_FIELDS - set(value.keys()))
        unknown_fields = sorted(set(value.keys()) - LOCALIZATION_FIELDS)

        for field in missing_fields:
            entry_issues.append(
                LocalizationIssue(
                    language_code,
                    "Missing required field: {}".format(field),
                    path="{}.{}".format(language_code, field),
                )
            )

        if unknown_fields:
            entry_issues.append(
                LocalizationIssue(
                    language_code,
                    "Unknown field(s): {}".format(", ".join(unknown_fields)),
                    path=language_code,
                )
            )

        title = value.get("title")
        description = value.get("description")

        if "title" in value and not isinstance(title, str):
            entry_issues.append(
                LocalizationIssue(
                    language_code,
                    "Title must be a string",
                    path="{}.title".format(language_code),
                )
            )
        elif isinstance(title, str):
            if not title.strip():
                entry_issues.append(
                    LocalizationIssue(
                        language_code,
                        "Title must not be empty",
                        path="{}.title".format(language_code),
                    )
                )
            elif len(title) > MAX_TITLE_LENGTH:
                entry_issues.append(
                    LocalizationIssue(
                        language_code,
                        "Title is too long: {} / {} characters".format(
                            len(title), MAX_TITLE_LENGTH
                        ),
                        path="{}.title".format(language_code),
                    )
                )

        if "description" in value and not isinstance(description, str):
            entry_issues.append(
                LocalizationIssue(
                    language_code,
                    "Description must be a string",
                    path="{}.description".format(language_code),
                )
            )
        elif isinstance(description, str) and len(description) > MAX_DESCRIPTION_LENGTH:
            entry_issues.append(
                LocalizationIssue(
                    language_code,
                    "Description is too long: {} / {} characters".format(
                        len(description), MAX_DESCRIPTION_LENGTH
                    ),
                    path="{}.description".format(language_code),
                )
            )

        if entry_issues:
            issues.extend(entry_issues)
            continue

        entries[language_code] = LocalizationValue(title, description)

    return ParsedLocalizations(entries=entries, issues=tuple(issues))


def _as_localization_value(value: Any) -> Optional[LocalizationValue]:
    if isinstance(value, LocalizationValue):
        return value
    if isinstance(value, Mapping):
        title = value.get("title")
        description = value.get("description")
        if isinstance(title, str) and isinstance(description, str):
            return LocalizationValue(title, description)
    return None


def build_localization_diff(
    existing: Mapping[str, Any],
    submitted: Mapping[str, LocalizationValue],
) -> Tuple[LocalizationDiff, ...]:
    """Compare submitted entries against the current YouTube localizations."""
    diffs = []
    for language_code in sorted(submitted.keys()):
        submitted_value = _as_localization_value(submitted[language_code])
        if submitted_value is None:
            continue

        existing_value = _as_localization_value(existing.get(language_code))
        if existing_value is None:
            status = "added"
        elif existing_value == submitted_value:
            status = "unchanged"
        else:
            status = "changed"

        diffs.append(
            LocalizationDiff(
                language_code=language_code,
                status=status,
                submitted=submitted_value,
                existing=existing_value,
            )
        )

    return tuple(diffs)


def merge_localizations(
    existing: Mapping[str, Any],
    submitted: Mapping[str, LocalizationValue],
) -> Dict[str, Dict[str, str]]:
    """Merge submitted entries into every existing localization."""
    merged = {}
    for language_code, value in existing.items():
        if isinstance(value, LocalizationValue):
            merged[language_code] = value.to_dict()
        else:
            merged[language_code] = copy.deepcopy(value)

    for language_code in sorted(submitted.keys()):
        value = _as_localization_value(submitted[language_code])
        if value is not None:
            merged[language_code] = value.to_dict()

    return merged


def _source_issues(video_resource: Mapping[str, Any]) -> Tuple[LocalizationIssue, ...]:
    issues = []
    if not isinstance(video_resource, Mapping):
        return (LocalizationIssue(None, "YouTube video resource must be an object"),)

    if not video_resource.get("id"):
        issues.append(LocalizationIssue(None, "Video resource is missing id", path="id"))

    snippet = video_resource.get("snippet")
    if not isinstance(snippet, Mapping):
        return tuple(
            issues
            + [LocalizationIssue(None, "Video resource is missing snippet", path="snippet")]
        )

    for field in ("title", "description", "categoryId"):
        if field not in snippet or snippet[field] is None:
            issues.append(
                LocalizationIssue(
                    None,
                    "Video resource is missing snippet.{}".format(field),
                    path="snippet.{}".format(field),
                )
            )

    return tuple(issues)


def build_video_update_payload(
    video_resource: Mapping[str, Any],
    submitted: Mapping[str, LocalizationValue],
) -> Dict[str, Any]:
    """Build one safe ``videos.update`` body from the fetched resource."""
    issues = _source_issues(video_resource)
    if issues:
        raise ValueError(issues[0].message)

    resource = copy.deepcopy(dict(video_resource))
    snippet = resource["snippet"]
    existing = resource.get("localizations") or {}
    if not isinstance(existing, Mapping):
        existing = {}

    payload = {
        "id": resource["id"],
        "snippet": {},
        "localizations": merge_localizations(existing, submitted),
    }
    for field in WRITABLE_SNIPPET_FIELDS:
        if field in snippet:
            payload["snippet"][field] = copy.deepcopy(snippet[field])

    return payload


def build_localization_plan(
    video_resource: Mapping[str, Any],
    parsed: ParsedLocalizations,
) -> LocalizationPlan:
    """Create a diff and payload, disabling writes for any validation issue."""
    existing = {}
    if isinstance(video_resource, Mapping):
        raw_existing = video_resource.get("localizations") or {}
        if isinstance(raw_existing, Mapping):
            existing = raw_existing

    diffs = build_localization_diff(existing, parsed.entries)
    preserved = tuple(sorted(set(existing.keys()) - set(parsed.entries.keys())))
    issues = tuple(parsed.issues) + _source_issues(video_resource)
    payload = None
    if not issues:
        payload = build_video_update_payload(video_resource, parsed.entries)

    return LocalizationPlan(
        diffs=diffs,
        issues=issues,
        payload=payload,
        preserved_language_codes=preserved,
    )
