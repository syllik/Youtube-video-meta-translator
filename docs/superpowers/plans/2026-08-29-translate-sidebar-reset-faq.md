# Translate Sidebar, Reset, Draft, and FAQ Implementation Plan

> **For agentic workers:** This plan was executed inline in the current task because the user explicitly prohibited subagents. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Extend the existing unified Translate workflow with compact sidebar cards, safe destructive resets, cursor-backed Load more, durable manual drafts, merge-based Codex/LLM handoff, clearer page layout, and a static FAQ.

**Architecture:** Preserve the current Streamlit pages, shared `AppContext`, cursor-backed caches, universal editor, and Preview → Publish service. Add small pure helpers for draft serialization, merge, counts, reset payloads, and accumulated pagination; route reset through a separate service operation and keep FAQ outside YouTube bootstrap.

**Tech Stack:** Python 3, Streamlit, YouTube Data API v3, existing dataclasses/state dictionaries, `unittest`/`pytest`-compatible tests, existing project commands only.

**Spec:** `docs/superpowers/specs/2026-08-29-translate-sidebar-reset-faq-design.md`

## Global Constraints

- Keep one Translate workflow and one supporting LLM Translation prompt page; do not restore legacy workflows.
- Use live YouTube Data API `i18nLanguages.list` as the only source of valid localization language codes.
- Preserve Preview-never-writes, current-Preview-required Publish, re-fetch-before-Publish, and omitted-localization preservation semantics.
- Keep all user-facing copy, comments, docstrings, and repository documentation in English.
- Do not add provider integrations, API-key dependencies, or a second pagination/editor/publishing architecture.
- Do not push changes automatically.

---

### Task 1: Pure localization helpers and manual draft state

**Files:**
- Modify: `localizations.py`
- Modify: `state/manual_state.py`
- Modify: `ui/llm_package.py`
- Test: `tests/test_localizations.py`
- Test: `tests/test_manual_streamlit_state.py`

**Interfaces:**
- Produce `build_manual_draft_json(video_resource: Mapping[str, Any]) -> str`, excluding the video default language from localization keys and returning canonical direct JSON.
- Produce `build_video_reset_update_payload(video_resource: Mapping[str, Any]) -> Dict[str, Any]`, preserving `id`, writable snippet fields, default title/description/defaultLanguage, and setting `localizations` to `{}`.
- Produce `merge_localization_documents(current_raw_json: str, incoming_document: Mapping[str, Any]) -> str`, replacing case-insensitively overlapping language keys and retaining all other current draft keys.
- Produce `load_manual_draft(state, video_resource, force: bool = False) -> bool` and `request_manual_reload(state) -> None`; ordinary reruns must not reload a draft once its video marker is current.

- [x] **Step 1: Add failing tests for live draft serialization and reset payload.**

  Add tests that build a resource containing default `en`, localizations `de` and `fr`, and extra snippet fields. Assert the draft JSON contains only `de` and `fr`, and assert the reset payload has an empty `localizations` object while preserving title, description, defaultLanguage, categoryId, tags, and id without mutating the source resource.

- [x] **Step 2: Run the focused tests and verify they fail for missing helpers.**

  Run:

  ```bash
  python -m pytest tests/test_localizations.py -q
  ```

  Expected: the new helper tests fail because the helpers are not yet defined.

- [x] **Step 3: Implement the pure serialization and reset-payload helpers.**

  Use the existing `WRITABLE_SNIPPET_FIELDS`, deep-copy the fetched resource, preserve only fields present in `snippet`, exclude the default code with `casefold()`, and serialize direct localization entries with `ensure_ascii=False` and stable indentation.

- [x] **Step 4: Add failing tests for merge semantics and draft lifecycle.**

  Add tests for an existing draft containing `de`, `fr`, and `es` merged with incoming `ja`/`vi`; assert all five remain. Add an overlapping `de` case and assert only that entry changes. Add state tests showing a normal second `load_manual_draft` call preserves a hand-edited draft, `force=True` reloads fresh YouTube data, changing video ids loads the new video, and `request_manual_reload` causes the next load to refresh.

- [x] **Step 5: Run the focused tests and verify the lifecycle tests fail.**

  Run:

  ```bash
  python -m pytest tests/test_manual_streamlit_state.py -q
  ```

  Expected: the new merge/lifecycle assertions fail before implementation.

