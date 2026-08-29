"""Target-language selection for the primary Translate workflow."""

from typing import Any, Mapping, MutableMapping, Sequence, Tuple

from language_labels import format_language_label
from llm_localization_package import calculate_llm_translation_progress
from state.translation_state import (
    set_translation_target_selection,
    sync_translation_target_selection,
)


def render_target_selection(
    session_state: MutableMapping[str, Any],
    video_resource: Mapping[str, Any],
    catalog,
    source_codes: Sequence[str] = (),
) -> Tuple[str, ...]:
    """Render the uncapped primary Translate target selector."""
    import streamlit as st

    video_id = video_resource.get("id")
    progress = calculate_llm_translation_progress(
        video_resource, catalog, excluded_source_codes=source_codes
    )
    current = sync_translation_target_selection(
        session_state.setdefault("translation", {}), video_id, progress
    )
    options = tuple(language.code for language in progress.missing)
    labels_by_code = {
        language.code: format_language_label(language.code, catalog)
        for language in progress.missing
    }

    with st.expander("Target languages", expanded=bool(options)):
        if not options:
            st.info("No missing target languages are available for this video.")
            return ()
        source_key = ",".join(source_codes) or "default"
        widget_key = "translate-target-languages-{}-{}".format(
            video_id, source_key
        )
        selected = tuple(
            st.multiselect(
                "Target languages",
                options,
                default=current,
                format_func=lambda code: labels_by_code[code],
                key=widget_key,
            )
        )
        normalized = set_translation_target_selection(
            session_state["translation"], video_id, progress, selected
        )
        if not normalized:
            st.info("Select at least one target language to generate translations.")
        return normalized
