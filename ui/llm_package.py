"""Streamlit controls for the prompt-only localization workflow."""

import hashlib
import json
from typing import Any, MutableMapping, Sequence

from llm_localization_package import (
    calculate_llm_translation_progress,
    parse_llm_upload_json,
)
from localizations import LocalizationIssue, ParsedLocalizations
from state.llm_state import set_llm_prompt
from state.manual_state import set_manual_json


def apply_llm_upload(
    state: MutableMapping[str, Any],
    file_content: bytes,
    expected_language_codes: Sequence[str],
) -> ParsedLocalizations:
    """Validate an uploaded UTF-8 batch and hand valid JSON to the editor."""
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

    canonical_json = json.dumps(
        {
            language_code: value.to_dict()
            for language_code, value in parsed.entries.items()
        },
        ensure_ascii=False,
        indent=2,
    )
    set_manual_json(state, canonical_json)
    return parsed


def _render_issues(issues) -> None:
    import streamlit as st

    for issue in issues:
        st.error("{}: {}".format(issue.path or "document", issue.message))


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
) -> None:
    """Show progress, prompt-page handoff, and local JSON upload."""
    import streamlit as st
    import streamlit.components.v1 as components

    st.markdown('<div id="llm-translation-form"></div>', unsafe_allow_html=True)
    if state.get("scroll_to_form"):
        components.html(
            '<script>window.parent.document.getElementById('
            '"llm-translation-form").scrollIntoView({behavior: "smooth"});'
            "</script>",
            height=0,
        )
        state["scroll_to_form"] = False

    progress = calculate_llm_translation_progress(video_resource, catalog)
    st.caption(
        "YouTube translations: {} / {}".format(progress.current, progress.total)
    )
    st.caption("Missing translations: {}".format(progress.missing_count))
    st.page_link(
        "pages/3_LLM_prompt.py",
        label="LLM Translation prompt",
    )
    if not progress.missing:
        st.success("All supported YouTube localizations are complete.")
        return

    prompt_video_id = state.get("prompt_video_id")
    target_codes = state.get("prompt_target_codes", ())
    prompt = state.get("prompt_text", "")
    if prompt_video_id != video_resource.get("id") or not target_codes or not prompt:
        return

    st.caption("Selected languages: {}".format(", ".join(target_codes)))
    st.caption("Prompt is ready on the supporting LLM Translation prompt page.")

    uploaded_file = st.file_uploader(
        "Upload JSON file",
        type=["json"],
        key="llm-localizations-upload",
    )
    if uploaded_file is None:
        return

    file_content = uploaded_file.getvalue()
    upload_context = _upload_context(video_resource, target_codes, file_content)
    if state.get("consumed_upload_context") == upload_context:
        return
    if state.get("upload_issue_context") == upload_context:
        _render_issues(state.get("upload_issues", ()))
        return

    parsed = apply_llm_upload(state, file_content, target_codes)
    if not parsed.is_valid:
        state["upload_issue_context"] = upload_context
        state["upload_issues"] = parsed.issues
        _render_issues(parsed.issues)
        return

    state["consumed_upload_context"] = upload_context
    state["upload_issue_context"] = None
    state["upload_issues"] = ()
    editor_key = "{}-localizations-json".format(widget_prefix)
    st.session_state[editor_key] = state["raw_json"]
    st.rerun()