- [x] **Step 6: Implement merge and explicit draft lifecycle state.**

  Add a loaded-video marker and reload flag to `MANUAL_DEFAULTS`. Make `sync_manual_video` clear the old marker on video change. Make `load_manual_draft` set canonical raw JSON, clear stale validation/preview state, and consume reload requests; leave `raw_json` untouched when the same video is already loaded and no reload was requested. Update `apply_llm_upload` and `apply_generated_localizations` to merge before calling `set_manual_json`; invalid uploads must return before changing state.

- [x] **Step 7: Run the focused tests and commit the self-contained data/state change.**

  Run:

  ```bash
  python -m pytest tests/test_localizations.py tests/test_manual_streamlit_state.py -q
  ```

  Expected: PASS. Then commit:

  ```bash
  git add localizations.py state/manual_state.py ui/llm_package.py tests/test_localizations.py tests/test_manual_streamlit_state.py
  git commit -m "feat: preserve and merge translation drafts"
  ```

### Task 2: Live catalog, progress counts, pagination accumulation, and reset service

**Files:**
- Modify: `models.py`
- Modify: `state/common_state.py`
- Modify: `streamlit_app.py`
- Modify: `services/youtube_service.py`
- Modify: `services/manual_localization_service.py`
- Modify: `ui/video_list.py`
- Test: `tests/test_common_state.py`
- Test: `tests/test_video_list.py`
- Test: `tests/test_youtube_service.py`
- Test: `tests/test_localization_service.py`

**Interfaces:**
- Produce `video_localization_counts(video: VideoSummary, supported_language_codes: Iterable[str]) -> Tuple[int, int]` for `done` and `undone`, excluding the default language from both.
- Produce `load_accumulated_video_page(service, state, selection: PaginationSelection) -> YouTubePage`, `load_more_video_page(service, state, selection: PaginationSelection) -> YouTubePage`, and `can_load_more(state, selection, total_videos: int) -> bool` using existing cursor/page caches.
- Add `YoutubeService.reset_video_localizations(video_id: str) -> Mapping[str, Any]` as a separate destructive operation; it fetches current data, builds the reset payload, and performs one update.
- Extend `AppContext` with the live language catalog and make shared bootstrap load it once for sidebar, Translate, and prompt-page reuse.

- [x] **Step 1: Add failing tests for catalog-based counts and accumulated pages.**

  Add count cases where default `en` appears among current codes, a live catalog includes `en`, `de`, `fr`, `ja`, and current localizations include `de`; assert `(done, undone) == (1, 2)`. Add cursor-backed tests for initial page 1, appending page 2, repeated append not fetching or duplicating page 2, and page 2 starting a new accumulation at page 2. Assert `all` never reports a load-more opportunity.

- [x] **Step 2: Run focused state/list tests and verify the new assertions fail.**

  Run:

  ```bash
  python -m pytest tests/test_common_state.py tests/test_video_list.py -q
  ```

  Expected: failures for the missing count and accumulation interfaces.

- [x] **Step 3: Implement catalog counts and accumulation on top of existing caches.**

  Keep `page_tokens_by_limit` and `video_pages_by_limit` as the only page data source. Store only the accumulation base selection and last appended page in common state. Rebuild the visible tuple from cached numeric pages, fetch only the next missing cursor page, deduplicate by video id while retaining first-seen order, and reset accumulation when page or limit changes.

- [x] **Step 4: Add failing tests for the separate reset service path.**

  Extend the fake YouTube boundary so reset can fetch a resource and record one update. Assert `YoutubeService.reset_video_localizations("video-1")` targets exactly that id, sends an empty `localizations` object with preserved snippet fields, and does not call preview/publish helpers. Assert `ManualLocalizationService.reset` delegates to the dedicated service method.

- [x] **Step 5: Run reset service tests and verify they fail before implementation.**

  Run:

  ```bash
  python -m pytest tests/test_youtube_service.py tests/test_localization_service.py -q
  ```

  Expected: failures for the missing dedicated reset method and delegation.

- [x] **Step 6: Implement catalog reuse and the reset service path.**

  Add the catalog field to `AppContext`, fetch it under the shared bootstrap spinner, pass it through both pages, and stop duplicate page-level catalog fetches. Implement `YoutubeService.reset_video_localizations` using the pure reset payload helper and the existing account update boundary. Add `ManualLocalizationService.reset` as the explicit UI-facing operation.

