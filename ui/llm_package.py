"""Streamlit controls for Codex generation and external-LLM JSON handoff."""

import hashlib
from contextlib import nullcontext
from typing import Any, MutableMapping, Sequence

from codex_localization_generator import (
    CodexGenerationError,
    generate_missing_localizations,
)
from codex_localization_runner import CodexLocalizationError, check_codex_login
from llm_localization_package import (
    calculate_llm_translation_progress,
    parse_llm_upload_json,
)
from localizations import (
    LocalizationIssue,
    ParsedLocalizations,
    validate_localizations,
)
from language_labels import format_language_label
from state.translation_state import merge_translation_draft
from ui.badges import render_language_badges


def apply_llm_upload(
    state: MutableMapping[str, Any],
    file_content: bytes,
    expected_language_codes: Sequence[str],
) -> ParsedLocalizations:
    """Validate an uploaded UTF-8 batch and merge it into the translation draft."""
    try:
        raw_json = file_content.decode("utf-8")
    except UnicodeDecodeError:
        return ParsedLocalizations(
            entries={},
            issues=(LocalizationIssue(None, "Upload must be valid UTF-8 JSON."),),
        )

    parsed = parse_llm_upload_json(raw_json, expected_language_codes)
    if not parsed.is_valid:
        return parsed

    merge_translation_draft(
        state,
        {
            language_code: value.to_dict()
            for language_code, value in parsed.entries.items()
        },
    )
    return parsed


def apply_generated_localizations(
    state: MutableMapping[str, Any], document, supported_language_codes
) -> ParsedLocalizations:
    """Validate generated localizations and merge them into the translation draft."""
    parsed = validate_localizations(document, supported_language_codes)
    if not parsed.is_valid:
        return parsed
    merge_translation_draft(
        state,
        {
            language_code: value.to_dict()
            for language_code, value in parsed.entries.items()
        },
    )
    return parsed


def _render_issues(issues) -> None:
    import streamlit as st

    for issue in issues:
        st.error("{}: {}".format(issue.path or "document", issue.message))


def _operation_spinner(st, message: str):
    spinner = getattr(st, "spinner", None)
    return spinner(message) if spinner is not None else nullcontext()


def _upload_context(video_resource, target_codes, file_content: bytes):
    return (
        video_resource["id"],
        tuple(target_codes),
        hashlib.sha256(file_content).hexdigest(),
    )


def render_llm_translation_controls(
    state: MutableMapping[str, Any],
    video_resource,
    catalog,
    widget_prefix: str = "llm",
    *,
    login_checker=check_codex_login,
    generate_localizations=generate_missing_localizations,
    prompt_state: MutableMapping[str, Any] = None,
    source_codes: Sequence[str] = (),
) -> None:
    """Show generation, prompt handoff, and upload controls for one translation state."""
    import streamlit as st
    import streamlit.components.v1 as components

    prompt_state = prompt_state if prompt_state is not None else state

    st.markdown('<div id="translate-form"></div>', unsafe_allow_html=True)
    if state.get("scroll_to_form"):
        components.html(
            '<script>window.parent.document.getElementById('
            '"translate-form").scrollIntoView({behavior: "smooth"});'
            "</script>",
            height=0,
        )
        state["scroll_to_form"] = False

    progress = calculate_llm_translation_progress(
        video_resource, catalog, excluded_source_codes=source_codes
    )
    st.caption(
        "YouTube translations: {} / {}".format(progress.current, progress.total)
    )
    if not progress.missing:
        st.success("All metadata localizations are complete.")
        return

    st.page_link("pages/2_LLM_prompt.py", label="LLM Translation prompt")
    st.markdown("**Codex**")
    if st.button(
        "Generate missing translations",
        key="llm-generate-missing-{}".format(video_resource["id"]),
        type="primary",
        disabled=state.get("operation_status") not in (None, "idle"),
    ):
        state["operation_status"] = "generating"
        try:
            with _operation_spinner(st, "Generating translations..."):
                login_checker()
                progress_placeholder = st.empty()

                def on_batch(index, total, codes):
                    progress_placeholder.info(
                        "Generating batch {} / {} — {}".format(
                            index,
                            total,
                            ", ".join(
                                format_language_label(code, catalog) for code in codes
                            ),
                        )
                    )

                generation_kwargs = {"on_batch": on_batch}
                if source_codes:
                    generation_kwargs["selected_source_codes"] = source_codes
                generated_document = generate_localizations(
                    video_resource, catalog, **generation_kwargs
                )
        except (CodexLocalizationError, CodexGenerationError) as error:
            state["operation_status"] = "idle"
            st.error(str(error))
            return
        except Exception as error:
            state["operation_status"] = "idle"
            st.error("Automatic translation generation failed: {}".format(error))
            return
        state["operation_status"] = "idle"

        if not generated_document:
            st.success("All metadata localizations are complete.")
            return

        parsed_generation = apply_generated_localizations(
            state, generated_document, catalog.codes
        )
        if not parsed_generation.is_valid:
            _render_issues(parsed_generation.issues)
            return
        st.rerun()
        return

    st.markdown("**External LLM**")
    st.markdown(
        "1. Prepare prompt\n"
        "2. Generate JSON in an external LLM\n"
        "3. Upload JSON"
    )

    prompt_video_id = prompt_state.get("prompt_video_id")
    target_codes = prompt_state.get("prompt_target_codes", ())
    prompt = prompt_state.get("prompt_text", "")
    upload_ready = bool(
        prompt_video_id == video_resource.get("id") and target_codes and prompt
    )

    if not upload_ready:
        st.caption(
            "Prepare a prompt first so the upload can be bound to this video "
            "and target-language set."
        )

    if upload_ready:
        render_language_badges(
            target_codes,
            label="Selected languages",
            catalog=catalog,
        )
        st.code(
            '{\n  "de": {\n    "title": "Translated title",\n    "description": "Translated description"\n  }\n}',
            language="json",
        )

    uploaded_file = st.file_uploader(
        "Upload JSON file",
        type=["json"],
        key="llm-localizations-upload-{}".format(video_resource["id"]),
        disabled=not upload_ready,
        help=(
            "Prepare a prompt first so the upload can be bound to this video "
            "and target-language set."
        ),
    )
    if not upload_ready or uploaded_file is None:
        return

    file_content = uploaded_file.getvalue()
    upload_context = _upload_context(video_resource, target_codes, file_content)
    if prompt_state.get("consumed_upload_context") == upload_context:
        return
    if prompt_state.get("upload_issue_context") == upload_context:
        _render_issues(prompt_state.get("upload_issues", ()))
        return

    parsed = apply_llm_upload(state, file_content, target_codes)
    if not parsed.is_valid:
        prompt_state["upload_issue_context"] = upload_context
        prompt_state["upload_issues"] = parsed.issues
        _render_issues(parsed.issues)
        return

    prompt_state["consumed_upload_context"] = upload_context
    prompt_state["upload_issue_context"] = None
    prompt_state["upload_issues"] = ()
    st.rerun()
