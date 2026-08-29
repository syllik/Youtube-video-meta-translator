"""Presentation-only formatting for exact YouTube language codes."""

from typing import Any, Mapping


def _english_names(catalog: Any) -> Mapping[str, str]:
    return {
        language.code.casefold(): language.english_name
        for language in getattr(catalog, "languages", ())
        if isinstance(getattr(language, "code", None), str)
        and isinstance(getattr(language, "english_name", None), str)
        and language.english_name.strip()
    }


def format_language_label(code: str, catalog: Any = None) -> str:
    """Format one exact BCP-47 code with its checked-in English name."""
    if not isinstance(code, str):
        return str(code)
    english_name = _english_names(catalog).get(code.casefold())
    if not english_name:
        return code
    return "{} — {}".format(code, english_name)
