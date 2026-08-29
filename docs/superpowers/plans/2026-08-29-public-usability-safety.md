# Public Usability and Safety Implementation Plan

> **For agentic workers:** This plan is executed inline because the approved specification prohibits subagents. Steps use checkbox syntax for tracking.

**Goal:** Harden destructive Reset, clarify the primary Translate workflow, make failures actionable, and publish synchronized English plus 26 localized ordinary-user guides.

**Architecture:** Preserve the existing Streamlit pages, state dictionaries, YouTube account boundary, Preview/Publish service, Codex subprocess safety, and direct JSON upload contract. Add only narrow guards and render helpers at the existing service/UI boundaries; do not introduce a concurrency framework, provider integration, backend, or second workflow.

**Tech Stack:** Python 3, Streamlit, YouTube Data API v3, existing dataclasses/state dictionaries, `unittest` fakes/mocks, Markdown documentation.

**Spec:** User-provided specification in `/Users/mihaildovgun/.codex/attachments/7d034da2-4b45-4874-b4b6-89eb4f2655fa/pasted-text.txt`.

## Global Constraints

- Work against `main @ 3051a6b6b9535208ec9a8fbe32c24d721aa6a24a` baseline after verifying the current HEAD.
- Keep one `Translate` workflow and one `LLM Translation prompt` supporting page.
- Preserve Preview read-only behavior, fresh Publish refetch, ETag/`If-Match`, stale Preview protection, omitted-localization preservation, and selected-video state binding.
- Use existing `unittest` tests with fakes/mocks; never perform real YouTube writes or Codex translations in automated tests.
- For behavioral fixes, add the regression test first, observe the expected failure, then implement the smallest fix.
- Keep code comments and canonical documentation in English; write the final implementation report in Russian.
- Do not add dependencies, providers, APIs, workflows, telemetry, CI/CD, packaging, manual JSON editor, or architecture rewrites.
- Do not modify `docs/superpowers/**` history or translate `docs/development.md`.

### Task 1: Conditional destructive Reset

**Files:**
- Modify: `services/youtube_service.py`
- Test: `tests/test_youtube_service.py`

**Interfaces:**
- `YoutubeService.reset_video_localizations(video_id: str)` fetches one fresh resource, requires a usable `etag`, calls `account.update_video_localizations(payload, if_match=etag)`, and performs the existing verification only after an accepted write.

- [x] Add RED tests for fresh-ETag forwarding, missing/blank ETag no-write, HTTP 412 no-success/no-retry/no-verification, and successful conditional-write verification.
- [x] Run `.venv/bin/python -m unittest tests.test_youtube_service tests.test_youtube_localization_api -v` and confirm only the new expectations fail.
- [x] Implement the conditional call using the fetched resource's exact ID and ETag; convert 412/precondition failures to `YoutubeResetError` with actionable no-write wording; do not add a fallback without ETag.
- [x] Re-run the focused tests and then the full suite.

### Task 2: Selected-video-only Danger zone

**Files:**
- Modify: `ui/video_list.py`
- Modify: `ui/sidebar.py`
- Modify: `ui/reset_control.py` only if the existing component contract needs a narrow label/key adjustment
- Modify: `state/common_state.py` only if a pending-selection guard needs shared state support
- Test: `tests/test_sidebar.py`
- Test: `tests/test_video_list.py`

**Interfaces:**
- `render_video_list(videos, session_state, supported_language_codes=())` renders cards without destructive controls.
- Sidebar renders one collapsed `Danger zone` only when `common.selected_video_id` is set and passes only that selected ID to the reset component.
- `_consume_pending_reset(context, session_state)` refuses to call the service when pending and current selected IDs differ.

- [x] Add RED tests proving cards contain no Reset, no selected video hides Danger zone, a selected video scopes the reset target, and a stale pending ID produces a safe error without a service call; retain the `window.confirm` contract test.
- [x] Run `.venv/bin/python -m unittest tests.test_sidebar tests.test_video_list -v` and confirm the new assertions fail.
- [x] Remove per-card reset rendering; add selected-video Danger zone with exact title when available and always exact ID; retain browser confirmation and existing post-success invalidation.
- [x] Add the pending/current selected-ID equality check immediately before service invocation, preserving URL and pagination state.
- [x] Re-run focused tests and the full suite.

### Task 3: Publish refresh and mutually exclusive outcomes

