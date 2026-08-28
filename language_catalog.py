"""Validated, normalized representation of YouTube's live language catalog."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Mapping, Optional, Tuple


LANGUAGE_CATALOG_SOURCE = "YouTube Data API v3 i18nLanguages.list"


class LanguageCatalogError(ValueError):
    """Raised when YouTube returns an unusable language catalog."""


@dataclass(frozen=True)
class YouTubeLanguage:
    id: str
    code: str
    name: str


@dataclass(frozen=True)
class YouTubeLanguageCatalog:
    source: str
    fetched_at: str
    hl: str
    languages: Tuple[YouTubeLanguage, ...]

    @property
    def codes(self) -> Tuple[str, ...]:
        return tuple(language.code for language in self.languages)

    @property
    def code_to_name(self) -> Dict[str, str]:
        return {language.code: language.name for language in self.languages}


def utc_timestamp() -> str:
    """Return an ISO-8601 UTC timestamp with millisecond precision."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _required_string(value: Any, field: str, item_index: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LanguageCatalogError(
            "Language catalog item {} is missing {}".format(item_index, field)
        )
    return value.strip()


def build_language_catalog(
    response: Mapping[str, Any],
    hl: str = "ru",
    fetched_at: Optional[str] = None,
) -> YouTubeLanguageCatalog:
    """Convert one ``i18nLanguages.list`` response into a stable catalog."""
    if not isinstance(response, Mapping):
        raise LanguageCatalogError("Language catalog response must be an object")

    items = response.get("items")
    if not isinstance(items, list):
        raise LanguageCatalogError("Language catalog response is missing items")

    languages = []
    seen_codes = set()
    for item_index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise LanguageCatalogError(
                "Language catalog item {} must be an object".format(item_index)
            )
        item_id = _required_string(item.get("id"), "id", item_index)
        snippet = item.get("snippet")
        if not isinstance(snippet, Mapping):
            raise LanguageCatalogError(
                "Language catalog item {} is missing snippet".format(item_index)
            )
        code = _required_string(snippet.get("hl"), "snippet.hl", item_index)
        name = _required_string(snippet.get("name"), "snippet.name", item_index)
        normalized_code = code.casefold()
        if normalized_code in seen_codes:
            raise LanguageCatalogError(
                "Duplicate language code in catalog: {}".format(code)
            )
        seen_codes.add(normalized_code)
        languages.append(YouTubeLanguage(item_id, code, name))

    languages.sort(key=lambda language: (language.name.casefold(), language.code.casefold()))
    return YouTubeLanguageCatalog(
        source=LANGUAGE_CATALOG_SOURCE,
        fetched_at=fetched_at or utc_timestamp(),
        hl=_required_string(hl, "hl", -1),
        languages=tuple(languages),
    )
