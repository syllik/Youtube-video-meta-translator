"""Shared source-language selection for Translate and the prompt page."""

from typing import Any, Mapping, MutableMapping, Tuple

from llm_localization_package import build_translation_source_candidates
from state.common_state import set_source_selection, sync_source_selection


def _language_names(catalog) -> Mapping[str, str]:
    return {
        language.code.casefold(): language.name
        for language in getattr(catalog, "languages", ())
    }


def source_label(source: Mapping[str, Any], catalog) -> str:
    code = source["languageCode"]
    name = _language_names(catalog).get(code.casefold(), code)
    return "{} ({})".format(name, code)


def render_source_selection(
    session_state: MutableMapping[str, Any],
    video_resource: Mapping[str, Any],
    catalog,
) -> Tuple[str, ...]:
    """Render the shared source selector and return normalized source codes."""
    import streamlit as st

    video_id = video_resource.get("id")
    candidates = build_translation_source_candidates(video_resource, catalog)
    codes = tuple(source["languageCode"] for source in candidates)
    default_code = codes[0] if codes else None
    current = sync_source_selection(
        session_state, video_id, default_code, codes
    )

    with st.expander("Source languages", expanded=bool(candidates)):
        if not candidates:
            st.error("The selected video has no usable default source metadata.")
            return ()

        st.caption(
            "Primary source: {}. Existing localizations are optional verified reference translations.".format(
                source_label(candidates[0], catalog)
            )
        )
        if len(candidates) == 1:
            st.info(
                "Using the default source automatically: {}.".format(
                    source_label(candidates[0], catalog)
                )
            )
            return current

        labels_by_code = {
            source["languageCode"]: source_label(source, catalog)
            for source in candidates
        }
        widget_key = "common-source-languages-{}".format(video_id)

        def restore_primary_source() -> None:
            values = st.session_state.get(widget_key, ())
            normalized = set_source_selection(
                session_state,
                video_id,
                values,
                default_code,
                codes,
            )
            st.session_state[widget_key] = list(normalized)

        selected = tuple(
            st.multiselect(
                "Source languages",
                codes,
                default=current,
                format_func=lambda code: labels_by_code[code],
                key=widget_key,
                on_change=restore_primary_source,
            )
        )
        return set_source_selection(
            session_state, video_id, selected, default_code, codes
        )
