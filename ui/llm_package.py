"""Streamlit controls for Codex generation and external-LLM JSON handoff."""

import hashlib
import json
import math
from contextlib import nullcontext
from typing import Any, Mapping, MutableMapping, Optional, Sequence, Tuple

from codex_localization_generator import (
    CodexLocalizationCancelled,
    CodexGenerationError,
    generate_missing_localizations,
)
from codex_localization_runner import CodexLocalizationError, check_codex_login
from generation_controller import (
    ACTIVE_GENERATION_STATUSES,
    DuplicateGenerationError,
    get_generation_controller,
)
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
        state["generation_job_id"] = None
        state["generation_status"] = "idle"
        state["generation_current_batch_index"] = 0
        state["generation_current_batch_total"] = 0
        state["generation_current_batch_codes"] = ()
        state["generation_committed_batch_keys"] = ()
    elif state.get("generation_status") not in ACTIVE_GENERATION_STATUSES:
        state["generation_total_batches"] = _batch_count(len(remaining))
    return remaining


def _record_generation_checkpoint(
    state: MutableMapping[str, Any],
    codes: Sequence[str],
    batch_key: Optional[Tuple[Any, ...]] = None,
) -> bool:
    if batch_key is not None:
        recorded_keys = tuple(state.get("generation_committed_batch_keys") or ())
        if batch_key in recorded_keys:
            return False
        state["generation_committed_batch_keys"] = recorded_keys + (batch_key,)
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
    return True


def _apply_generation_snapshot(state: MutableMapping[str, Any], snapshot) -> None:
    stop_pending = (
        state.get("generation_status") == "stopping"
        or getattr(snapshot, "stop_requested", False)
    )
    state["generation_status"] = (
        "stopping"
        if stop_pending and snapshot.status in ACTIVE_GENERATION_STATUSES
        else snapshot.status
    )
    state["generation_current_batch_index"] = snapshot.current_batch_index
    state["generation_current_batch_total"] = snapshot.total_batches
    state["generation_current_batch_codes"] = tuple(snapshot.current_batch_codes)
    state["generation_completed_codes"] = tuple(snapshot.completed_codes)
    if snapshot.total_batches:
        state["generation_total_batches"] = snapshot.total_batches
    if state["generation_status"] in ACTIVE_GENERATION_STATUSES:
        state["operation_status"] = state["generation_status"]
    else:
        state["operation_status"] = "idle"
        if snapshot.status == "failed":
            state["generation_error"] = snapshot.error


