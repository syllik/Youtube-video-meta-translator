# Streamlit UI Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Flask/HTML/CSS runtime with a Streamlit application containing separate Machine translate and Manual translate pages, clear URL-backed pagination, and isolated mode state.

**Architecture:** Keep YouTube OAuth, provider integrations, and the pure localization engine behind service boundaries. Build one shared video-list/pagination layer, then wire two independent Streamlit pages whose widgets and state never cross modes.

**Tech Stack:** Python 3.12-compatible code, Streamlit multipage app, existing Google YouTube API client, DeepL, Google Cloud Translation, standard-library dataclasses and unittest.

**Spec:** `docs/superpowers/specs/2026-08-27-streamlit-migration-design.md`

## Global Constraints

- Streamlit is the only runtime UI and application entry point.
- The application launches with `streamlit run streamlit_app.py`.
- Exactly two workflow pages are exposed: `Machine translate` and `Manual translate`.
- Both pages render the shared channel context and video list; mode-only controls stay on their own page.
- Machine mode keeps multi-video, multi-language translation, DeepL preference, Google fallback, overwrite, and trim behavior.
- Manual mode handles one video per operation, validates prepared JSON, previews a diff, and publishes at most one merged update.
- Manual JSON omissions never delete existing YouTube localizations.
- Video IDs are the only selection and API identifiers; titles are display-only.
- Allowed page limits are exactly `10`, `20`, `50`, and `all`; the default is `10`.
- `page` and `limit` are stored in the URL; invalid values are normalized to a canonical URL.
- Initial loading fetches at most 10 videos unless the user explicitly selects another limit.
- YouTube cursor tokens are cached by limit and page; numeric offsets are never assumed.
- Changing the limit resets page to 1 and clears page-derived data; changing the page does not clear mode settings.
- Manual preview performs no write; publish validates and refetches current YouTube state before writing.
- Do not add subtitles, SRT, audio localization, dubbing, AI translation, CSV, Excel, database, or cloud deployment.
- Do not expose tracebacks, OAuth tokens, credential paths, or provider secrets in the UI.
- Keep tests credential-free and use mocked YouTube/provider clients.

---

## File map before implementation

Create or modify the following focused units:

```text
streamlit_app.py                         # Streamlit entry point and shared bootstrap
pages/1_Machine_translate.py             # Machine page composition only
pages/2_Manual_translate.py              # Manual page composition only
models.py                                 # Shared immutable UI/service data models
services/youtube_service.py              # OAuth-backed YouTube boundary and cursors
services/machine_translation_service.py  # DeepL/Google machine workflow
services/manual_localization_service.py  # Manual workflow facade over pure engine
state/common_state.py                    # Shared session state and page cache
state/machine_state.py                   # Machine widget/operation state
state/manual_state.py                    # Manual editor/preview state
ui/styles.py                              # Small readable Streamlit style layer
ui/channel_header.py                      # Shared channel header
ui/video_list.py                          # Shared list and mode-specific selectors
ui/pagination.py                          # URL parsing and pagination controls
ui/feedback.py                            # Shared safe status/error rendering
ui/machine_controls.py                    # Machine-only controls
ui/manual_editor.py                       # Manual-only editor and diff report
tests/test_pagination.py
tests/test_streamlit_state.py
tests/test_machine_translation_service.py
tests/test_manual_streamlit_state.py
tests/test_streamlit_pages.py
```

Retain `localizations.py` as the pure parser/validator/diff/merge engine.
Retain `google_translate.py` and the DeepL integration as provider code used
only by the machine service. `localization_service.py` stays as a compatibility
facade while the new `services/manual_localization_service.py` becomes the
page-facing boundary during the migration.

The following old runtime surfaces are removed after the new application is
verified:

```text
app.py
templates/home.html
templates/quota-error.html
static/css/home.css
static/css/quota.css
```

Flask and Jinja dependencies are removed from `requirements.txt` once no
runtime or test imports remain.

---

### Task 1: Add the Streamlit runtime shell and lazy application bootstrap

**Files:**
- Create: `streamlit_app.py`
- Create: `pages/__init__.py`
- Create: `services/__init__.py`
- Create: `state/__init__.py`
- Create: `ui/__init__.py`
- Modify: `requirements.txt`
- Test: `tests/test_streamlit_pages.py`

**Interfaces:**
- `get_youtube_service(session_state: MutableMapping[str, Any]) -> YoutubeService` creates the OAuth-backed service only when a page needs it.
- `render_app_intro() -> None` renders the root page without machine/manual widgets.
- `page_title(mode: str) -> str` returns the visible title for each page and rejects unknown modes.

- [ ] **Step 1: Write the failing bootstrap tests**