**Files:**
- Modify: `pages/1_Translate.py`
- Modify: `ui/translation_review.py`
- Modify: `state/common_state.py` only through the existing `reset_video_cache` helper
- Test: `tests/test_translation_review.py`
- Test: `tests/test_streamlit_pages.py`

**Interfaces:**
- Successful Publish callback calls `reset_video_cache(st.session_state)`, keeps `common.selected_video_id`, clears the prompt state, and reruns.
- Publish rendering chooses exactly one primary outcome: `wrote=True` success; valid unchanged result no-change; non-empty issues conflict; exception actionable error.

- [x] Add RED tests for success/cache invalidation, unchanged no-change, stale/412 conflict without no-change text, and exception-only error output.
- [x] Run the focused review/page tests and confirm the new expectations fail.
- [x] Update the successful callback to invalidate only after `result.wrote is True`; change outcome branching so issues take precedence over no-change messaging.
- [x] Re-run the focused tests and the full suite.

### Task 4: Read-only primary source and visible External LLM path

**Files:**
- Modify: `ui/source_selection.py`
- Modify: `ui/llm_package.py`
- Modify: `pages/1_Translate.py` only where callback/UI wiring is required
- Modify: `state/common_state.py` only if the existing selector normalization needs a focused adjustment
- Create: `tests/test_source_selection.py`
- Test: `tests/test_common_state.py`
- Test: `tests/test_streamlit_pages.py`
- Test: `tests/test_translation_draft_handoff.py`
- Test: `tests/test_translation_state.py`
- Test: `tests/test_llm_prompt.py`
- Test: `tests/test_llm_localization_package.py`

**Interfaces:**
- `render_source_selection(...)` displays `Primary source: <name> (<code>)` separately and offers only existing non-primary localizations as optional references; downstream return remains `(primary_code, *selected_reference_codes)`.
- `render_llm_translation_controls(...)` always shows Codex and a three-step External LLM path; uploader remains inactive unless prompt video, exact target tuple, and prompt text match the current selected video.

- [x] Add RED tests for primary exclusion from options, empty/cleared references retaining primary, video-change reset, shared selection, visible three-step copy, inactive uploader, matching prompt activation, stale prompt rejection, and unchanged exact-code validation.
- [x] Run the listed focused source/LLM tests and confirm the new assertions fail.
- [x] Render the primary source as read-only, make the optional reference expander selectable only from non-primary existing localizations, and preserve all state normalization semantics.
- [x] Render the External LLM instructions before checking prompt prerequisites; use a disabled uploader or explicit inactive placeholder with the required guidance while preserving current binding and validation.
- [x] Re-run focused tests and the full suite.

### Task 5: Shared actionable YouTube/OAuth feedback

**Files:**
- Modify: `youtube_account.py` only for narrow setup/callback error context if required
- Modify: `ui/feedback.py`
- Modify: `streamlit_app.py`
- Modify: `pages/1_Translate.py`
- Modify: `pages/2_LLM_prompt.py` only where selected-video errors are rendered
- Modify: `ui/translation_review.py`
- Test: `tests/test_feedback.py` if created
- Test: `tests/test_streamlit_pages.py`
- Test: `tests/test_youtube_localization_api.py`
- Test: `tests/test_translation_review.py`

**Interfaces:**
- Add a small shared classifier/renderer in `ui/feedback.py` that maps setup, auth, callback-port, quota, missing-video, network/API, and generic errors to safe English messages and correct Streamlit severity.
- Keep raw credential/token/environment/path diagnostics out of all messages.

- [x] Add RED tests for missing OAuth file, malformed/wrong Desktop-app JSON, auth/401, callback port 8080, `quotaExceeded`, `YoutubeVideoNotFoundError`, generic network/API errors, severity, and secret redaction.
- [x] Run the focused feedback/API/review tests and confirm the new cases fail.
- [x] Consolidate existing `_render_service_error()` behavior into the shared helper and route bootstrap, selected-video loads, Preview, and Publish through it without broad exception-framework changes.
- [x] Add only the minimal setup error context needed to distinguish missing and malformed OAuth files; preserve automatic refresh/re-auth and never delete `token.json` automatically.
- [x] Re-run focused tests and the full suite.

### Task 6: Actionable Codex error copy

