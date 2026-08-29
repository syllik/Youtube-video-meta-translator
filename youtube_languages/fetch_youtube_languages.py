"""Fetch the current YouTube application-language catalog and save it as JSON."""

from __future__ import annotations

import json
import locale
import os
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

import requests
from dotenv import load_dotenv


API_URL = "https://www.googleapis.com/youtube/v3/i18nLanguages"
API_HL = "ru"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = PROJECT_ROOT / "data" / "youtube-languages.json"
SOURCE_NAME = "YouTube Data API v3 i18nLanguages.list"


class YouTubeLanguageSnippet(TypedDict):
    hl: str
    name: str


class YouTubeLanguageItem(TypedDict):
    id: str
    snippet: YouTubeLanguageSnippet


class YouTubeLanguagesResponse(TypedDict):
    items: list[YouTubeLanguageItem]


class LanguageEntry(TypedDict):
    code: str
    name: str
    id: str


class LanguagesDocument(TypedDict):
    source: str
    fetchedAt: str
    hl: str
    count: int
    languages: list[LanguageEntry]


class YouTubeLanguagesError(RuntimeError):
    """Raised when the YouTube application/UI catalog cannot be fetched."""


HttpGet = Callable[..., Any]


def _redact_api_key(message: str, api_key: str) -> str:
    if api_key:
        return message.replace(api_key, "[REDACTED]")
    return message


def _safe_google_error_message(response: Any, api_key: str) -> str:
    try:
        payload = response.json()
    except (TypeError, ValueError):
        payload = None

    message = ""
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping) and isinstance(error.get("message"), str):
            message = error["message"]

    if not message:
        text = getattr(response, "text", "")
        message = text.strip() if isinstance(text, str) else ""

    if not message:
        message = "Google API returned an error without a message."

    return _redact_api_key(message[:500], api_key)


def fetch_languages(api_key: str, http_get: HttpGet = requests.get) -> Mapping[str, Any]:
    """Fetch the raw response from the official i18nLanguages.list endpoint."""
    try:
        response = http_get(
            API_URL,
            params={"part": "snippet", "hl": API_HL, "key": api_key},
            timeout=30,
        )
    except requests.RequestException as error:
        message = _redact_api_key(str(error), api_key)
        raise YouTubeLanguagesError(
            "Network error while requesting YouTube API: {}".format(message)
        ) from None

    status_code = getattr(response, "status_code", None)
    if not isinstance(status_code, int) or not 200 <= status_code < 300:
        raise YouTubeLanguagesError(
            "YouTube API returned HTTP {}: {}".format(
                status_code if status_code is not None else "unknown",
                _safe_google_error_message(response, api_key),
            )
        )

    try:
        payload = response.json()
    except (TypeError, ValueError):
        raise YouTubeLanguagesError(
            "YouTube API returned malformed JSON."
        ) from None

    if not isinstance(payload, Mapping):
        raise YouTubeLanguagesError("YouTube API returned an invalid JSON object.")

    return payload


def _sort_by_russian_locale(languages: list[LanguageEntry]) -> None:
    """Sort in-place using the closest available Russian system locale."""
    previous_locale = locale.setlocale(locale.LC_COLLATE)
    russian_locale = None
    for candidate in ("ru_RU.UTF-8", "ru_RU.utf8", "Russian_Russia.1251"):
        try:
            locale.setlocale(locale.LC_COLLATE, candidate)
            russian_locale = candidate
            break
        except locale.Error:
            continue

    try:
        if russian_locale is None:
            raise locale.Error("Russian locale is not installed")
        languages.sort(key=lambda language: locale.strxfrm(language["name"]))
    finally:
        locale.setlocale(locale.LC_COLLATE, previous_locale)


def build_output(response: Mapping[str, Any], fetched_at: str) -> LanguagesDocument:
    """Convert a YouTube API response into the persisted catalog format."""
    items = response.get("items")
    if not isinstance(items, list):
        raise ValueError("YouTube API response must contain an items array")

    languages: list[LanguageEntry] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise ValueError("YouTube API language item {} is malformed".format(index))

        snippet = item.get("snippet")
        code = snippet.get("hl") if isinstance(snippet, Mapping) else None
        name = snippet.get("name") if isinstance(snippet, Mapping) else None
        item_id = item.get("id")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (code, name, item_id)
        ):
            raise ValueError("YouTube API language item {} is malformed".format(index))

        languages.append({"code": code, "name": name, "id": item_id})

    _sort_by_russian_locale(languages)
    return {
        "source": SOURCE_NAME,
        "fetchedAt": fetched_at,
        "hl": API_HL,
        "count": len(languages),
        "languages": languages,
    }


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def save_output(document: LanguagesDocument, output_path: Path = OUTPUT_PATH) -> None:
    """Write the catalog as readable UTF-8 JSON without escaping Unicode."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_and_save(
    api_key: str,
    output_path: Path = OUTPUT_PATH,
    http_get: HttpGet = requests.get,
) -> LanguagesDocument:
    """Fetch, validate, transform, and save the application/UI catalog."""
    response = fetch_languages(api_key, http_get=http_get)
    document = build_output(response, _utc_timestamp())
    save_output(document, output_path=output_path)
    return document


def _display_path(output_path: Path) -> str:
    try:
        return str(output_path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(output_path)


def main(
    *,
    environ: Mapping[str, str] | None = None,
    output_path: Path = OUTPUT_PATH,
    http_get: HttpGet = requests.get,
    load_environment: bool = True,
) -> int:
    """Run the CLI and return a process exit code."""
    if load_environment:
        load_dotenv()

    environment = os.environ if environ is None else environ
    api_key = environment.get("YOUTUBE_API_KEY", "").strip()
    if not api_key:
        print(
            "Error: YOUTUBE_API_KEY is not set. Add it to the environment or .env.",
            file=sys.stderr,
        )
        return 1

    try:
        document = fetch_and_save(
            api_key,
            output_path=output_path,
            http_get=http_get,
        )
    except (OSError, ValueError, YouTubeLanguagesError) as error:
        print("Error: {}".format(_redact_api_key(str(error), api_key)), file=sys.stderr)
        return 1

    print(
        "Fetched {} YouTube languages -> {}".format(
            document["count"], _display_path(output_path)
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
