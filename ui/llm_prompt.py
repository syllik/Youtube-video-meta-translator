"""Supporting page for selecting LLM targets and copying a prompt."""

import html
from typing import Any, Mapping, MutableMapping, Tuple

from llm_localization_package import (
    LLM_BATCH_SIZE,
    build_llm_translation_package,
    build_llm_translation_prompt,
    build_selected_llm_languages,
    calculate_llm_translation_progress,
    select_next_llm_languages,
)
from state.llm_state import set_llm_prompt, set_llm_selected_codes


FREE_WEB_LLMS: Tuple[Tuple[str, str], ...] = (
    ("ChatGPT", "https://chatgpt.com/"),
    ("Google Gemini", "https://gemini.google.com/"),
    ("Claude", "https://claude.ai/"),
    ("Microsoft Copilot", "https://copilot.microsoft.com/"),
    ("Perplexity", "https://www.perplexity.ai/"),
    ("Mistral", "https://chat.mistral.ai/"),
)


def _render_free_web_llms() -> None:
    import streamlit as st

    links = " ".join(
        '<a href="{}" target="_blank" rel="noopener noreferrer">{}</a>'.format(
            html.escape(url, quote=True), html.escape(label)
        )
        for label, url in FREE_WEB_LLMS
    )
    st.markdown("**Free web LLMs**<br>{}".format(links), unsafe_allow_html=True)
    st.caption(
        "Free-tier availability depends on account, region, and provider limits."
    )


def _default_target_codes(state: Mapping[str, Any], progress) -> Tuple[str, ...]:
    available = {language.code.casefold(): language.code for language in progress.missing}
    stored = tuple(state.get("selected_target_codes") or ())
    if state.get("selected_target_codes_initialized") or stored:
        return tuple(
            available[code.strip().casefold()]
            for code in stored
            if isinstance(code, str) and code.strip().casefold() in available
        )
    return tuple(language.code for language in select_next_llm_languages(progress))


def render_llm_prompt_page(
    state: MutableMapping[str, Any],
    video_resource: Mapping[str, Any],
    catalog,
) -> None:
    """Render missing-language selection, prompt copy, and web-LLM links."""
    import streamlit as st

    video_id = state.get("selected_video_id") or video_resource.get("id")
    if not video_id:
        st.page_link(
            "pages/2_LLM_translate.py",
            label="Select a video on LLM translate",
        )
        _render_free_web_llms()
        return

    progress = calculate_llm_translation_progress(video_resource, catalog)
    st.caption(
        "YouTube translations: {} / {}".format(progress.current, progress.total)
    )
    if not progress.missing:
        st.success("All supported YouTube localizations are complete.")
        _render_free_web_llms()
        return

    labels_by_code = {
        language.code: "{} ({})".format(language.name, language.code)
        for language in progress.missing
    }
    options = tuple(labels_by_code)
    default_codes = _default_target_codes(state, progress)
    selected_codes = tuple(
        st.multiselect(
            "Target languages",
            options,
            default=default_codes,
            max_selections=LLM_BATCH_SIZE,
            format_func=lambda code: labels_by_code[code],
            key="llm-prompt-targets-{}".format(video_id),
        )
    )

    try:
        selected_languages = build_selected_llm_languages(
            progress, selected_codes, max_count=LLM_BATCH_SIZE
        )
    except ValueError as error:
        st.error(str(error))
        _render_free_web_llms()
        return

    canonical_codes = tuple(language.code for language in selected_languages)
    set_llm_selected_codes(state, video_id, canonical_codes)
    if not selected_languages:
        set_llm_prompt(state, video_id, (), "")
        st.info("Select at least one target language to build a prompt.")
        _render_free_web_llms()
        return

    package = build_llm_translation_package(video_resource, selected_languages)
    prompt = build_llm_translation_prompt(package)
    set_llm_prompt(state, video_id, canonical_codes, prompt)

    st.code(prompt, language="text")

    _render_free_web_llms()
