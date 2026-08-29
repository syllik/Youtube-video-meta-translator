"""Supporting page for selecting LLM targets and copying a source-aware prompt."""

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


def _render_return_link() -> None:
    import streamlit as st

    st.page_link("pages/1_Translate.py", label="Return to Translate")


def render_source_quality_guide() -> None:
    """Render the short, non-technical source-language quality guidance."""
    import streamlit as st

    with st.expander("Source-language quality guide", expanded=True):
        st.markdown(
            "Translation uses the default source as the authoritative meaning. "
            "One source can miss nuance, so use at least 2 source languages when "
            "possible. 2–3 strong translations are a good target; "
            "around 2–5 translations from different language families can give "
            "the LLM useful context without replacing the default source."
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
    source_codes=(),
) -> None:
    """Render missing-language selection, prompt copy, and web-LLM links."""
    import streamlit as st

    video_id = state.get("bound_video_id") or video_resource.get("id")
    if not video_id:
        _render_return_link()
        _render_free_web_llms()
        return

    progress = calculate_llm_translation_progress(
        video_resource, catalog, excluded_source_codes=source_codes
    )
    st.caption(
        "YouTube translations: {} / {}".format(progress.current, progress.total)
    )
    if not progress.missing:
        st.success("All supported YouTube localizations are complete.")
        _render_return_link()
        _render_free_web_llms()
        return

    with st.expander("Target languages", expanded=True):
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
        _render_return_link()
        _render_free_web_llms()
        return

    package = build_llm_translation_package(
        video_resource,
        selected_languages,
        selected_source_codes=source_codes,
        catalog=catalog,
    )
    prompt = build_llm_translation_prompt(package)
    set_llm_prompt(state, video_id, canonical_codes, prompt)

    with st.expander("Prepared prompt", expanded=True):
        st.code(prompt, language="text")

    with st.expander("External LLM options", expanded=False):
        _render_return_link()
        _render_free_web_llms()