**Files:**
- Modify: `codex_localization_runner.py`
- Modify: `codex_localization_generator.py`
- Modify: `ui/llm_package.py`
- Test: `tests/test_codex_localization_runner.py`
- Test: `tests/test_codex_localization_generator.py`
- Test: `tests/test_codex_localization_end_to_end.py`

**Interfaces:**
- Preserve subprocess isolation, allowlisted environment, timeouts, sanitized stderr, one retry, validation, and no partial merge.
- Failure copy includes status next action, timeout retry guidance, and failed batch number/total, affected codes, reason, retry guidance, and explicit no-partial-merge wording.

- [x] Add RED tests for non-logout status failure guidance and batch failure copy while asserting missing CLI and explicit logout messages remain unchanged and sanitized.
- [x] Run the focused Codex tests and confirm the new expectations fail.
- [x] Update only the user-facing failure strings and batch context propagation; do not change subprocess architecture or add recovery workflows.
- [x] Re-run focused tests and the full suite.

### Task 7: Canonical English documentation and policy

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/README.md`
- Modify: `docs/getting-started.md`
- Modify: `docs/configuration.md`
- Modify: `docs/translate-workflow.md`
- Modify: `docs/llm-localizations.md`
- Modify: `docs/troubleshooting.md`
- Modify: `docs/security.md`
- Modify: `docs/development.md` only for factual English updates
- Modify: `ui/faq.py`

- [x] Update canonical English docs only after Phases 1–3 behavior is green: primary/reference flow, Publish refresh, Reset Danger zone/ETag/no-retry, External LLM three steps, setup recovery, and Codex failures.
- [x] Update `AGENTS.md` so English canonical docs remain source of truth, localized ordinary-user guides live only under `docs/i18n/<locale>/README.md`, development docs stay English-only, and technical identifiers/UI labels remain literal.
- [x] Add the compact 27-locale navigation line to the root README after the locale set is fixed.
- [x] Check requested terms with `git grep` and run `git diff --check`.

### Task 8: 26 self-contained localized guides

**Files:**
- Create exactly one `README.md` under each of: `zh-Hans`, `zh-Hant`, `es`, `hi`, `pt-BR`, `bn`, `ru`, `ja`, `pa-Arab`, `tr`, `vi`, `ar`, `mr`, `te`, `ko`, `ta`, `ur`, `id`, `de`, `fr`, `jv`, `fa`, `it`, `ha`, `gu`, `bho`.

- [x] Add the same compact switcher to all 26 guides, linking to `../../../README.md` and sibling guides with correct relative paths; use native language names and no flags.
- [x] Translate the same self-contained ordinary-user structure in batches of 4–6 locales: requirements, macOS/Linux and Windows PowerShell install, OAuth placement/authorization, Start, Translate, primary/reference source behavior, Codex, External LLM, Preview, Publish, Danger zone/Reset, troubleshooting, security, and License.
- [x] Preserve commands, JSON, filenames, paths, environment names, URLs, BCP-47 codes, identifiers, product names, and literal UI labels exactly; explicitly protect `config/account_client_secrets_main.json`, `token.json`, and `token.pickle` in every guide.
- [x] Verify every guide semantically matches the final English workflow and contains no invented capabilities or locale-specific behavior.
- [x] Verify `find docs/i18n -mindepth 2 -maxdepth 2 -name README.md | wc -l` returns `26` and `docs/development.md`/`docs/superpowers/**` remain English/history-only.

### Task 9: Full verification and review

- [x] Run all focused test commands after their phases and record results.
- [x] Run `.venv/bin/python -m unittest discover -s tests -v` and confirm zero real YouTube/Codex calls.
- [x] Run `.venv/bin/python -m compileall -q streamlit_app.py pages models.py language_catalog.py llm_localization_package.py codex_localization_runner.py codex_localization_generator.py generate_codex_localizations.py services state ui youtube_account.py localizations.py localization_service.py tests`.
- [x] Run `.venv/bin/python -m pip check` and `.venv/bin/python -m compileall` with no broken requirements.
- [x] Run `git diff --check` and inspect the final diff for safety invariants, secret leakage, scope expansion, stale docs, and accidental changes to `docs/superpowers/**`.
- [x] Perform a local Streamlit smoke test without Publish/Reset writes: card placement, Danger zone, primary/reference UI, two generation paths, inactive/active uploader, Preview gating, and safe errors.
- [x] Return a concise Russian report listing Phase changes, closed P0/P1 risks, added tests, exact verification commands/results, total test count, locale list, and unresolved issues only.