def _poll_generation(
    state: MutableMapping[str, Any],
    video_resource,
    catalog,
    controller,
):
    job_id = state.get("generation_job_id")
    owner_id = state.get("generation_owner_id")
    if not job_id or not owner_id:
        return None, ()

    snapshot, events = controller.poll(owner_id, job_id)
    if (
        snapshot is None
        or snapshot.job_id != job_id
        or snapshot.video_id != video_resource.get("id")
    ):
        return None, ()
    _apply_generation_snapshot(state, snapshot)
    for event in events:
        if event.job_id != job_id or event.video_id != video_resource.get("id"):
            continue
        if event.kind == "batch_completed":
            checkpoint_recorded = _record_generation_checkpoint(
                state,
                event.codes,
                batch_key=(event.job_id, event.index, event.total, event.codes),
            )
            if checkpoint_recorded:
                merge_translation_draft(state, event.batch_document or {})
        elif event.kind == "terminal":
            if snapshot.status == "failed":
                state["generation_error"] = event.error or snapshot.error
            elif snapshot.status == "stopped":
                state["generation_error"] = None
    return snapshot, events


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
    generation_controller=None,
) -> None:
    """Show cancellable Codex generation and external-LLM upload controls."""
    import streamlit as st
    import streamlit.components.v1 as components

    prompt_state = prompt_state if prompt_state is not None else state
    controller = generation_controller or get_generation_controller()
    async_mode = generation_controller is not None or (
        generate_localizations is generate_missing_localizations
    )

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

    def render_body() -> None:
        terminal_seen = False
        if async_mode:
            _snapshot, events = _poll_generation(
                state, video_resource, catalog, controller
            )
            terminal_seen = any(event.kind == "terminal" for event in events)

        remaining_codes = _sync_generation_state(
            state,
            video_resource["id"],
            selected_codes,
            state.get("draft") or {},
            catalog.codes,
        )
        status = state.get("generation_status", "idle")
        active = status in ACTIVE_GENERATION_STATUSES

        if terminal_seen:
            cleanup = getattr(controller, "cleanup", None)
            if callable(cleanup):
                cleanup(state.get("generation_owner_id"), state.get("generation_job_id"))
            _request_rerun(st)

        if status == "stopping":
            st.info("Stopping Codex generation...")
        elif status == "stopped":
            st.info("Generation stopped. Completed batches remain in the draft.")
        elif status == "failed" and state.get("generation_error"):
            st.warning("Previous generation failed: {}".format(state["generation_error"]))

        if not progress.missing:
            st.success("All metadata localizations are complete.")
        if progress.missing:
            st.page_link("pages/2_LLM_prompt.py", label="LLM Translation prompt")
        st.markdown("**Codex**")

        if status in {"starting", "generating"} and state.get(
            "generation_current_batch_index"
        ):
            index = state["generation_current_batch_index"]
            total = state.get("generation_current_batch_total") or state.get(
                "generation_total_batches", 0
            )
            codes = state.get("generation_current_batch_codes") or ()
            st.info(
                "Generating batch {} / {} — {}".format(
                    index,
                    total,
                    ", ".join(format_language_label(code, catalog) for code in codes),
                )
            )

        if selected_codes:
            if remaining_codes:
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
            not selected_codes or not remaining_codes or active
        )
        stop_disabled = not bool(status in {"starting", "generating"})
        generate_column, stop_column, download_column = st.columns(3)
        with generate_column:
            generate_clicked = st.button(
                "Generate missing translations",
                key="llm-generate-missing-{}".format(video_resource["id"]),
                type="primary",
                disabled=generate_disabled,
            )
        with stop_column:
            stop_clicked = st.button(
                "STOP",
                key="llm-stop-generation-{}".format(video_resource["id"]),
                disabled=stop_disabled,
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

        if stop_clicked:
            if controller.stop(state["generation_owner_id"], state.get("generation_job_id")):
                state["generation_status"] = "stopping"
                state["operation_status"] = "stopping"
            _request_rerun(st)
            return

        if generate_clicked:
            state["generation_error"] = None
            if async_mode:
                try:
                    snapshot = controller.start(
                        state["generation_owner_id"],
                        video_resource,
                        catalog,
                        remaining_codes,
                        source_codes,
                    )
                except DuplicateGenerationError as error:
                    state["generation_error"] = str(error)
                    st.error(str(error))
                    return
                state["generation_job_id"] = snapshot.job_id
                state["generation_video_id"] = snapshot.video_id
                state["generation_target_codes"] = tuple(selected_codes)
                state["generation_completed_codes"] = ()
                state["generation_completed_batch_count"] = 0
                state["generation_committed_batch_keys"] = ()
                state["generation_total_batches"] = _batch_count(len(remaining_codes))
                _apply_generation_snapshot(state, snapshot)
                _request_rerun(st)
                return

            state["operation_status"] = "generating"
            state["generation_status"] = "generating"
            callback_called = []
            try:
                with _operation_spinner(st, "Generating translations..."):
                    login_checker()
                    progress_placeholder = st.empty()

                    def on_batch(index, total, codes):
                        state["generation_current_batch_index"] = index
                        state["generation_current_batch_total"] = total
                        state["generation_current_batch_codes"] = tuple(codes)
                        progress_placeholder.info(
                            "Generating batch {} / {} — {}".format(
                                index,
                                total,
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
            except CodexLocalizationCancelled:
                state["generation_status"] = "stopped"
                state["operation_status"] = "idle"
                st.info("Generation stopped. Completed batches remain in the draft.")
                _request_rerun(st)
                return
            except (CodexLocalizationError, CodexGenerationError) as error:
                state["generation_status"] = "failed"
                state["operation_status"] = "idle"
                state["generation_error"] = str(error)
                st.error(str(error))
                _request_rerun(st)
                return
            except Exception as error:
                state["generation_status"] = "failed"
                state["operation_status"] = "idle"
                state["generation_error"] = str(error)
                st.error("Automatic translation generation failed: {}".format(error))
                _request_rerun(st)
                return
            state["operation_status"] = "idle"
            state["generation_status"] = "completed"

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
            disabled=not upload_ready or active,
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

    fragment = getattr(st, "fragment", None)
    if not callable(fragment):
        fragment = getattr(st, "experimental_fragment", None)
    if callable(fragment):
        @fragment(run_every=0.5 if state.get("generation_status") in ACTIVE_GENERATION_STATUSES else None)
        def render_generation_fragment():
            render_body()

        render_generation_fragment()
    else:
        render_body()
