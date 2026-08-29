"""Pure helpers for source-aware translation packages and localization JSON."""

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from localizations import LocalizationIssue, ParsedLocalizations, validate_localizations


LLM_BATCH_SIZE = 10


class _DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object repeats one of its members."""


def _reject_duplicate_json_keys(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    document = {}
    for key, value in pairs:
        if key in document:
            raise _DuplicateJsonKeyError(
                "Duplicate JSON object key: {}".format(key)
            )
        document[key] = value
    return document


@dataclass(frozen=True)
class LlmTranslationProgress:
    current: int
    total: int
    missing: Tuple[YouTubeLanguage, ...]

    @property
    def missing_count(self) -> int:
        return len(self.missing)


def calculate_llm_translation_progress(
    video_resource: Mapping[str, Any],
    catalog: YouTubeLanguageCatalog,
    excluded_source_codes: Sequence[str] = (),
) -> LlmTranslationProgress:
    """Calculate missing targets from the metadata language catalog."""
    snippet = video_resource.get("snippet")
    default_language = (
        snippet.get("defaultLanguage") if isinstance(snippet, Mapping) else None
    )
    default_code = (
        default_language.casefold() if isinstance(default_language, str) else None
    )
    excluded_codes = {
        code.strip().casefold()
        for code in excluded_source_codes
        if isinstance(code, str) and code.strip()
    }

    supported_languages = tuple(
        language
        for language in catalog.languages
        if language.code.casefold() != default_code
    )
    existing_localizations = video_resource.get("localizations") or {}
    existing_codes = (
        {
            code.casefold()
            for code in existing_localizations
            if isinstance(code, str)
        }
        if isinstance(existing_localizations, Mapping)
        else set()
    )
    missing = tuple(
        language
        for language in supported_languages
        if language.code.casefold() not in existing_codes
        and language.code.casefold() not in excluded_codes
    )
    return LlmTranslationProgress(
        current=len(supported_languages) - len(missing),
        total=len(supported_languages),
        missing=missing,
    )


def select_next_llm_languages(
    progress: LlmTranslationProgress, batch_size: int = LLM_BATCH_SIZE
) -> Tuple[YouTubeLanguage, ...]:
    """Select the next bounded batch from catalog-ordered missing languages."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    return progress.missing[:batch_size]


def build_selected_llm_languages(
    progress: LlmTranslationProgress,
    selected_codes: Sequence[str],
    max_count: Optional[int] = LLM_BATCH_SIZE,
) -> Tuple[YouTubeLanguage, ...]:
    """Normalize and validate an explicit subset of missing languages."""
    if max_count is not None and max_count <= 0:
        raise ValueError("max_count must be positive")

    selected = []
    normalized = set()
    for raw_code in selected_codes:
        if not isinstance(raw_code, str) or not raw_code.strip():
            raise ValueError("selected language codes must be non-empty strings")
        code = raw_code.strip().casefold()
        if code in normalized:
            raise ValueError("duplicate selected language code: {}".format(raw_code))
        normalized.add(code)
        selected.append(code)

    if max_count is not None and len(selected) > max_count:
        raise ValueError(
            "no more than {} languages may be selected".format(max_count)
        )

    by_code = {
        language.code.casefold(): language for language in progress.missing
    }
    unknown = [code for code in selected if code not in by_code]
    if unknown:
        raise ValueError("language is not a missing target: {}".format(unknown[0]))

    return tuple(
        language
        for language in progress.missing
        if language.code.casefold() in normalized
    )


def _catalog_code_map(catalog: YouTubeLanguageCatalog):
    if catalog is None:
        return {}
    return {
        language.code.casefold(): language.code for language in catalog.languages
    }


def _canonical_source_code(raw_code: Any, catalog: YouTubeLanguageCatalog) -> str:
    if not isinstance(raw_code, str) or not raw_code.strip():
        return ""
    stripped = raw_code.strip()
    return _catalog_code_map(catalog).get(stripped.casefold(), stripped)


def build_translation_source_candidates(
    video_resource: Mapping[str, Any], catalog: YouTubeLanguageCatalog = None
) -> Tuple[Dict[str, Any], ...]:
    """Extract the default source and real existing localization references."""
    snippet = video_resource.get("snippet")
    if not isinstance(snippet, Mapping):
        return ()

    default_code = _canonical_source_code(snippet.get("defaultLanguage"), catalog)
    if not default_code:
        return ()

    sources = [{
        "languageCode": default_code,
        "title": snippet.get("title", ""),
        "description": snippet.get("description", ""),
    }]
    localizations = video_resource.get("localizations") or {}
    if not isinstance(localizations, Mapping):
        return tuple(sources)

    for raw_code, value in localizations.items():
        code = _canonical_source_code(raw_code, catalog)
        if not code or code.casefold() == default_code.casefold():
            continue
        if not isinstance(value, Mapping):
            continue
        title = value.get("title")
        description = value.get("description")
        if not isinstance(title, str) or not isinstance(description, str):
            continue
        sources.append({
            "languageCode": code,
            "title": title,
            "description": description,
        })
    return tuple(sources)


def normalize_translation_source_codes(
    video_resource: Mapping[str, Any],
    selected_source_codes: Sequence[str],
    catalog: YouTubeLanguageCatalog = None,
) -> Tuple[str, ...]:
    """Return canonical selected source codes with the default source first."""
    candidates = build_translation_source_candidates(video_resource, catalog)
    if not candidates:
        raise ValueError("Video resource is missing defaultLanguage source metadata")

    by_code = {
        source["languageCode"].casefold(): source["languageCode"]
        for source in candidates
    }
    default_code = candidates[0]["languageCode"]
    requested = selected_source_codes or (default_code,)
    selected = []
    seen = set()
    for raw_code in requested:
        canonical = _canonical_source_code(raw_code, catalog)
        if not canonical or canonical.casefold() not in by_code:
            raise ValueError("language is not an available source: {}".format(raw_code))
        canonical = by_code[canonical.casefold()]
        if canonical.casefold() not in seen:
            selected.append(canonical)
            seen.add(canonical.casefold())

    if default_code.casefold() not in seen:
        selected.insert(0, default_code)
    else:
        selected = [
            default_code,
            *[code for code in selected if code.casefold() != default_code.casefold()],
        ]
    return tuple(selected)


