"""Shared source-language selection for Translate and the prompt page."""

from typing import Any, Mapping, MutableMapping, Tuple

from llm_localization_package import build_translation_source_candidates
from language_labels import format_language_label
from state.common_state import set_source_selection, sync_source_selection


def source_label(source: Mapping[str, Any], catalog) -> str:
    return format_language_label(source["languageCode"], catalog)


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
            "Primary source: {}".format(source_label(candidates[0], catalog))
        )
        reference_candidates = candidates[1:]
        if not reference_candidates:
            st.info("No reference translations available.")
            return set_source_selection(
                session_state, video_id, (default_code,), default_code, codes
            )

        reference_codes = tuple(
            source["languageCode"] for source in reference_candidates
        )
        labels_by_code = {
            source["languageCode"]: source_label(source, catalog)
            for source in reference_candidates
        }
        widget_key = "common-source-languages-{}".format(video_id)
        selected_references = tuple(
            code
            for code in current
            if code.casefold() != default_code.casefold()
        )

        def restore_primary_source() -> None:
            values = st.session_state.get(widget_key, ())
            normalized = set_source_selection(
                session_state,
                video_id,
                (default_code, *values),
                default_code,
                codes,
            )
            st.session_state[widget_key] = [
                code
                for code in normalized
                if code.casefold() != default_code.casefold()
            ]

        with st.expander("Optional reference translations", expanded=False):
            selected = tuple(
                st.multiselect(
                    "Optional reference translations",
                    reference_codes,
                    default=selected_references,
                    format_func=lambda code: labels_by_code[code],
                    key=widget_key,
                    on_change=restore_primary_source,
                )
            )
        return set_source_selection(
            session_state,
            video_id,
            (default_code, *selected),
            default_code,
            codes,
        )
