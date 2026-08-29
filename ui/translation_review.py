"""Preview and publish controls for the internal translation draft."""

from typing import Any, Callable, MutableMapping, Optional

from googleapiclient.errors import HttpError
from youtube_account import YoutubeVideoNotFoundError

from localizations import validate_localizations
from state.translation_state import (
    clear_translation_draft,
    store_translation_preview,
    translation_can_publish,
    translation_preview_is_current,
)


def _render_errors(issues) -> None:
    import streamlit as st

    for issue in issues:
        path = issue.path or "document"
        st.error("{}: {}".format(path, issue.message))


def _render_service_error(error: Exception) -> None:
    import streamlit as st

    if isinstance(error, YoutubeVideoNotFoundError):
        st.error("The selected video was not found. Refresh the list and select it again.")
        return
    if isinstance(error, HttpError):
        details = getattr(error, "error_details", None) or []
        reason = (
            details[0].get("reason")
            if details and isinstance(details[0], dict)
            else None
        )
        if reason == "quotaExceeded":
            st.error(
                "YouTube API quota is exhausted. Wait for the quota reset before trying again."
            )
            return
    st.error(
        "YouTube could not complete this localization request. "
        "Check the connection and try again."
    )


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
                        diff.existing.title,
                        diff.existing.description,
                    ),
                    language="text",
                )
            st.markdown("**After**")
            st.code(
                "title: {}\ndescription: {}".format(
                    diff.submitted.title,
                    diff.submitted.description,
                ),
                language="text",
            )


def render_preview_publish(
    state: MutableMapping[str, Any],
    video_id: Optional[str],
    service: Any,
    supported_language_codes,
    widget_prefix: str = "translate",
    on_published: Optional[Callable[[], None]] = None,
) -> None:
    """Render read-only review controls for one internal translation draft."""
    import streamlit as st

    if hasattr(video_id, "id"):
        video_id = video_id.id
    draft = state.get("draft") or {}
    parsed = state.get("draft_validation")
    if parsed is None:
        parsed = validate_localizations(draft, supported_language_codes)
        state["draft_validation"] = parsed

    with st.expander(
        "Preview and publish", expanded=state.get("preview_result") is not None
    ):
        if not draft:
            st.info("Generate or upload translations to create a draft for Preview.")
        preview_col, spacer_col, publish_col = st.columns((1, 3, 1))
        with preview_col:
            preview_clicked = st.button(
                "Preview changes",
                type="primary",
                disabled=(
                    state.get("operation_status") not in (None, "idle")
                    or not bool(video_id and parsed.is_valid)
                ),
                key="{}-preview-changes".format(widget_prefix),
            )
        with publish_col:
            publish_clicked = st.button(
                "Publish changes",
                disabled=(
                    state.get("operation_status") not in (None, "idle")
                    or not translation_can_publish(state)
                ),
                key="{}-publish-changes".format(widget_prefix),
            )

        if preview_clicked:
            state["operation_status"] = "previewing"
            try:
                with st.spinner("Comparing with the current YouTube state..."):
                    store_translation_preview(state, service.preview(video_id, draft))
                state["operation_status"] = "idle"
                st.rerun()
            except Exception as error:
                state["operation_status"] = "idle"
                state["operation_error"] = "youtube_api"
                _render_service_error(error)

        if publish_clicked:
            if not translation_preview_is_current(state):
                st.warning("The draft changed after Preview. Preview the changes again.")
            else:
                state["operation_status"] = "publishing"
                try:
                    with st.spinner("Publishing localization changes..."):
                        result = service.publish(
                            video_id,
                            draft,
                            expected_video=state["preview_result"].video,
                        )
                    if result.wrote:
                        clear_translation_draft(state)
                        st.success("Localization changes published successfully.")
                        if on_published is not None:
                            on_published()
                    else:
                        store_translation_preview(state, result)
                        state["operation_status"] = "idle"
                        st.info("No localization changes were found.")
                except Exception as error:
                    state["operation_status"] = "idle"
                    state["operation_error"] = "youtube_api"
                    _render_service_error(error)

        result = state.get("preview_result")
        if result is not None:
            if result.plan.issues:
                _render_errors(result.plan.issues)
            else:
                _render_report(result)