- [x] **Step 7: Run all Task 2 tests and commit the service/state change.**

  Run:

  ```bash
  python -m pytest tests/test_common_state.py tests/test_video_list.py tests/test_youtube_service.py tests/test_localization_service.py -q
  ```

  Expected: PASS. Then commit:

  ```bash
  git add models.py state/common_state.py streamlit_app.py services/youtube_service.py services/manual_localization_service.py ui/video_list.py tests/test_common_state.py tests/test_video_list.py tests/test_youtube_service.py tests/test_localization_service.py
  git commit -m "feat: add live catalog counts and reset service"
  ```

### Task 3: Sidebar UI, browser confirmation, Load more, and operation feedback

**Files:**
- Modify: `ui/sidebar.py`
- Modify: `ui/video_list.py`
- Modify: `ui/pagination.py`
- Modify: `ui/styles.py`
- Modify: `state/common_state.py`
- Modify: `tests/test_sidebar.py`
- Modify: `tests/test_pagination.py`
- Modify: `tests/test_video_pagination.py`

**Interfaces:**
- Keep `render_video_list(videos, session_state, ...)` backward-compatible for existing two-argument tests while accepting live catalog codes and current query parameters.
- Render each card with title, default language, `Localizations: done / undone`, video ID, full-width Select/Selected, and full-width Reset languages.
- Render reset as an HTML button/link whose `onclick` returns native `window.confirm()`; only confirmed navigation adds a pending reset query value. Consume that value in the sidebar and call the dedicated reset operation for the exact card id.
- Render `Load more` only after all cards for numeric limits and wrap batch loading in `st.spinner` with a status guard.

- [x] **Step 1: Add failing source/UI contract tests.**

  Update sidebar tests to assert descriptions and localization badges are absent, card text contains exact done/undone counts, reset appears for an unselected card, the channel image markup has full-width styling, and the selected card uses the selected styling path. Add pagination tests asserting Previous/Next labels are icon-only and Load more appends after cards.

- [x] **Step 2: Run the sidebar and pagination tests and record expected failures.**

  Run:

  ```bash
  python -m pytest tests/test_sidebar.py tests/test_pagination.py tests/test_video_pagination.py -q
  ```

  Expected: failures against the old card markup, old pagination labels, and absent Load more/reset behavior.

- [x] **Step 3: Implement the compact channel block and video-card markup.**

  Make the channel image occupy the block width, keep all channel text in one column, remove video description/badges, calculate counts from the live catalog helper, add a subtle selected container treatment, and keep the thumbnail external icon visible without a full-image overlay. Keep YouTube thumbnail links intact.

- [x] **Step 4: Implement native confirmation and reset-query handling.**

  Build a confirmation message containing title/id, deletion warning, default-metadata result, and save-first guidance. Cancel must return false and leave the URL unchanged. On confirmed pending reset, call `ManualLocalizationService.reset`, invalidate common page caches, request selected-draft reload when the id matches, store success/error feedback, remove the pending query, and rerun once after success.

- [x] **Step 5: Implement icon pagination and Load more rendering.**

  Replace Previous/Next labels with accessible icon-only buttons, preserve page selector and URL updates, render accumulated videos from common state, and place Load more after the video list. Disable/omit it for `all`, the final page, and while a load is active. Wrap API calls in visible spinners.

- [x] **Step 6: Run the focused UI tests and commit the sidebar change.**

  Run:

  ```bash
  python -m pytest tests/test_sidebar.py tests/test_pagination.py tests/test_video_pagination.py -q
  ```

  Expected: PASS. Then commit:

  ```bash
  git add ui/sidebar.py ui/video_list.py ui/pagination.py ui/styles.py state/common_state.py tests/test_sidebar.py tests/test_pagination.py tests/test_video_pagination.py
  git commit -m "feat: simplify sidebar and add load more reset"
  ```

### Task 4: Translate/LLM page order, draft reload wiring, loaders, and static FAQ

**Files:**
- Modify: `pages/1_Translate.py`
- Modify: `pages/2_LLM_prompt.py`
- Modify: `ui/manual_editor.py`
- Modify: `ui/llm_package.py`
- Modify: `ui/llm_prompt.py`
- Modify: `streamlit_app.py`
- Create: `pages/3_FAQ.py`
- Create: `ui/faq.py`
- Test: `tests/test_streamlit_pages.py`
- Test: `tests/test_manual_streamlit_state.py`
- Test: `tests/test_llm_prompt.py`
- Test: `tests/test_legacy_regressions.py`

**Interfaces:**
- Split editor rendering into `render_localization_json_example(...)`, `render_manual_editor(...)`, and `render_preview_publish(...)` so Translate can enforce the requested order.
- Keep `render_llm_translation_controls(...)` as the only generation/upload handoff and make it merge into the shared draft.
- Provide `render_faq_page()` that imports only Streamlit and renders static short expanders.

