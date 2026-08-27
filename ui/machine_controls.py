"""Machine-only controls and their explicit state mapping."""

from typing import Any, Mapping, MutableMapping, Tuple

from services.machine_translation_service import MachineTranslationOptions
from state.machine_state import machine_can_submit


def render_machine_controls(
    state: MutableMapping[str, Any],
    language_options: Mapping[str, str],
    disabled: bool = False,
) -> Tuple[MachineTranslationOptions, bool]:
    import streamlit as st

    with st.container(border=True):
        st.subheader("Translation settings")
        code_options = list(language_options.keys())
        selected_codes = st.multiselect(
            "Target languages",
            code_options,
            default=[code for code in state.get("selected_language_codes", set()) if code in code_options],
            format_func=lambda code: "{} ({})".format(language_options[code], code),
            key="machine-language-select",
            disabled=disabled,
        )
        state["selected_language_codes"] = set(selected_codes)
        prefer_deepl = st.checkbox(
            "Prefer DeepL when available",
            value=bool(state.get("prefer_deepl")),
            key="machine-prefer-deepl",
            disabled=disabled,
        )
        overwrite = st.checkbox(
            "Overwrite existing localizations",
            value=bool(state.get("overwrite")),
            key="machine-overwrite",
            disabled=disabled,
        )
        trim = st.checkbox(
            "Trim text that exceeds YouTube limits",
            value=bool(state.get("trim")),
            key="machine-trim",
            disabled=disabled,
        )
        state.update(prefer_deepl=prefer_deepl, overwrite=overwrite, trim=trim)
        can_submit = machine_can_submit(state) and not disabled
        clicked = st.button(
            "Translate selected videos",
            type="primary",
            disabled=not can_submit,
            key="machine-submit",
        )
    return MachineTranslationOptions(prefer_deepl, overwrite, trim), clicked
