"""Streamlit controls for Codex generation and external-LLM JSON handoff."""

import hashlib
import json
import math
from contextlib import nullcontext
from typing import Any, Mapping, MutableMapping, Sequence, Tuple

from codex_localization_generator import (
    CodexGenerationError,
    generate_missing_localizations,
)
from codex_localization_runner import CodexLocalizationError, check_codex_login
from llm_localization_package import (
    LLM_BATCH_SIZE,
    build_selected_llm_languages,
    calculate_llm_translation_progress,
    parse_localization_upload_json,
)
from localizations import (
    LocalizationIssue,
    ParsedLocalizations,
    validate_localizations,
)
from language_labels import format_language_label
from state.translation_state import merge_translation_draft


def apply_llm_upload(
    state: MutableMapping[str, Any],
    file_content: bytes,
    supported_language_codes: Sequence[str],
) -> ParsedLocalizations:
    """Validate an uploaded UTF-8 batch and merge it into the translation draft."""
    try:
        raw_json = file_content.decode("utf-8")
    except UnicodeDecodeError:
        return ParsedLocalizations(
            entries={},
            issues=(LocalizationIssue(None, "Upload must be valid UTF-8 JSON."),),
        )

    parsed = parse_localization_upload_json(raw_json, supported_language_codes)
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


def serialize_translation_draft(draft: Mapping[str, Any]) -> str:
    """Serialize the current internal draft as a direct readable JSON map."""
    document = draft if isinstance(draft, Mapping) else {}
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def remaining_translation_target_codes(
    selected_codes: Sequence[str],
    draft: Mapping[str, Any],
    supported_language_codes: Sequence[str],
) -> Tuple[str, ...]:
    """Return selected codes that do not already have valid draft entries."""
    parsed = validate_localizations(draft or {}, supported_language_codes)
    valid_codes = {code.casefold() for code in parsed.entries}
    return tuple(
        code
        for code in selected_codes
        if isinstance(code, str) and code.casefold() not in valid_codes
    )


def _batch_count(code_count: int) -> int:
    return int(math.ceil(code_count / float(LLM_BATCH_SIZE))) if code_count else 0


def _sync_generation_state(
    state: MutableMapping[str, Any],
    video_id: str,
    selected_codes: Sequence[str],
    draft: Mapping[str, Any],
    supported_language_codes: Sequence[str],
) -> Tuple[str, ...]:
    """Bind resumable generation metadata to one video and target selection."""
    selected_codes = tuple(selected_codes)
    remaining = remaining_translation_target_codes(
        selected_codes, draft, supported_language_codes
    )
    if (
        state.get("generation_video_id") != video_id
        or tuple(state.get("generation_target_codes") or ()) != selected_codes
    ):
        state["generation_video_id"] = video_id
        state["generation_target_codes"] = selected_codes
        state["generation_completed_codes"] = ()
        state["generation_completed_batch_count"] = 0
        state["generation_total_batches"] = _batch_count(len(remaining))
        state["generation_last_batch_codes"] = ()
        state["generation_error"] = None
    return remaining


def _record_generation_checkpoint(
    state: MutableMapping[str, Any], codes: Sequence[str]
) -> None:
    completed = list(state.get("generation_completed_codes") or ())
    completed_folds = {code.casefold() for code in completed}
    for code in codes:
        if code.casefold() not in completed_folds:
            completed.append(code)
            completed_folds.add(code.casefold())
    state["generation_completed_codes"] = tuple(completed)
    state["generation_completed_batch_count"] = (
        state.get("generation_completed_batch_count", 0) + 1
    )
    state["generation_last_batch_codes"] = tuple(codes)


def _render_issues(issues) -> None:
    import streamlit as st

    for issue in issues:
        st.error("{}: {}".format(issue.path or "document", issue.message))


def _operation_spinner(st, message: str):
    spinner = getattr(st, "spinner", None)
    return spinner(message) if spinner is not None else nullcontext()


def _request_rerun(st) -> None:
    rerun = getattr(st, "rerun", None)
    if callable(rerun):
        rerun()


