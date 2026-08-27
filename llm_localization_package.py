"""Pure input, prompt, schema, and response helpers for LLM translations."""

import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Sequence, Tuple

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog
from localizations import (
    MAX_DESCRIPTION_LENGTH,
    MAX_TITLE_LENGTH,
    validate_localizations,
)


LLM_BATCH_SIZE = 10


@dataclass(frozen=True)
class LlmTranslationProgress:
    current: int
    total: int
    missing: Tuple[YouTubeLanguage, ...]

    @property
    def missing_count(self) -> int:
        return len(self.missing)


class LlmResponseError(ValueError):
    """Raised when an LLM response is not a complete YouTube localization map."""


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

    catalog_languages = tuple(catalog.languages)
    supported_languages = tuple(
        language
        for language in catalog_languages
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


def _required_source_string(value: Any, path: str, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise LlmResponseError("{} must be a string".format(path))
    return value


def _video_source(video_resource: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(video_resource, Mapping):
        raise LlmResponseError("YouTube video resource must be an object")
    snippet = video_resource.get("snippet")
    if not isinstance(snippet, Mapping):
        raise LlmResponseError("YouTube video resource is missing snippet")
    return {
        "videoId": _required_source_string(video_resource.get("id"), "id"),
        "title": _required_source_string(snippet.get("title"), "snippet.title"),
        "description": _required_source_string(
            snippet.get("description"), "snippet.description", allow_empty=True
        ),
        "defaultLanguage": snippet.get("defaultLanguage"),
    }


def _existing_localizations(video_resource: Mapping[str, Any]) -> Dict[str, Dict[str, str]]:
    raw_localizations = video_resource.get("localizations") or {}
    if not isinstance(raw_localizations, Mapping):
        raise LlmResponseError("YouTube video resource localizations must be an object")

    existing = {}
    for language_code, value in raw_localizations.items():
        if not isinstance(language_code, str) or not isinstance(value, Mapping):
            continue
        title = value.get("title")
        description = value.get("description")
        if isinstance(title, str) and isinstance(description, str):
            existing[language_code] = {
                "title": title,
                "description": description,
            }
    return existing


def build_llm_translation_package(
    video_resource: Mapping[str, Any],
    catalog: YouTubeLanguageCatalog,
    languages: Sequence[YouTubeLanguage] = None,
) -> Dict[str, Any]:
    """Build the internal request context for one live-catalog language batch."""
    selected_languages = tuple(languages if languages is not None else catalog.languages)
    return {
        "source": _video_source(video_resource),
        "existingLocalizations": _existing_localizations(video_resource),
        "languages": [
            {"id": language.id, "code": language.code, "name": language.name}
            for language in selected_languages
        ],
    }


def split_languages_into_batches(
    languages: Sequence[YouTubeLanguage], batch_size: int = LLM_BATCH_SIZE
) -> Tuple[Tuple[YouTubeLanguage, ...], ...]:
    """Split the live catalog into deterministic, bounded translation batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    languages = tuple(languages)
    return tuple(
        languages[index : index + batch_size]
        for index in range(0, len(languages), batch_size)
    )


def build_llm_translation_prompt(package: Mapping[str, Any]) -> str:
    """Return the instruction used for one direct YouTube localization batch."""
    del package
    return """Translate the selected YouTube video's metadata for every language in the input JSON.

Use source.title and source.description as the primary source. Use
source.defaultLanguage when it is available. Existing entries in
existingLocalizations are context only: keep useful terminology and style
consistent, but translate the current source meaning accurately.

Output rules:
1. Return one JSON object keyed directly by the exact language codes from the
   input languages list.
2. Do not return a wrapper such as {"languages": ...}, {"catalog": ...}, or
   {"localizations": ...}.
3. Use every requested language code exactly once. Do not invent, rename,
   normalize, or omit a code.
4. Every language value must contain exactly the string fields title and
   description.
5. Translate by meaning, preserving tone, proper names, URLs, hashtags,
   product names, technical tokens, and meaningful line breaks.
6. Keep each title at or below 100 characters and each description at or below
   5000 characters.
7. Return valid JSON only, without Markdown fences, comments, or explanations.

Before returning, compare the output key set with the requested languages list
and correct all missing or extra keys."""


def build_llm_output_schema(language_codes: Sequence[str]) -> Dict[str, Any]:
    """Build a strict JSON Schema whose root keys are the current batch codes."""
    codes = tuple(language_codes)
    if not codes or len(set(codes)) != len(codes):
        raise ValueError("language_codes must be a non-empty sequence of unique codes")
    value_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": MAX_TITLE_LENGTH,
            },
            "description": {
                "type": "string",
                "maxLength": MAX_DESCRIPTION_LENGTH,
            },
        },
        "required": ["title", "description"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {code: value_schema for code in codes},
        "required": list(codes),
        "additionalProperties": False,
    }


def parse_llm_translation_output(
    raw_output: str, expected_language_codes: Sequence[str]
) -> Dict[str, Dict[str, str]]:
    """Parse and strictly validate one structured-output batch."""
    codes = tuple(expected_language_codes)
    try:
        document = json.loads(raw_output)
    except (TypeError, json.JSONDecodeError) as error:
        raise LlmResponseError("LLM returned invalid JSON") from error

    if not isinstance(document, dict):
        raise LlmResponseError("LLM output must be a JSON object")

    expected = set(codes)
    actual = set(document)
    missing = expected - actual
    extra = actual - expected
    if missing or extra:
        message = "LLM output keys do not match the requested batch"
        if missing:
            message += "; missing: {}".format(", ".join(sorted(missing)))
        if extra:
            message += "; extra: {}".format(", ".join(sorted(extra)))
        raise LlmResponseError(message)

    parsed = validate_localizations(document, codes)
    if parsed.issues:
        raise LlmResponseError(parsed.issues[0].message)
    return {
        code: parsed.entries[code].to_dict()
        for code in codes
    }


def serialize_localization_map(localizations: Mapping[str, Any]) -> str:
    """Serialize the direct YouTube localization map with readable Unicode."""
    return json.dumps(localizations, ensure_ascii=False, indent=2)
