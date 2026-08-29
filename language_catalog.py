"""Validated language catalogs for YouTube application and video metadata flows."""

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple


APPLICATION_LANGUAGE_CATALOG_SOURCE = "YouTube Data API v3 i18nLanguages.list"
METADATA_LANGUAGE_CATALOG_SCOPE = "YouTube video metadata localizations"
METADATA_LANGUAGE_CATALOG_SOURCE = "YouTube Studio metadata language picker"
METADATA_LANGUAGE_CATALOG_PATH = (
    Path(__file__).resolve().parent / "data" / "youtube-metadata-languages.json"
)

# Keep the old name available for callers that only consume the application catalog.
LANGUAGE_CATALOG_SOURCE = APPLICATION_LANGUAGE_CATALOG_SOURCE
_BCP47_CODE_RE = re.compile(r"^[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*$")


class LanguageCatalogError(ValueError):
    """Raised when a language catalog is missing or unusable."""


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
    scope: str = "application"
    reviewed_at: Optional[str] = None

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
        source=APPLICATION_LANGUAGE_CATALOG_SOURCE,
        fetched_at=fetched_at or utc_timestamp(),
        hl=_required_string(hl, "hl", -1),
        languages=tuple(languages),
        scope="application",
    )


def _metadata_required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LanguageCatalogError(
            "Metadata language catalog is missing {}".format(field)
        )
    return value.strip()


def build_metadata_language_catalog(
    document: Mapping[str, Any],
) -> YouTubeLanguageCatalog:
    """Validate and normalize the checked-in video metadata language snapshot."""
    if not isinstance(document, Mapping):
        raise LanguageCatalogError("Metadata language catalog must be an object")

    scope = _metadata_required_string(document.get("scope"), "scope")
    source = _metadata_required_string(document.get("source"), "source")
    reviewed_at = _metadata_required_string(document.get("reviewedAt"), "reviewedAt")
    count = document.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 1:
        raise LanguageCatalogError(
            "Metadata language catalog count must be a positive integer"
        )

    items = document.get("languages")
    if not isinstance(items, list):
        raise LanguageCatalogError("Metadata language catalog is missing languages")
    if count != len(items):
        raise LanguageCatalogError(
            "Metadata language catalog count {} does not match {} entries".format(
                count, len(items)
            )
        )

    languages = []
    seen_codes = set()
    for item_index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise LanguageCatalogError(
                "Metadata language catalog item {} must be an object".format(item_index)
            )
        code = _metadata_required_string(
            item.get("code"), "languages[{}].code".format(item_index)
        )
        name = _metadata_required_string(
            item.get("name"), "languages[{}].name".format(item_index)
        )
        if not _BCP47_CODE_RE.fullmatch(code):
            raise LanguageCatalogError(
                "Invalid BCP-47 language code in metadata catalog: {}".format(code)
            )
        normalized_code = code.casefold()
        if normalized_code in seen_codes:
            raise LanguageCatalogError(
                "Duplicate language code in metadata catalog: {}".format(code)
            )
        seen_codes.add(normalized_code)
        languages.append(YouTubeLanguage(code, code, name))

    languages.sort(
        key=lambda language: (language.name.casefold(), language.code.casefold())
    )
    return YouTubeLanguageCatalog(
        source=source,
        fetched_at=reviewed_at,
        hl="",
        languages=tuple(languages),
        scope=scope,
        reviewed_at=reviewed_at,
    )


def load_metadata_language_catalog(
    path: Optional[Path] = None,
) -> YouTubeLanguageCatalog:
    """Load the checked-in metadata catalog without making a network request."""
    snapshot_path = Path(path) if path is not None else METADATA_LANGUAGE_CATALOG_PATH
    try:
        with snapshot_path.open("r", encoding="utf-8") as snapshot_file:
            document = json.load(snapshot_file)
    except (OSError, json.JSONDecodeError) as error:
        raise LanguageCatalogError(
            "Unable to load metadata language catalog from {}: {}".format(
                snapshot_path, error
            )
        ) from error
    return build_metadata_language_catalog(document)