- [x] **Step 1: Add failing page-contract tests.**

  Assert Translate source order is Example → Manual edit → Source languages → Generate translations → Preview & Publish, assert the example is not an editor, assert the prompt page contains an expander-based quality guide, and assert FAQ imports/configures/render-static content without `bootstrap_app_context`, `YoutubeService`, OAuth, fetch calls, or sidebar rendering.

- [x] **Step 2: Run the page tests and verify they fail against the current layout.**

  Run:

  ```bash
  python -m pytest tests/test_streamlit_pages.py tests/test_manual_streamlit_state.py tests/test_llm_prompt.py tests/test_legacy_regressions.py -q
  ```

  Expected: failures for section order, missing FAQ, and missing quality-guide text.

- [x] **Step 3: Split Manual edit, example, and Preview & Publish rendering.**

  Move the example into `Localization JSON Example`, keep only the text area and validation in `Manual edit`, and move preview/publish buttons/report into the final expander. Use the state draft loader before rendering the text area. On successful publish request a fresh draft reload and clear prompt/upload context before rerun.

- [x] **Step 4: Wire shared catalog, selected-video reloads, and visible operation loaders.**

  Make Translate and the prompt page consume `context.language_catalog`, wrap selected-video/catalog loads in spinners, keep source selection unchanged, wrap Codex generation in a spinner/progress placeholder, and guard preview/publish/reset/load-more actions with their operation states.

- [x] **Step 5: Restructure the LLM prompt page and add the static FAQ.**

  Put the introductory instructions, quality guide, target-language selection, generated prompt, and external links into logical expanders without changing source-selection semantics. Add the FAQ page and root page link with short practical English answers covering every required topic.

- [x] **Step 6: Run the focused page tests and commit the page change.**

  Run:

  ```bash
  python -m pytest tests/test_streamlit_pages.py tests/test_manual_streamlit_state.py tests/test_llm_prompt.py tests/test_legacy_regressions.py -q
  ```

  Expected: PASS. Then commit:

  ```bash
  git add pages/1_Translate.py pages/2_LLM_prompt.py pages/3_FAQ.py ui/faq.py ui/manual_editor.py ui/llm_package.py ui/llm_prompt.py streamlit_app.py tests/test_streamlit_pages.py tests/test_manual_streamlit_state.py tests/test_llm_prompt.py tests/test_legacy_regressions.py
  git commit -m "feat: reorganize translation pages and add faq"
  ```

### Task 5: Documentation alignment and complete verification

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/README.md`
- Modify: `docs/development.md`
- Modify: `docs/manual-localizations.md`
- Modify: `docs/llm-localizations.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/troubleshooting.md`

- [x] **Step 1: Update the documentation to match the implemented UI.**

  Document the compact sidebar, live-catalog done/undone counts, Load more/page behavior, Manual edit draft lifecycle, merge semantics, omitted-language preservation, destructive Reset languages, native confirmation, source-quality guidance, FAQ navigation, and FAQ operation without YouTube OAuth/API. Remove stale legacy control names or claims that contradict the implementation.

- [x] **Step 2: Check documentation for stale workflows and requested terms.**

  Run:

  ```bash
  rg -n -i "Manual translate|LLM translate|Machine translate|Localization JSON|Reset languages|Load more|FAQ|omitted|source language" README.md AGENTS.md docs
  ```

  Expected: only current unified-workflow terminology remains; the old example label is replaced where it referred to the UI section.

- [x] **Step 3: Run the full credential-free suite and syntax/import checks.**

  Run:

  ```bash
  python -m unittest discover -s tests -v
  python -m compileall -q streamlit_app.py pages models.py language_catalog.py llm_localization_package.py codex_localization_runner.py codex_localization_generator.py generate_codex_localizations.py services state ui youtube_account.py localizations.py localization_service.py tests
  python -m pip check
  git diff --check
  ```

  Expected: all tests pass, compileall is silent, pip reports no broken requirements, and diff check is clean.

- [x] **Step 4: Inspect the final diff and record real limitations.**

  Run:

  ```bash
  git status --short
  git diff --stat HEAD~5..HEAD
  git log -6 --oneline
  ```

  Confirm no push occurred, no credentials were added, the current main branch contains only the intended implementation/documentation commits, and the final report names any limitation that could not be verified without live YouTube/OAuth access.
