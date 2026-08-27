"""Manual-only JSON editor, preview report, and publish action."""

import html
from typing import Any, Mapping, MutableMapping

from localizations import parse_localizations_json
from state.manual_state import (
    manual_can_publish,
    manual_preview_is_current,
    set_manual_json,
    store_manual_preview,
)


def _render_errors(issues) -> None:
    import streamlit as st

    for issue in issues:
        path = issue.path or "document"
        st.error("{}: {}".format(path, issue.message))


def _render_report(result: Any) -> None:
    import streamlit as st

    summary = result.plan.diffs
    counts = {"added": 0, "changed": 0, "unchanged": 0}
    for item in summary:
        counts[item.status] += 1
    preserved = result.plan.preserved_language_codes
    st.info(
        "Added: {} · Changed: {} · Unchanged: {} · Preserved: {}".format(
            counts["added"], counts["changed"], counts["unchanged"], len(preserved)
        )
    )
    if preserved:
        st.caption("Preserved existing languages: {}".format(", ".join(preserved)))
    for diff in result.plan.diffs:
        label = "{} — {}".format(diff.language_code, diff.status.title())
        with st.expander(label, expanded=diff.status in {"added", "changed"}):
            if diff.existing is None:
                st.caption("No existing localization")
            else:
                st.markdown("**Before**")
                st.code(
                    "title: {}\ndescription: {}".format(
                        html.escape(diff.existing.title),
                        html.escape(diff.existing.description),
                    ),
                    language="text",
                )
            st.markdown("**After**")
            st.code(
                "title: {}\ndescription: {}".format(
                    html.escape(diff.submitted.title),
                    html.escape(diff.submitted.description),
                ),
                language="text",
            )


def render_manual_editor(
    state: MutableMapping[str, Any],
    video: Any,
    service: Any,
    supported_language_codes,
) -> None:
    import streamlit as st

    st.subheader("Manual localizations")
    st.caption(
        "Paste prepared JSON. Existing languages omitted from the JSON are preserved."
    )
    st.code(
        '{\n  "de": {\n    "title": "German title",\n    "description": "German description"\n  }\n}',
        language="json",
    )
    raw_json = st.text_area(
        "Localizations JSON",
        value=state.get("raw_json", ""),
        height=300,
        key="manual-localizations-json",
        placeholder="Paste a JSON object keyed by YouTube language code",
    )
    set_manual_json(state, raw_json)
    parsed = parse_localizations_json(raw_json, supported_language_codes)
    state["local_validation"] = parsed
    if parsed.issues:
        _render_errors(parsed.issues)
    elif raw_json.strip():
        st.success("JSON is valid. Preview it against the current YouTube state.")
    else:
        st.info("Paste JSON to continue.")

    preview_col, publish_col = st.columns(2)
    with preview_col:
        preview_clicked = st.button(
            "Preview changes",
            type="primary",
            disabled=not bool(video and parsed.is_valid),
            key="manual-preview-changes",
        )
    with publish_col:
        publish_clicked = st.button(
            "Publish changes",
            disabled=not manual_can_publish(state),
            key="manual-publish-changes",
        )

    if preview_clicked:
        state["operation_status"] = "previewing"
        try:
            store_manual_preview(state, service.preview(video.id, raw_json))
            state["operation_status"] = "idle"
            st.rerun()
        except Exception:
            state["operation_status"] = "idle"
            state["operation_error"] = "youtube_api"
            st.error("Could not preview the current YouTube localization state.")

    if publish_clicked:
        if not manual_preview_is_current(state):
            st.warning("The JSON changed after preview. Preview the changes again.")
        else:
            state["operation_status"] = "publishing"
            try:
                result = service.publish(video.id, raw_json)
                store_manual_preview(state, result)
                state["operation_status"] = "idle"
                if result.wrote:
                    st.success("Localization changes published successfully.")
                else:
                    st.info("No localization changes were found.")
            except Exception:
                state["operation_status"] = "idle"
                state["operation_error"] = "youtube_api"
                st.error("Could not publish localization changes.")

    result = state.get("preview_result")
    if result is not None:
        if result.plan.issues:
            _render_errors(result.plan.issues)
        else:
            _render_report(result)