def build_llm_translation_package(
    video_resource: Mapping[str, Any],
    languages: Sequence[YouTubeLanguage],
    selected_source_codes: Sequence[str] = (),
    catalog: YouTubeLanguageCatalog = None,
) -> Dict[str, Any]:
    """Build a package with one authoritative source and optional references."""
    candidates = build_translation_source_candidates(video_resource, catalog)
    selected_codes = normalize_translation_source_codes(
        video_resource, selected_source_codes, catalog
    )
    selected_by_code = {code.casefold() for code in selected_codes}
    primary = candidates[0]
    references = [
        source
        for source in candidates[1:]
        if source["languageCode"].casefold() in selected_by_code
    ]
    targets = [
        language
        for language in languages
        if language.code.casefold() not in selected_by_code
    ]
    return {
        "source": {"primary": primary, "references": references},
        "targetLanguages": [
            {"code": language.code, "name": language.name} for language in targets
        ],
        "expectedLanguageCodes": [language.code for language in targets],
        "expectedCount": len(targets),
    }


def build_llm_localization_schema(
    expected_language_codes: Sequence[str],
) -> Dict[str, Any]:
    """Build an exact JSON Schema for one direct localization map."""
    codes = []
    normalized = set()

    for raw_code in expected_language_codes:
        if not isinstance(raw_code, str) or not raw_code.strip():
            raise ValueError("expected language codes must be non-empty strings")
        code = raw_code.strip()
        folded = code.casefold()
        if folded in normalized:
            raise ValueError("duplicate expected language code: {}".format(code))
        normalized.add(folded)
        codes.append(code)

    if not codes:
        raise ValueError("at least one expected language code is required")

    properties = {}
    for code in codes:
        properties[code] = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                },
                "description": {
                    "type": "string",
                    "maxLength": 5000,
                },
            },
            "required": ["title", "description"],
            "additionalProperties": False,
        }

    return {
        "type": "object",
        "properties": properties,
        "required": codes,
        "additionalProperties": False,
    }


def build_llm_translation_prompt(package: Mapping[str, Any]) -> str:
    """Build strict instructions for one downloadable localization JSON file."""
    package_json = json.dumps(package, ensure_ascii=False, indent=2)
    return """Translate the primary source metadata in this package into every exact target code.

The primary source is authoritative and determines the intended meaning. Any
reference sources are verified existing translations: use them only to clarify
intent, tone, and semantic nuance. If a reference conflicts with the primary
source, follow the primary source. Do not treat references as competing originals.

Return one attached, downloadable UTF-8 `.json` file. The file must contain a
direct JSON object whose keys are the exact language codes in
`expectedLanguageCodes`; each key's value must contain only `title` and
`description`. Do not return a wrapper.

Preserve meaning, tone, proper names, URLs, hashtags, technical tokens, and
meaningful line breaks. Keep titles at most 100 characters and descriptions at
most 5000 characters. Before creating the file, verify that its key set exactly
matches `expectedLanguageCodes`.

Do not use `catalog`, `languages`, `source`, `outputContract`, or
`schemaVersion` as output keys. Do not use language names as keys. Do not
return Markdown, a code block, or prose.

Package:
{}""".format(package_json)


def parse_llm_upload_json(
    raw_json: str, expected_language_codes: Sequence[str]
) -> ParsedLocalizations:
    """Parse one exact expected localization batch without mutating state."""
    parsed = parse_localization_upload_json(raw_json, expected_language_codes)
    expected_by_code = {
        code.strip().casefold(): code.strip()
        for code in expected_language_codes
        if isinstance(code, str) and code.strip()
    }
    parsed_codes = {language_code.casefold() for language_code in parsed.entries}
    missing_codes = sorted(set(expected_by_code) - parsed_codes)
    if not missing_codes:
        return parsed

    missing_issues = tuple(
        LocalizationIssue(
            expected_by_code[code],
            "Missing required language code: {}".format(expected_by_code[code]),
            path=expected_by_code[code],
        )
        for code in missing_codes
    )
    return ParsedLocalizations(entries=parsed.entries, issues=parsed.issues + missing_issues)


def parse_localization_upload_json(
    raw_json: str, supported_language_codes: Sequence[str]
) -> ParsedLocalizations:
    """Parse any non-empty valid localization map without requiring a target set."""
    try:
        document = json.loads(raw_json, object_pairs_hook=_reject_duplicate_json_keys)
    except _DuplicateJsonKeyError as error:
        return ParsedLocalizations(
            entries={}, issues=(LocalizationIssue(None, str(error)),)
        )
    except json.JSONDecodeError as error:
        return ParsedLocalizations(
            entries={},
            issues=(
                LocalizationIssue(
                    None,
                    "Invalid JSON at line {}, column {}: {}".format(
                        error.lineno, error.colno, error.msg
                    ),
                ),
            ),
        )
    except (TypeError, ValueError) as error:
        message = "Invalid JSON"
        if getattr(error, "msg", None):
            message = "{}: {}".format(message, error.msg)
        return ParsedLocalizations(
            entries={}, issues=(LocalizationIssue(None, message),)
        )

    return validate_localizations(document, supported_language_codes)