def _upload_context(video_resource, file_content: bytes):
    return (
        video_resource["id"],
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
    target_codes: Sequence[str] = None,
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
    try:
        selected_languages = (
            progress.missing
            if target_codes is None
            else build_selected_llm_languages(
                progress, target_codes, max_count=None
            )
        )
    except ValueError as error:
        st.error(str(error))
        selected_languages = ()

    selected_codes = tuple(language.code for language in selected_languages)
    draft = state.get("draft") or {}
    remaining_codes = _sync_generation_state(
        state,
        video_resource["id"],
        selected_codes,
        draft,
        catalog.codes,
    )

    if state.get("generation_error"):
        st.warning(
            "Previous generation stopped: {}".format(state["generation_error"])
        )
    if not progress.missing:
        st.success("All metadata localizations are complete.")

    if progress.missing:
        st.page_link("pages/2_LLM_prompt.py", label="LLM Translation prompt")
    st.markdown("**Codex**")
    if selected_codes:
        if remaining_codes:
            st.caption(
                "Codex batches: {} / {} completed.".format(
                    state.get("generation_completed_batch_count", 0),
                    state.get("generation_total_batches", 0),
                )
            )
            st.caption(
                "Remaining selected targets: {}".format(
                    ", ".join(
                        format_language_label(code, catalog)
                        for code in remaining_codes
                    )
                )
            )
        else:
            st.success("All selected target languages are available in the draft.")
    else:
        st.info("Select at least one target language to generate translations.")

    generate_disabled = bool(
        not selected_codes
        or not remaining_codes
        or state.get("operation_status") not in (None, "idle")
    )
    generate_column, download_column = st.columns(2)
    with generate_column:
        generate_clicked = st.button(
            "Generate missing translations",
            key="llm-generate-missing-{}".format(video_resource["id"]),
            type="primary",
            disabled=generate_disabled,
        )
    with download_column:
        st.download_button(
            "Download JSON",
            data=serialize_translation_draft(state.get("draft") or {}),
            file_name="{}-localizations.json".format(video_resource["id"]),
            mime="application/json",
            key="llm-download-localizations-{}".format(video_resource["id"]),
            disabled=not bool(state.get("draft")),
            help="Download the current internal translation draft.",
        )

    if generate_clicked:
        state["operation_status"] = "generating"
        state["generation_error"] = None
        callback_called = []
        try:
            with _operation_spinner(st, "Generating translations..."):
                login_checker()
                progress_placeholder = st.empty()

                def on_batch(index, total, codes):
                    completed = state.get("generation_completed_batch_count", 0)
                    total_display = max(
                        state.get("generation_total_batches", 0),
                        completed + total,
                    )
                    progress_placeholder.info(
                        "Generating batch {} / {} — {}".format(
                            completed + index,
                            total_display,
                            ", ".join(
                                format_language_label(code, catalog) for code in codes
                            ),
                        )
                    )

                def on_batch_completed(
                    index, total, codes, batch_document, cumulative_document
                ):
                    merge_translation_draft(state, batch_document)
                    _record_generation_checkpoint(state, codes)
                    state["generation_error"] = None
                    callback_called.append(True)

                generation_kwargs = {
                    "on_batch": on_batch,
                    "on_batch_completed": on_batch_completed,
                    "target_codes": remaining_codes,
                    "batch_size": LLM_BATCH_SIZE,
                }
                if source_codes:
                    generation_kwargs["selected_source_codes"] = source_codes
                generated_document = generate_localizations(
                    video_resource, catalog, **generation_kwargs
                )
        except (CodexLocalizationError, CodexGenerationError) as error:
            state["operation_status"] = "idle"
            state["generation_error"] = str(error)
            st.error(str(error))
            _request_rerun(st)
            return
        except Exception as error:
            state["operation_status"] = "idle"
            state["generation_error"] = str(error)
            st.error("Automatic translation generation failed: {}".format(error))
            _request_rerun(st)
            return
        state["operation_status"] = "idle"

        if generated_document and not callback_called:
            parsed_generation = apply_generated_localizations(
                state, generated_document, catalog.codes
            )
            if not parsed_generation.is_valid:
                state["generation_error"] = "Generated localization output was invalid."
                _render_issues(parsed_generation.issues)
                _request_rerun(st)
                return
            _record_generation_checkpoint(state, remaining_codes)

        if generated_document or callback_called:
            _request_rerun(st)
        return

    st.markdown("**External LLM**")
    st.markdown(
        "1. (Optional) Prepare prompt\n"
        "2. Generate JSON in an external LLM\n"
        "3. Upload JSON"
    )

    upload_ready = bool(video_resource.get("id"))

    if not upload_ready:
        st.caption(
            "Select a video first so the upload can be applied to that video."
        )

    if upload_ready:
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
            "Select a video first so the uploaded localizations can be reviewed "
            "for that video."
        ),
    )
    if not upload_ready or uploaded_file is None:
        return

    file_content = uploaded_file.getvalue()
    upload_context = _upload_context(video_resource, file_content)
    if prompt_state.get("consumed_upload_context") == upload_context:
        return
    if prompt_state.get("upload_issue_context") == upload_context:
        _render_issues(prompt_state.get("upload_issues", ()))
        return

    parsed = apply_llm_upload(state, file_content, catalog.codes)
    if not parsed.is_valid:
        prompt_state["upload_issue_context"] = upload_context
        prompt_state["upload_issues"] = parsed.issues
        _render_issues(parsed.issues)
        return

    prompt_state["consumed_upload_context"] = upload_context
    prompt_state["upload_issue_context"] = None
    prompt_state["upload_issues"] = ()
    st.rerun()
