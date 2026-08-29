"""Universal localization JSON editor, preview report, and publish action."""

import json
from typing import Any, Callable, Iterable, MutableMapping, Optional, Tuple

from googleapiclient.errors import HttpError
from youtube_account import YoutubeVideoNotFoundError

from localizations import parse_localizations_json
from state.manual_state import (
    manual_can_publish,
    manual_preview_is_current,
    set_manual_json,
    store_manual_preview,
)


POPULAR_PREVIEW_LANGUAGE_CODES: Tuple[str, ...] = (
    "en",
    "es",
    "hi",
    "pt-BR",
    "ar",
    "id",
    "fr",
    "de",
    "ja",
    "vi",
    "ru",
    "ko",
    "tr",
    "th",
    "it",
)


def select_manual_example_codes(
    supported_codes: Iterable[str],
    default_language_code: Optional[str] = None,
    max_count: int = 10,
) -> Tuple[str, ...]:
    """Choose popular example codes that exist in the live catalog."""
    if max_count <= 0:
        return ()

    live_by_code = {}
    for code in supported_codes:
        if isinstance(code, str) and code.strip():
            live_by_code.setdefault(code.strip().casefold(), code.strip())
    default_code = (
        default_language_code.strip().casefold()
        if isinstance(default_language_code, str) and default_language_code.strip()
        else None
    )

    selected = []
    selected_normalized = set()
    for preferred_code in POPULAR_PREVIEW_LANGUAGE_CODES:
        normalized_code = preferred_code.casefold()
        if normalized_code == default_code or normalized_code not in live_by_code:
            continue
        selected.append(live_by_code[normalized_code])
        selected_normalized.add(normalized_code)
        if len(selected) == max_count:
            return tuple(selected)

    for code in live_by_code.values():
        normalized_code = code.casefold()
        if normalized_code == default_code or normalized_code in selected_normalized:
            continue
        selected.append(code)
        selected_normalized.add(normalized_code)
        if len(selected) == max_count:
            break
    return tuple(selected)


def _example_json(codes: Iterable[str]) -> str:
    return json.dumps(
        {
            code: {
                "title": "Translated title",
                "description": "Translated description",
            }
            for code in codes
        },
        ensure_ascii=False,
        indent=2,
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
        reason = details[0].get("reason") if details and isinstance(details[0], dict) else None
        if reason == "quotaExceeded":
            st.error("YouTube API quota is exhausted. Wait for the quota reset before trying again.")
            return
    st.error("YouTube could not complete this localization request. Check the connection and try again.")


def localization_editor_key(widget_prefix: str, video_id: Optional[str]) -> str:
    """Keep Streamlit's editor widget isolated from drafts for other videos."""
    if not video_id:
        return "{}-localizations-json".format(widget_prefix)
    return "{}-localizations-json-{}".format(widget_prefix, video_id)


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


def render_manual_editor(
    state: MutableMapping[str, Any],
    video_id: Optional[str],
    service: Any,
    supported_language_codes,
    widget_prefix: str = "manual",
    on_published: Optional[Callable[[], None]] = None,
    default_language_code: Optional[str] = None,
) -> None:
    import streamlit as st

    render_markdown = getattr(st, "markdown", None)
    if render_markdown is not None:
        render_markdown(
            '<div id="localization-form"></div>', unsafe_allow_html=True
        )
    if state.get("scroll_to_form"):
        try:
            import streamlit.components.v1 as components
        except ModuleNotFoundError:
            components = None
        if components is not None:
            components.html(
                '<script>window.parent.document.getElementById('
                '"localization-form").scrollIntoView({behavior: "smooth"});'
                "</script>",
                height=0,
            )
        state["scroll_to_form"] = False

    editor_key = localization_editor_key(widget_prefix, video_id)
    if editor_key not in st.session_state:
        st.session_state[editor_key] = state.get("raw_json", "")
    raw_json_for_expander = st.session_state.get(
        editor_key, state.get("raw_json", "")
    )
    expanded = bool(
        raw_json_for_expander.strip()
        or state.get("preview_result") is not None
    )

    with st.expander("Localization JSON", expanded=expanded):
        st.caption(
            "Paste, edit, or upload direct localization JSON. Existing languages omitted from the JSON are preserved."
        )
        example_codes = select_manual_example_codes(
            supported_language_codes,
            default_language_code=default_language_code,
        )
        st.code(_example_json(example_codes), language="json")
        raw_json = st.text_area(
            "Localizations JSON",
            height=300,
            key=editor_key,
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

    with st.expander(
        "Preview & publish", expanded=state.get("preview_result") is not None
    ):
        preview_col, publish_col = st.columns(2)
        with preview_col:
            preview_clicked = st.button(
                "Preview changes",
                type="primary",
                disabled=not bool(video_id and parsed.is_valid),
                key="{}-preview-changes".format(widget_prefix),
            )
        with publish_col:
            publish_clicked = st.button(
                "Publish changes",
                disabled=not manual_can_publish(state),
                key="{}-publish-changes".format(widget_prefix),
            )

        if preview_clicked:
            state["operation_status"] = "previewing"
            try:
                with st.spinner("Comparing with the current YouTube state..."):
                    store_manual_preview(state, service.preview(video_id, raw_json))
                state["operation_status"] = "idle"
                st.rerun()
            except Exception as error:
                state["operation_status"] = "idle"
                state["operation_error"] = "youtube_api"
                _render_service_error(error)

        if publish_clicked:
            if not manual_preview_is_current(state):
                st.warning("The JSON changed after preview. Preview the changes again.")
            else:
                state["operation_status"] = "publishing"
                try:
                    with st.spinner("Publishing localization changes..."):
                        result = service.publish(video_id, raw_json)
                    store_manual_preview(state, result)
                    state["operation_status"] = "idle"
                    if result.wrote:
                        state["published"] = True
                        st.success("Localization changes published successfully.")
                        if on_published is not None:
                            on_published()
                    else:
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
