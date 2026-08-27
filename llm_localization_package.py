"""Pure helpers for the prompt-only LLM localization workflow."""

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from localizations import LocalizationIssue, ParsedLocalizations, validate_localizations


LLM_BATCH_SIZE = 10


@dataclass(frozen=True)
class LlmTranslationProgress:
    current: int
    total: int
    missing: Tuple[YouTubeLanguage, ...]

    @property
    def missing_count(self) -> int:
        return len(self.missing)


def calculate_llm_translation_progress(
    video_resource: Mapping[str, Any], catalog: YouTubeLanguageCatalog
) -> LlmTranslationProgress:
    """Calculate supported missing localization languages from a live catalog."""
    snippet = video_resource.get("snippet")
    default_language = (
        snippet.get("defaultLanguage") if isinstance(snippet, Mapping) else None
    )
    default_code = (
        default_language.casefold() if isinstance(default_language, str) else None
    )

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


def _video_source(video_resource: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract only the default video's source metadata for translation."""
    snippet = video_resource.get("snippet")
    if not isinstance(snippet, Mapping):
        snippet = {}
    return {
        "defaultLanguage": snippet.get("defaultLanguage"),
        "title": snippet.get("title"),
        "description": snippet.get("description"),
    }


def build_llm_translation_package(
    video_resource: Mapping[str, Any], languages: Sequence[YouTubeLanguage]
) -> Dict[str, Any]:
    """Build the default-source-only package for an external LLM."""
    return {
        "source": _video_source(video_resource),
        "targetLanguages": [
            {"code": language.code, "name": language.name} for language in languages
        ],
        "expectedLanguageCodes": [language.code for language in languages],
        "expectedCount": len(languages),
    }


def build_llm_translation_prompt(package: Mapping[str, Any]) -> str:
    """Build strict instructions for one downloadable localization JSON file."""
    package_json = json.dumps(package, ensure_ascii=False, indent=2)
    return """Translate the default source metadata in this package into every exact target code.

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
    try:
        document = json.loads(raw_json)
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

    parsed = validate_localizations(document, expected_language_codes)
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
