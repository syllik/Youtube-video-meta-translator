"""Pure progress and target-selection helpers for LLM translations."""

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

from language_catalog import YouTubeLanguage, YouTubeLanguageCatalog


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