```python
import importlib
import sys
import unittest
from unittest.mock import patch

from streamlit_app import page_title


class StreamlitBootstrapTests(unittest.TestCase):
    def test_page_titles_are_explicit(self):
        self.assertEqual(page_title("machine"), "Machine translate")
        self.assertEqual(page_title("manual"), "Manual translate")

    def test_unknown_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            page_title("legacy")

    def test_import_does_not_construct_youtube_client(self):
        sys.modules.pop("streamlit_app", None)
        with patch("youtube_account.YoutubeApi") as constructor:
            importlib.import_module("streamlit_app")
            constructor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused tests and verify the missing shell fails**

Run:

```bash
python -m unittest tests.test_streamlit_pages -v
```

Expected: FAIL because `streamlit_app.py` and `page_title` do not exist yet.

- [ ] **Step 3: Add the dependency and minimal entry point**

Add a bounded Streamlit dependency to `requirements.txt`:

```text
streamlit>=1.36,<2
```

Create an entry point that contains no OAuth construction at import time:

```python
import streamlit as st


def page_title(mode):
    titles = {"machine": "Machine translate", "manual": "Manual translate"}
    if mode not in titles:
        raise ValueError("Unknown application mode: {}".format(mode))
    return titles[mode]


def render_app_intro():
    st.set_page_config(
        page_title="YouTube Metadata Translator",
        page_icon="▶",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.title("YouTube Metadata Translator")
    st.write("Choose a workflow from the navigation panel.")
    st.page_link("pages/1_Machine_translate.py", label="Machine translate")
    st.page_link("pages/2_Manual_translate.py", label="Manual translate")


if __name__ == "__main__":
    render_app_intro()
```

Use `st.cache_resource` or a session-owned factory for the YouTube service,
but keep the construction in a helper called by pages, never at module import.

- [ ] **Step 4: Run the bootstrap tests and compile the shell**

Run:

```bash
python -m unittest tests.test_streamlit_pages -v
python -m compileall -q streamlit_app.py pages services state ui
```

Expected: the bootstrap tests pass and compilation succeeds.

- [ ] **Step 5: Commit the runtime shell**

```bash
git add requirements.txt streamlit_app.py pages services state ui tests/test_streamlit_pages.py
git commit -m "feat: add Streamlit application shell"
```

### Task 2: Define shared models and a YouTube service boundary

**Files:**
- Create: `models.py`
- Create: `services/youtube_service.py`
- Modify: `youtube_account.py`
- Modify: `tests/test_youtube_localization_api.py`
- Create: `tests/test_youtube_service.py`

**Interfaces:**
- `PageLimit = Union[int, str]`, where integers are `10`, `20`, or `50` and `"all"` is the full-load sentinel.
- `ChannelInfo(name: str, thumbnail_url: str, total_videos: int)` is an immutable channel summary.
- `VideoSummary(id: str, title: str, description: str, thumbnail_url: str, current_language_codes: Tuple[str, ...])` is the shared list model.
- `YouTubePage(videos: Tuple[VideoSummary, ...], next_page_token: Optional[str])` is a single API-page result.
- `YoutubeService.fetch_channel() -> ChannelInfo` reads the authenticated channel.
- `YoutubeService.fetch_video_page(limit: PageLimit, page_token: Optional[str]) -> YouTubePage` performs one playlist/video read without UI state.
- `YoutubeService.get_video_with_localizations(video_id: str) -> Mapping[str, Any]` fetches one complete video resource.
- `YoutubeService.update_video_localizations(payload: Mapping[str, Any]) -> Mapping[str, Any]` performs one safe update.
- `YoutubeService.publish_machine_localization(video_id: str, language_code: str, title: str, description: str, trim: bool) -> MachinePublishResult` preserves the legacy one-language update semantics behind the service.

- [ ] **Step 1: Add failing service-boundary tests**

```python
import unittest
from unittest.mock import Mock

from services.youtube_service import YoutubeService


class YoutubeServiceTests(unittest.TestCase):
    def test_fetch_video_page_passes_limit_and_page_token(self):
        account = Mock()
        account.fetch_video_page.return_value = {
            "videos": [],
            "next_page_token": "next-2",
        }
        service = YoutubeService(account)

        result = service.fetch_video_page(20, "next-1")

        account.fetch_video_page.assert_called_once_with(20, "next-1")
        self.assertEqual(result.next_page_token, "next-2")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the focused tests and confirm the boundary is absent**

Run:

```bash
python -m unittest tests.test_youtube_service -v
```

Expected: FAIL because the service and shared models are not implemented.

- [ ] **Step 3: Implement the adapter without moving OAuth side effects into Streamlit imports**

Move raw YouTube reads and writes behind `YoutubeService`. Keep the existing
credential compatibility behavior in `youtube_account.py`, including
`token.json`, restricted loading of legacy `token.pickle`, refresh, and the
existing OAuth client secrets path. Add explicit account methods for fetching
one playlist page, fetching one complete video, and performing one localization
update; then have the service translate raw resources into `VideoSummary` and
`YouTubePage`.

The account layer must expose a missing-resource error consistently:

```python
if not response.get("items"):
    raise YoutubeVideoNotFoundError(video_id)
```

Do not add a title fallback to the new service. A duplicate title is valid UI
content and must never change which video is published.

- [ ] **Step 4: Run existing and new YouTube tests**

Run:

```bash
python -m unittest tests.test_youtube_service tests.test_youtube_localization_api tests.test_video_pagination tests.test_youtube_languages -v
```

Expected: PASS, with all YouTube calls still mocked.

- [ ] **Step 5: Commit the shared model and service seam**

```bash
git add models.py services/youtube_service.py youtube_account.py tests/test_youtube_service.py tests/test_youtube_localization_api.py
git commit -m "refactor: add Streamlit YouTube service boundary"
```

### Task 3: Implement URL-backed pagination and common session state

**Files:**
- Create: `state/common_state.py`
- Create: `ui/pagination.py`
- Create: `tests/test_pagination.py`
- Create: `tests/test_common_state.py`

**Interfaces:**
- `ALLOWED_LIMITS = (10, 20, 50, "all")`.
- `PaginationSelection(page: int, limit: PageLimit)` stores the normalized URL selection.
- `parse_pagination_query(params: Mapping[str, str]) -> PaginationSelection` parses and normalizes `page`/`limit`.
- `canonical_pagination_query(selection: PaginationSelection) -> Dict[str, str]` returns `{"page": "...", "limit": "..."}`.
- `page_bounds(page: int, limit: PageLimit, total_videos: int) -> Tuple[int, int]` returns the displayed inclusive/exclusive range.
- `render_page_size_control(selection: PaginationSelection, query_params: MutableMapping[str, str]) -> None` renders the page-size selector near the channel actions and writes the canonical `page=1`/`limit` query parameters.
- `render_pagination(selection: PaginationSelection, total_videos: int, query_params: MutableMapping[str, str]) -> None` renders the range summary, page selector, previous/next buttons, and writes canonical page query parameters.
- `load_video_page(service: YoutubeService, state: MutableMapping[str, Any], selection: PaginationSelection) -> YouTubePage` resolves YouTube page tokens and stores results in common state.
- `reset_video_cache(state: MutableMapping[str, Any]) -> None` clears only common page data and cursor maps.

- [ ] **Step 1: Write failing URL and range tests**

```python
import unittest

from ui.pagination import (
    PaginationSelection,
    canonical_pagination_query,
    page_bounds,
    parse_pagination_query,
)


class PaginationTests(unittest.TestCase):
    def test_missing_query_uses_ten_and_first_page(self):
        self.assertEqual(parse_pagination_query({}), PaginationSelection(1, 10))

    def test_allowed_limits_include_twenty_not_twenty_five(self):
        self.assertEqual(parse_pagination_query({"limit": "20", "page": "3"}), PaginationSelection(3, 20))
        self.assertEqual(parse_pagination_query({"limit": "25"}), PaginationSelection(1, 10))

    def test_all_is_explicit_string_sentinel(self):
        selection = parse_pagination_query({"limit": "all", "page": "7"})
        self.assertEqual(selection, PaginationSelection(1, "all"))
        self.assertEqual(canonical_pagination_query(selection), {"page": "1", "limit": "all"})

    def test_page_bounds_are_readable(self):
        self.assertEqual(page_bounds(2, 10, 117), (10, 20))
        self.assertEqual(page_bounds(12, 10, 117), (110, 117))
        self.assertEqual(page_bounds(1, "all", 117), (0, 117))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Write failing cursor-cache tests**

```python
from unittest.mock import Mock

from models import YouTubePage, VideoSummary
from state.common_state import load_video_page, reset_video_cache
from ui.pagination import PaginationSelection


def test_page_three_walks_from_the_nearest_known_token():
    service = Mock()
    service.fetch_video_page.side_effect = [
        YouTubePage((VideoSummary("1", "One", "", "", ()),), "token-2"),
        YouTubePage((VideoSummary("2", "Two", "", "", ()),), "token-3"),
        YouTubePage((VideoSummary("3", "Three", "", "", ()),), None),
    ]
    state = {}

    page = load_video_page(service, state, PaginationSelection(3, 10))

    assert page.videos[0].id == "3"
    assert service.fetch_video_page.call_count == 3


def test_reset_clears_tokens_and_pages_only():
    state = {"page_tokens_by_limit": {10: {2: "token-2"}}, "video_pages_by_limit": {10: {1: object()}}}

    reset_video_cache(state)

    assert state["page_tokens_by_limit"] == {}
    assert state["video_pages_by_limit"] == {}
```

- [ ] **Step 3: Run focused tests and verify they fail**

Run:

```bash
python -m unittest tests.test_pagination tests.test_common_state -v
```

Expected: FAIL because query parsing, cursor traversal, and cache state do not exist.

- [ ] **Step 4: Implement canonical URL parsing and cursor-aware loading**

Implement these exact branches:

```python
if limit not in {"10", "20", "50", "all"}:
    limit = 10
if limit == "all":
    page = 1
else:
    page = max(1, parse_int_or_default(raw_page, 1))
```

When total count is known, clamp a numeric page to the calculated last page.
When `limit` changes, set page to 1 before calling `reset_video_cache`. For a
numeric page, use a cached page result if present; otherwise use the nearest
known token and call `fetch_video_page` until the requested page is reached.
For `all`, repeatedly fetch with a maximum API page size of 50 and store one
combined result under the `all` key. Do not make an `all` request during the
default initial load.

The rendered control must show the complete context in one line:

```text
Videos 11–20 of 117 · Page 2 of 12 · 10 per page
```

Use `Previous`, a compact page selector, and `Next`; disable boundary actions.
On every change, update `st.query_params` and call `st.rerun()` once.

- [ ] **Step 5: Run pagination tests and compile UI helpers**

Run:

```bash
python -m unittest tests.test_pagination tests.test_common_state -v
python -m compileall -q models.py state/common_state.py ui/pagination.py
```

Expected: PASS and successful compilation.

- [ ] **Step 6: Commit URL pagination and common state**

```bash
git add models.py state/common_state.py ui/pagination.py tests/test_pagination.py tests/test_common_state.py
git commit -m "feat: add URL-backed YouTube pagination"
```

### Task 4: Build the shared readable UI components

**Files:**
- Create: `ui/styles.py`
- Create: `ui/channel_header.py`
- Create: `ui/video_list.py`
- Create: `ui/feedback.py`
- Modify: `tests/test_streamlit_pages.py`
- Create: `tests/test_video_list.py`

**Interfaces:**
- `apply_app_styles() -> None` injects only the small CSS needed for readable spacing, contrast, thumbnail sizing, and narrow layouts.
- `render_channel_header(channel: ChannelInfo, on_refresh: Callable[[], None]) -> None` renders channel identity and refresh action.
- `render_video_list(videos: Sequence[VideoSummary], mode: str, machine_state: MutableMapping[str, Any], manual_state: MutableMapping[str, Any]) -> SelectionResult` renders the shared list with mode-specific selector widgets.
- `render_feedback(message: str, kind: str) -> None` maps safe operation categories to Streamlit status elements.
- `SelectionResult(mode: str, selected_video_ids: Tuple[str, ...], selected_manual_video_id: Optional[str])` never contains title-based identifiers.

- [ ] **Step 1: Write selector-key tests**

```python
from ui.video_list import widget_key


def test_widget_keys_are_stable_by_mode_and_video_id():
    assert widget_key("machine", "video-42") == "machine-video-video-42"
    assert widget_key("manual", "video-42") == "manual-video-video-42"
    assert widget_key("machine", "video-42") != widget_key("manual", "video-42")
```

- [ ] **Step 2: Implement shared list structure**

Each video row must render:

```text
[mode selector] [thumbnail] title
                         description preview
                         video ID / YouTube link
                         language badges or “No localizations”
```

For `machine`, use checkboxes keyed as `machine-video-{video_id}` and provide
`Select all visible`. For `manual`, use one `Select`/`Selected` button per
video card keyed as `manual-video-{video_id}` and return exactly one selected ID.
Keep the list
visible on both pages and do not show an inline manual editor in the list.

Use `st.columns` with a narrower selector/thumbnail column and a flexible text
column. Make the ID and link secondary information, not part of the title.
Do not use color alone for localization status; include text labels or counts.

- [ ] **Step 3: Add shared header, feedback, and accessible style**

The header shows channel thumbnail, channel name, `Total videos: N`, and
`Refresh list`. Feedback maps `oauth_required`, `quota_exceeded`,
`video_not_found`, `youtube_api`, `translation_failed`, and
`operation_in_progress` to short recovery instructions. Raw exception text is
logged, not shown.

- [ ] **Step 4: Run shared UI unit tests**

Run:

```bash
python -m unittest tests.test_video_list tests.test_streamlit_pages -v
```

Expected: PASS without OAuth or a live Streamlit browser session.

- [ ] **Step 5: Commit the shared visual layer**

```bash
git add ui/styles.py ui/channel_header.py ui/video_list.py ui/feedback.py tests/test_video_list.py tests/test_streamlit_pages.py
git commit -m "feat: add shared Streamlit video list UI"
```

### Task 5: Extract the machine translation workflow and machine state

**Files:**
- Create: `services/machine_translation_service.py`
- Create: `state/machine_state.py`
- Create: `ui/machine_controls.py`
- Create: `tests/test_machine_translation_service.py`
- Create: `tests/test_machine_state.py`
- Modify: `google_translate.py`

**Interfaces:**
- `MachineTranslationOptions(prefer_deepl: bool, overwrite: bool, trim: bool)` stores only machine settings.
- `MachineError(video_id: Optional[str], language_code: Optional[str], error_type: str, message: str)` stores a safe user-facing batch error.
- `MachineTranslationResult(translated: int, skipped: int, trimmed: int, errors: Tuple[MachineError, ...])` stores safe operation results.
- `MachineTranslationService.translate_and_publish(video_ids: Sequence[str], language_codes: Sequence[str], options: MachineTranslationOptions) -> MachineTranslationResult` performs the existing batch flow without Streamlit imports.
- `init_machine_state(session_state: MutableMapping[str, Any]) -> None` initializes only machine keys.
- `clear_machine_operation(session_state: MutableMapping[str, Any]) -> None` clears only the machine result/status.
- `machine_can_submit(state: Mapping[str, Any]) -> bool` returns true only when at least one video and language are selected and no operation is active.
- `render_machine_controls(...) -> MachineTranslationOptions` renders provider, language, overwrite, trim, and submit controls.

- [ ] **Step 1: Write failing provider and selection tests**

```python
from unittest.mock import Mock

from services.machine_translation_service import (
    MachineTranslationOptions,
    MachineTranslationService,
)


def test_deepl_falls_back_to_google_when_deepl_is_unavailable():
    deepl = Mock()
    deepl.translate_text.side_effect = RuntimeError("DeepL unavailable")
    google = Mock()
    google.translate_text.return_value = "Google result"
    youtube = Mock()
    youtube.get_video_with_localizations.return_value = {
        "id": "video-1",
        "snippet": {"title": "Original", "description": "Text", "categoryId": "22"},
        "localizations": {},
    }

    service = MachineTranslationService(youtube, deepl=deepl, google=google)
    result = service.translate_and_publish(
        ["video-1"], ["es"], MachineTranslationOptions(True, False, False)
    )

    assert result.translated == 1
    google.translate.assert_called()


def test_existing_language_is_skipped_when_overwrite_is_off():
    youtube = Mock()
    youtube.get_video_with_localizations.return_value = {
        "id": "video-1",
        "snippet": {"title": "Original", "description": "Text", "categoryId": "22"},
        "localizations": {"es": {"title": "Old", "description": "Old"}},
    }
    service = MachineTranslationService(youtube, deepl=None, google=Mock())

    result = service.translate_and_publish(
        ["video-1"], ["es"], MachineTranslationOptions(False, False, False)
    )

    assert result.skipped == 1
    youtube.publish_machine_localization.assert_not_called()
```

- [ ] **Step 2: Run machine tests and verify they fail**

Run:

```bash
python -m unittest tests.test_machine_translation_service tests.test_machine_state -v
```

Expected: FAIL because the new service and state helpers do not exist.

- [ ] **Step 3: Extract the current translation loop into the service**

Preserve the current branches:

```text
if video ID is not in the selected video set
    record videoNotFound and do not write
if language code is unavailable
    record translationUnavailable and do not write
if language already exists and overwrite is false
    increment skipped and continue
if DeepL is preferred and supports the language
    try DeepL for title and description
if DeepL fails or does not support the language
    use Google Translation
if provider translation fails
    stop the batch with translationFailed and do not publish that item
if trim is true
    trim title/description to the existing YouTube limits and increment trimmed
else if either value is too long
    increment skipped and continue
else
    publish the localization through YoutubeService
```

Do not import `streamlit` in this service. Inject provider clients and a sleep
function so tests can run instantly. Keep `time.sleep(1)` behavior in the real
factory only if it is still required by the provider/API workflow.

- [ ] **Step 4: Implement namespaced machine state and controls**

Use stable ID keys:

```python
machine_state = session_state.setdefault("machine", {
    "selected_video_ids": set(),
    "select_all_visible": False,
    "select_all_channel": False,
    "selected_language_codes": set(),
    "prefer_deepl": False,
    "overwrite": False,
    "trim": False,
    "operation_status": "idle",
    "operation_result": None,
    "operation_error": None,
})
```

Keep settings when pagination changes. Remove IDs that are no longer in the
channel only after a refresh confirms they disappeared. Disable machine inputs
while `operation_status == "running"` and, on completion, clear common video
cache then reload the same canonical `page`/`limit` URL.

- [ ] **Step 5: Run machine tests and verify behavior**

Run:

```bash
python -m unittest tests.test_machine_translation_service tests.test_machine_state -v
```

Expected: PASS, including fallback, skip, trim, overwrite, and disabled-submit cases.

- [ ] **Step 6: Commit the machine workflow**

```bash
git add services/machine_translation_service.py state/machine_state.py ui/machine_controls.py google_translate.py tests/test_machine_translation_service.py tests/test_machine_state.py
git commit -m "refactor: isolate machine translation workflow"
```

### Task 6: Add the manual localization service and manual state rules

**Files:**
- Create: `services/manual_localization_service.py`
- Create: `state/manual_state.py`
- Create: `ui/manual_editor.py`
- Create: `tests/test_manual_streamlit_state.py`
- Modify: `localization_service.py`
- Modify: `tests/test_localization_service.py`

**Interfaces:**
- `ManualLocalizationService.preview(video_id: str, raw_json: str) -> LocalizationOperationResult` validates and fetches current state without writing.
- `ManualLocalizationService.publish(video_id: str, raw_json: str) -> LocalizationOperationResult` validates, refetches, merges, and writes at most once.
- `init_manual_state(session_state: MutableMapping[str, Any]) -> None` initializes only manual keys.
- `set_manual_video(session_state: MutableMapping[str, Any], video_id: Optional[str]) -> None` clears stale preview state when the selected ID changes.
- `set_manual_json(session_state: MutableMapping[str, Any], raw_json: str) -> None` clears preview state whenever the raw JSON changes.
- `manual_preview_is_current(state: Mapping[str, Any]) -> bool` compares the selected video and raw JSON fingerprint with the stored preview.
- `manual_can_publish(state: Mapping[str, Any]) -> bool` enables publish only for a current valid preview with changes.
- `render_manual_editor(...) -> None` renders the JSON editor, local validation, preview report, and publish action only after a video is selected with its card button.

- [ ] **Step 1: Write failing manual state tests**

```python
from state.manual_state import (
    manual_can_publish,
    manual_preview_is_current,
    set_manual_json,
    set_manual_video,
)


def test_switching_video_invalidates_preview():
    state = {
        "selected_video_id": "video-1",
        "raw_json": '{"es": {"title": "A", "description": "B"}}',
        "preview_fingerprint": ("video-1", "hash-1"),
        "preview_result": object(),
    }

    set_manual_video(state, "video-2")

    assert state["preview_result"] is None
    assert not manual_preview_is_current(state)
    assert not manual_can_publish(state)


def test_json_change_invalidates_preview_even_for_same_video():
    state = {
        "selected_video_id": "video-1",
        "raw_json": "old",
        "preview_fingerprint": ("video-1", "old-hash"),
        "preview_result": object(),
    }

    set_manual_json(state, "new")

    assert state["preview_result"] is None
    assert not manual_can_publish(state)
```

- [ ] **Step 2: Run the focused manual tests and verify they fail**

Run:

```bash
python -m unittest tests.test_manual_streamlit_state tests.test_localization_service -v
```

Expected: FAIL because state helpers and the Streamlit-facing service facade do not exist.

- [ ] **Step 3: Add the facade over the existing pure localization engine**

Do not duplicate parsing, validation, diff, or merge logic. Delegate to the
existing `parse_localizations_json`, `preview_localizations`, and
`publish_localizations` functions. Keep `localization_service.py` importing or
re-exporting the new facade so current pure-service tests remain meaningful.

The service must follow this sequence:

```text
Preview:
    parse JSON
    if invalid: return issues without YouTube fetch
    fetch current video with snippet + localizations
    build diff and merged payload
    return result with wrote=False

Publish:
    parse JSON again
    if invalid: return issues without fetch/write
    fetch current video again
    build fresh diff and merged payload
    if no added/changed entries: return wrote=False
    call one update_video_localizations(payload)
    return wrote=True
```

The publish button must not rely on a previous preview object as authorization
to write. It may use the fingerprint only to disable obviously stale UI; the
service still validates and refetches unconditionally.

- [ ] **Step 4: Implement manual state transitions and editor rendering**

Use a stable fingerprint:

```python
def manual_fingerprint(video_id, raw_json):
    return (video_id, hashlib.sha256(raw_json.encode("utf-8")).hexdigest())
```

When no video is selected, show selection guidance and do not render the
textarea. When a video is selected with its card button, render the textarea
and local validation.
The user must click `Preview changes` to fetch YouTube state; this prevents an
API request on every keystroke. After preview, show:

```text
Added: N · Changed: N · Unchanged: N · Preserved: N
```

Render each language with text status (`Added`, `Changed`, `Unchanged`) and
before/after title and description in expanders. Render field-level errors as
`ja.title: ...`. Enable `Publish changes` only when the preview fingerprint
matches the current video/JSON and there is at least one change.

- [ ] **Step 5: Run manual tests and the pure localization suite**

Run:

```bash
python -m unittest tests.test_manual_streamlit_state tests.test_localization_service tests.test_localizations tests.test_localization_api -v
```

Expected: PASS, with no YouTube update during preview and one update at most during publish.

- [ ] **Step 6: Commit the manual workflow**

```bash
git add services/manual_localization_service.py state/manual_state.py ui/manual_editor.py localization_service.py tests/test_manual_streamlit_state.py tests/test_localization_service.py
git commit -m "refactor: isolate manual localization workflow"
```

### Task 7: Compose the two Streamlit pages and enforce mode separation

**Files:**
- Create: `pages/1_Machine_translate.py`
- Create: `pages/2_Manual_translate.py`
- Modify: `streamlit_app.py`
- Modify: `tests/test_streamlit_pages.py`

**Interfaces:**
- `render_machine_page() -> None` composes common bootstrap, machine controls, shared video list, and shared pagination.
- `render_manual_page() -> None` composes common bootstrap, manual card-button list, manual editor, and shared pagination.
- `render_common_page_context(mode: str) -> CommonPageContext` loads the channel and current page exactly once per rerun.

- [ ] **Step 1: Add page-content contract tests**

```python
from pathlib import Path


def test_machine_page_contains_machine_components_only():
    source = Path("pages/1_Machine_translate.py").read_text()
    assert "render_machine_controls" in source
    assert "render_video_list" in source
    assert "render_manual_editor" not in source


def test_manual_page_contains_manual_components_only():
    source = Path("pages/2_Manual_translate.py").read_text()
    assert "render_manual_editor" in source
    assert "render_video_list" in source
    assert "render_machine_controls" not in source
```

- [ ] **Step 2: Wire the common context**

The shared page bootstrap must execute this order:

```text
read and canonicalize page/limit from st.query_params
    ↓
initialize common state
    ↓
construct/reuse YoutubeService lazily
    ↓
if channel is unavailable: render safe auth/API state and stop
    ↓
fetch only the requested page from common cache/cursor state
    ↓
render channel header
    ↓
return current VideoSummary list and PaginationSelection
```

Do not initialize a machine provider on the manual page. Do not initialize
manual preview state on the machine page beyond its inert namespace defaults.

- [ ] **Step 3: Wire the machine page**

Render in this order:

```text
Machine translate title and explanation
channel header
machine controls
Select all visible + optional Select all channel
shared video list with checkboxes
pagination summary and controls
```

On submit:

```text
if no video IDs: show “Select at least one video”
else if no language codes: show “Select at least one language”
else if an operation is running: keep controls disabled
else set running → call MachineTranslationService → show result
```

Use only current-page video IDs unless the explicit `Select all channel` action
has been chosen after `limit=all`. Preserve current multi-video behavior.

- [ ] **Step 4: Wire the manual page**

Render in this order:

```text
Manual translate title and explanation
channel header
shared video list with card-level Select/Selected buttons
if no selected ID: show “Select one video to begin”
else render manual JSON editor and local validation
if Preview changes was clicked: show fresh diff/preserved summary
if preview is current and changed: enable Publish changes
pagination summary and controls
```

Do not show provider, overwrite, trim, language multi-select, or machine
checkbox controls on this page.

- [ ] **Step 5: Run page tests and launch a local smoke check**

Run:

```bash
python -m unittest tests.test_streamlit_pages tests.test_streamlit_state -v
python -m compileall -q streamlit_app.py pages models.py services state ui
```

Then launch locally:

```bash
streamlit run streamlit_app.py --server.headless true
```

Verify manually with mocked or configured local credentials:

1. The root navigation exposes only Machine translate and Manual translate.
2. The initial URL resolves to `page=1&limit=10`.
3. The machine page shows checkboxes and machine controls only.
4. The manual page shows card-level Select/Selected buttons and the editor only after selection.
5. Changing to `limit=20` rewrites the URL to `page=1&limit=20`.
6. Moving to page 2 shows `Videos 21–40 of ...` for limit 20 and no stale page-1 rows.
7. Switching pages preserves the URL position but does not submit state from the other mode.

- [ ] **Step 6: Commit the composed pages**

```bash
git add streamlit_app.py pages/1_Machine_translate.py pages/2_Manual_translate.py tests/test_streamlit_pages.py tests/test_streamlit_state.py
git commit -m "feat: add separate machine and manual Streamlit pages"
```

### Task 8: Remove the Flask UI path and migrate documentation

**Files:**
- Delete: `app.py`
- Delete: `templates/home.html`
- Delete: `templates/quota-error.html`
- Delete: `static/css/home.css`
- Delete: `static/css/quota.css`
- Modify: `requirements.txt`
- Modify: `README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/development.md`
- Modify: `docs/manual-localizations.md`
- Modify: `docs/legacy-translation.md`
- Modify: `docs/troubleshooting.md`
- Modify: `tests/test_legacy_regressions.py`
- Modify: `tests/test_localization_api.py`

**Interfaces:**
- No Flask import remains in runtime or tests.
- `python -m unittest discover -s tests -v` tests services and Streamlit-independent helpers rather than Flask endpoints.
- README startup instructions use `streamlit run streamlit_app.py`.

- [ ] **Step 1: Replace Flask-specific tests with service/page contracts**

Preserve the behaviors worth keeping from the old tests:

```text
duplicate titles do not select the wrong video
legacy provider fallback and overwrite/trim behavior remain covered
manual preview never writes
manual publish refetches and writes once
invalid manual JSON never fetches or writes
pagination clears stale page data
```

Remove assertions about Flask routes, Jinja rendering, DOM IDs, Axios, and
browser modals. Move their useful cases into
`test_machine_translation_service.py`, `test_manual_streamlit_state.py`,
`test_streamlit_pages.py`, and the YouTube service tests.

- [ ] **Step 2: Remove the Flask runtime files and dependencies**

Delete the old Flask UI files only after page tests pass. Remove `Flask`,
`Jinja2`, `MarkupSafe`, `Werkzeug`, `click`, `itsdangerous`, and any other
dependency that is no longer required by the installed runtime. Keep Google,
DeepL, dotenv, and Streamlit dependencies.

- [ ] **Step 3: Update user-facing documentation**

Document:

```text
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Explain that the sidebar switches between two independent workflows. State the
pagination URL contract, the `10 / 20 / 50 / all` choices, machine selection
semantics, and manual JSON preview/publish safety. Keep OAuth and credential
instructions, replacing Flask-specific port/browser wording with Streamlit
startup wording where necessary.

- [ ] **Step 4: Prove the old UI is absent**

Run:

```bash
rg -n "from flask|import flask|render_template|url_for|axios|home\.html|quota-error\.html|/api/localizations" --glob '*.py' --glob '*.html' .
```

Expected: no Flask/HTML runtime references remain. Manual localization service
tests must call Python service methods directly.

- [ ] **Step 5: Commit the Flask removal and docs**

```bash
git add -A
git commit -m "refactor: replace Flask UI with Streamlit"
```

### Task 9: Run the complete verification suite and review the final diff

**Files:**
- Modify: files listed in Tasks 1–8 when a verification command exposes a regression
- Test: `tests/` full credential-free suite

- [ ] **Step 1: Run the full credential-free tests**

```bash
python -m unittest discover -s tests -v
```

Expected: all tests pass without Google OAuth, YouTube credentials, DeepL, or
Google Cloud Translation network calls.

- [ ] **Step 2: Run compile, dependency, and whitespace checks**

```bash
python -m compileall -q streamlit_app.py pages models.py services state ui localizations.py google_translate.py youtube_account.py tests
python -m pip check
git diff --check
```

Expected: compilation succeeds, pip reports no broken requirements, and the
diff has no whitespace errors.

- [ ] **Step 3: Run static behavior checks**

```bash
rg -n "limit.*25|value=25|25 per page|Videos Per Page" .
rg -n "selected_videos|video_title.*identifier|replace\(' ', ''\)" pages services state ui
rg -n "Flask|render_template|axios|templates/|static/css" --glob '!docs/superpowers/**' .
```

Expected: no `25` pagination option remains, no new title-based API selection
exists, and no Flask runtime references remain.

- [ ] **Step 4: Verify URL and state acceptance cases**

Check the final app against this table:

| Action | Expected result |
| --- | --- |
| First open | `page=1`, `limit=10`, no more than 10 videos loaded |
| Choose 20 | URL becomes `page=1&limit=20`; page cache and cursor map reset |
| Choose page 2 | URL keeps `limit=20`; range shows 21–40; no stale rows |
| Choose `all` | URL uses `limit=all`; all videos load only after explicit action |
| Switch to Machine translate | Checkboxes and machine controls only |
| Switch to Manual translate | Select/Selected buttons and manual editor only |
| Change machine page selection | Manual preview state remains untouched |
| Change manual video | JSON preview is invalidated; publish disabled |
| Edit manual JSON | Preview is invalidated; YouTube is not called until Preview |
| Publish manual changes | JSON revalidated, current state refetched, at most one update |
| Duplicate video titles | ID selection still targets the chosen video |

- [ ] **Step 5: Review status and hand off**

```bash
git status --short --branch
git log --oneline -8
```

Confirm that only intended Streamlit migration files changed, no credentials
or generated token files are staged, and the final handoff includes the launch
command, test command, and known requirement for configured YouTube OAuth.
