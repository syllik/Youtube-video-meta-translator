# Critical Review Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan must be executed without real Codex translations, real model calls, YouTube writes, or unnecessary network requests.

**Goal:** Make the current Codex-to-editor-to-Preview-to-Publish path safe against wrong-video drafts, stale YouTube state overwrites, secret leakage, non-canonical language keys, and indefinitely hung Codex subprocesses.

**Architecture:** Keep the existing two-workflow Streamlit architecture and shared localization service. Add video-scoped editor widget identity, explicit publish-time freshness validation with a conditional YouTube update, live-catalog canonical-code resolution, and bounded/sanitized Codex subprocess execution. Preserve the current all-or-nothing batch generator and omitted-localization merge behavior.

**Tech Stack:** Python standard library, Streamlit session state, `subprocess`, Google YouTube Data API v3, existing `unittest` tests, and the installed local Codex CLI.

**Spec:** Phase 1 findings from the 2026-08-28 critical review request, together with `docs/superpowers/specs/2026-08-28-llm-prompt-upload-flow-design.md` and `AGENTS.md`.

## Global Constraints

- Do not add a third workflow, provider integration, API-key setting, or dependency.
- The live authenticated YouTube `i18nLanguages.list` catalog remains the only source of valid localization codes and their canonical spelling.
- Existing YouTube localizations omitted from submitted JSON must remain in every update payload.
- Invalid, incomplete, stale, or conflicted data must never reach `videos.update`.
- Automatic generation remains generation-only until the user reviews the editable JSON and explicitly previews and publishes it.
- Keep changes limited to the five Phase 1 findings; do not refactor unrelated UI, pagination, OAuth, or batching code.
- All regression tests remain credential-free and must use fakes/mocks; do not run a real Codex translation or a real YouTube write.

---

### Task 1: Isolate automatic LLM editor state by selected video

**Finding addressed:** CRITICAL wrong-video publication caused by the fixed `llm-localizations-json` Streamlit key surviving a video switch after `sync_llm_video` clears the namespaced form state.

**Files:**
- Modify: `ui/manual_editor.py`
- Modify: `ui/llm_package.py`
- Modify: `tests/test_manual_streamlit_state.py`
- Modify: `tests/test_streamlit_state.py`
- Modify: `docs/llm-localizations.md`
- Modify: `README.md`

**Interfaces:**
- Add one shared helper, such as `localizations_editor_key(widget_prefix: str, video_id: Optional[str]) -> str`, and use it from both `render_manual_editor` and every LLM JSON handoff.
- For a selected video, the returned key must include the video ID. Generation, upload, and editor rendering must use the identical key.
- Before applying a completed automatic result, verify that `state["bound_video_id"]` still equals `video_resource["id"]`; discard a result produced for a no-longer-active video and leave the editor unchanged when it does not.

- [ ] **Step 1: Add the failing state/widget regression.**

  Model Streamlit's persistent top-level widget dictionary, not only the namespaced state:

  1. Render or generate for `video-1` and place its JSON in the LLM editor widget key.
  2. Run `sync_llm_video(state, "video-2")`, which must clear the LLM form state.
  3. Render the editor for `video-2`.
  4. Assert that the editor reads an empty/new `video-2` key and does not repopulate `state["raw_json"]` from the `video-1` key.

  Add a second regression where a fake generator changes `state["bound_video_id"]` before returning; assert that its result is not applied to the editor.

- [ ] **Step 2: Run the focused tests and verify the regressions fail on current behavior.**

  Run:

  ```bash
  python3 -m unittest tests.test_manual_streamlit_state tests.test_streamlit_state
  ```

  Expected before implementation: the new video-switch case observes the old fixed widget value, and the active-video guard case applies a result after the bound video changes.

- [ ] **Step 3: Implement the minimal video-scoped key handoff.**

  Use the shared helper in `render_manual_editor`, `apply_generated_localizations` callers, and the valid-upload handoff. Keep the existing manual workflow's intentional behavior of retaining a manually entered JSON draft across video selection, but ensure LLM state clearing cannot be undone by an old widget key. Do not reuse a completed automatic result after the active video changes.

- [ ] **Step 4: Run the focused tests and the affected workflow tests.**

  Run:

  ```bash
  python3 -m unittest tests.test_manual_streamlit_state tests.test_streamlit_state tests.test_streamlit_pages
  ```

  Expected: PASS, including the existing upload/generation handoff tests and the new wrong-video protection cases.

- [ ] **Step 5: Align the user-facing workflow documentation.**

  State that automatic JSON is bound to the selected video and is discarded when the selected video changes; the user must generate or upload again for the new video. Keep documentation in English and do not describe the internal widget key.

**Dependencies:** None. Complete before Task 2 because both tasks touch the editor publish boundary.

---

### Task 2: Reject stale Preview state before YouTube publication

**Findings addressed:** CRITICAL stale Preview/live-state overwrite; the current `manual_fingerprint` covers only `(video_id, raw_json)`, while `publish_localizations` fetches a newer video and writes it without comparing it to the Preview state.

**Files:**
- Modify: `localization_service.py`
- Modify: `services/manual_localization_service.py`
- Modify: `services/youtube_service.py`
- Modify: `youtube_account.py`
- Modify: `ui/manual_editor.py`
- Modify: `tests/test_localization_service.py`
- Modify: `tests/test_manual_localization_service.py`
- Modify: `tests/test_localization_api.py`
- Modify: `tests/test_youtube_localization_api.py`
- Modify: `tests/test_manual_streamlit_state.py`
- Modify: `docs/manual-localizations.md`
- Modify: `README.md`

**Interfaces:**
- Extend the publish boundary with an optional expected Preview resource/version, for example `publish_localizations(..., expected_video: Optional[Mapping[str, Any]] = None)` and the corresponding `ManualLocalizationService.publish` argument.
- Keep the existing `LocalizationOperationResult` shape usable by the UI. A stale-state result must contain `wrote=False`, an actionable conflict issue, and no update payload.
- Pass the Preview resource from `render_manual_editor` into the publish service. A matching Preview remains eligible; a mismatch requires a new Preview.
- Pass the current resource ETag to `YoutubeApi.update_video_localizations`/`YoutubeService.update_video_localizations` when available and send it as a conditional `If-Match` request header. Treat a failed precondition as a no-write conflict.

- [ ] **Step 1: Add the failing stale-state tests.**

  Cover both levels:

  1. Preview `video-1` with submitted `de=new` while YouTube contains `de=old`.
  2. Change the fake current YouTube resource to `de=collaborator` without changing the local JSON.
  3. Publish with the stored Preview resource.
  4. Assert that the service returns a conflict, performs no `videos.update`, and does not treat the new collaborator value as a value to overwrite.

  Also cover a matching Preview that still writes once and preserves an omitted existing localization, plus an API precondition failure that is surfaced as a no-write conflict.

- [ ] **Step 2: Run the focused service/API tests and verify they fail on current behavior.**

  Run:

  ```bash
  python3 -m unittest tests.test_localization_service tests.test_manual_localization_service tests.test_localization_api tests.test_youtube_localization_api
  ```

  Expected before implementation: the stale-state case currently writes the submitted value over the collaborator's newer value.

- [ ] **Step 3: Implement freshness validation at the publish boundary.**

  Record the relevant fetched YouTube state in the Preview result. On publish, validate the raw JSON again, fetch the current complete resource, compare the Preview resource's relevant `snippet`/`localizations` state (and ETag when present) with the current resource, and return a conflict before building or sending a write when they differ. Build the normal merged payload only from the current resource after the freshness check. Preserve omitted current localizations exactly as before.

- [ ] **Step 4: Add the conditional update guard and UI invalidation.**

  Attach the current resource ETag to the update request when the API supplies one. If YouTube rejects the precondition, return/store a conflict result so `manual_can_publish` becomes false and the UI asks the user to Preview again. Do not leave the old valid-looking Preview eligible after a conflict.

- [ ] **Step 5: Run all affected tests.**

  Run:

  ```bash
  python3 -m unittest tests.test_localization_service tests.test_manual_localization_service tests.test_localization_api tests.test_youtube_localization_api tests.test_manual_streamlit_state
  ```

  Expected: PASS, including no-write conflict behavior, matching publish, omitted-localization preservation, and the existing explicit Preview-before-Publish flow.

- [ ] **Step 6: Align the documentation.**

  Document that Publish revalidates the current YouTube resource and refuses to overwrite changes made after Preview; the recovery is to fetch/Preview again. Keep the omitted-localization preservation statement.

**Dependencies:** Task 1 is earlier only because of the shared editor file. This task must be complete before final end-to-end verification.

---

### Task 3: Restrict the Codex child environment to non-secret runtime/auth context

**Finding addressed:** CRITICAL secret exposure: `_codex_environment` copies the complete parent environment and removes only `OPENAI_API_KEY` and `CODEX_API_KEY`, leaving application/API/OAuth/CI secrets available to a model-controlled read-only subprocess.

**Files:**
- Modify: `codex_localization_runner.py`
- Modify: `tests/test_codex_localization_runner.py`
- Modify: `docs/llm-localizations.md`
- Modify: `docs/security.md`

**Interfaces:**
- Keep `_codex_environment(environ=None)` as the runner's single environment boundary.
- Preserve only the variables required to locate and authenticate the local CLI and run it (`PATH`, home/profile variables, `CODEX_HOME`, temporary-directory/runtime locale variables as applicable to the host). Do not pass arbitrary application, cloud, OAuth, CI, package-manager, or secret variables.
- Keep the existing `CODEX_HOME` authentication behavior; do not replace it with an API key.

- [ ] **Step 1: Add the failing environment-isolation test.**

  Pass a synthetic environment containing `PATH`, `HOME`, `USERPROFILE`, `CODEX_HOME`, `YOUTUBE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `GITHUB_TOKEN`, `AWS_SECRET_ACCESS_KEY`, `APP_SECRET`, `OPENAI_API_KEY`, and `CODEX_API_KEY`. Assert that required runtime/auth variables survive and every application/secret variable is absent.

- [ ] **Step 2: Run the runner tests and verify the new isolation test fails on current behavior.**

  Run:

  ```bash
  python3 -m unittest tests.test_codex_localization_runner
  ```

  Expected before implementation: the current copy-all-then-pop behavior retains `YOUTUBE_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, and arbitrary secrets.

- [ ] **Step 3: Implement the allowlisted child environment.**

  Build the child environment from an explicit safe allowlist, preserving only the local Codex executable/auth/runtime requirements. Keep `--ignore-user-config` and the read-only sandbox flags. Do not print the environment or include secret values in error messages.

- [ ] **Step 4: Run runner and CLI-generation tests.**

  Run:

  ```bash
  python3 -m unittest tests.test_codex_localization_runner tests.test_codex_localization_generator tests.test_codex_localization_end_to_end tests.test_generate_codex_localizations
  ```

  Expected: PASS, including authenticated-context variables still being present in the child and no API key/call-to-publish behavior.

- [ ] **Step 5: Update the security documentation.**

  Replace the claim that only two API-key variables are removed with the actual restricted-environment rule. Explain that local Codex authentication is retained through its dedicated local context while application secrets are not inherited.

**Dependencies:** None.

---

### Task 4: Resolve incoming language keys through the live catalog's exact casing

**Finding addressed:** HIGH invalid BCP-47/canonical-key handling: `_normalize_language_code` uppercases every non-primary subtag, turning real script tags such as `zh-Hans` and `sr-Latn` into `zh-HANS` and `sr-LATN`; the publish payload can then contain both canonical and case-fold-equivalent keys.

**Files:**
- Modify: `localizations.py`
- Modify: `llm_localization_package.py` only if exact expected-code re-keying needs a defensive adjustment
- Modify: `tests/test_localizations.py`
- Modify: `tests/test_llm_localization_package.py`
- Modify: `tests/test_localization_service.py`
- Modify: `docs/manual-localizations.md`

**Interfaces:**
- Replace heuristic subtag casing with a case-insensitive lookup from each incoming key to the exact code supplied by the live `supported_language_codes` collection.
- Reject duplicate incoming keys after case-folding against the live catalog.
- Ensure `ParsedLocalizations.entries`, diff keys, merged localization maps, and final `videos.update` payloads use the catalog's exact spelling.

- [ ] **Step 1: Add failing casing and collision regressions.**

  Add cases for:

  - `pt-br` resolving to exact catalog code `pt-BR`;
  - `zh-hans` and `sr-latn` resolving to exact catalog codes `zh-Hans` and `sr-Latn`;
  - an existing canonical `zh-Hans` plus submitted `zh-hans` producing one changed `zh-Hans` entry, not an added `zh-HANS` entry and not two payload keys;
  - two submitted spellings of the same code being rejected after case-folding.

  Assert the final payload keys, not only `ParsedLocalizations.is_valid`.

- [ ] **Step 2: Run parser/package tests and verify the script-subtag assertions fail on current behavior.**

  Run:

  ```bash
  python3 -m unittest tests.test_localizations tests.test_llm_localization_package tests.test_localization_service
  ```

  Expected before implementation: script subtags are stored/published with all-uppercase non-primary subtags, and the canonical-existing collision produces two equivalent keys.

- [ ] **Step 3: Implement live-catalog canonical resolution.**

  Use one case-folded catalog map for validation and exact output keys. Keep the catalog's own spelling authoritative; do not infer casing from subtag position and do not introduce a static language map.

- [ ] **Step 4: Run the complete localization path tests.**

  Run:

  ```bash
  python3 -m unittest tests.test_localizations tests.test_llm_localization_package tests.test_codex_localization_runner tests.test_codex_localization_generator tests.test_codex_localization_end_to_end tests.test_localization_service tests.test_localization_api
  ```

  Expected: PASS with exact casing retained from live-catalog fixtures through batch result, editor validation, diff, merge, and update payload.

- [ ] **Step 5: Update the manual-language documentation.**

  State that input keys are matched case-insensitively but emitted using the exact live YouTube catalog spelling, including script and regional subtags.

**Dependencies:** None; run before final end-to-end verification.

---

### Task 5: Bound Codex login and batch subprocess execution

**Finding addressed:** HIGH indefinite hang: both `check_codex_login` and `run_codex_batch` call `subprocess.run` without a timeout, so a stalled login/auth/model process blocks the synchronous Streamlit request and the retry loop cannot recover.

**Files:**
- Modify: `codex_localization_runner.py`
- Modify: `tests/test_codex_localization_runner.py`
- Modify: `tests/test_codex_localization_generator.py`
- Modify: `tests/test_manual_streamlit_state.py`
- Modify: `docs/llm-localizations.md`
- Modify: `docs/troubleshooting.md`

**Interfaces:**
- Add explicit bounded timeout constants for login status and one batch execution.
- Pass `timeout=` to both subprocess calls.
- Convert `subprocess.TimeoutExpired` into `CodexLocalizationError` with a safe, actionable message; preserve the existing generator retry policy for a timed-out batch and never apply partial results.

- [ ] **Step 1: Add failing timeout tests.**

  Make a fake `run` raise `subprocess.TimeoutExpired` for login and batch calls. Assert that each public runner function raises `CodexLocalizationError`, that the batch error identifies a timeout without exposing command output, and that the generator retries a timed-out batch exactly according to `retry_count` before raising `CodexGenerationError`.

- [ ] **Step 2: Run runner/generator tests and verify the timeout assertions fail on current behavior.**

  Run:

  ```bash
  python3 -m unittest tests.test_codex_localization_runner tests.test_codex_localization_generator
  ```

  Expected before implementation: no timeout keyword is passed, and `TimeoutExpired` escapes as an unhandled exception instead of following the Codex error/retry path.

- [ ] **Step 3: Implement bounded execution and safe timeout conversion.**

  Pass the constants to `subprocess.run`, catch `TimeoutExpired` around both calls, and raise the existing domain error. Do not increase retry count or return any partial `merged` mapping after a timed-out batch.

- [ ] **Step 4: Run the affected UI and CLI tests.**

  Run:

  ```bash
  python3 -m unittest tests.test_codex_localization_runner tests.test_codex_localization_generator tests.test_codex_localization_end_to_end tests.test_generate_codex_localizations tests.test_manual_streamlit_state
  ```

  Expected: PASS, including UI error handling without editor mutation or rerun after generation failure.

- [ ] **Step 5: Document bounded execution and recovery.**

  Explain that a timeout leaves the editor unchanged; the user can authenticate/check the local CLI and retry the generation. Do not document real translation smoke tests as part of automated verification.

**Dependencies:** None.

---

## Explicit execution order

1. Task 1 — isolate LLM editor state by video.
2. Task 2 — add Preview/live-state conflict protection and conditional publish.
3. Task 3 — restrict the Codex child environment.
4. Task 4 — preserve exact live language-code casing.
5. Task 5 — add subprocess timeouts and timeout-aware retries.
6. Run the final verification below and review the complete diff for scope.

## Final verification

- Run the complete credential-free test suite:

  ```bash
  python3 -m unittest discover -s tests
  ```

- Run a compilation check without importing or invoking external services:

  ```bash
  python3 -m compileall -q .
  ```

- Verify the local Codex CLI contract without starting a translation:

  ```bash
  codex --version
  codex exec --help
  ```

- Run `git diff --check`.
- Confirm no test invokes a real Codex translation, model call, YouTube update, or unnecessary network request.
- Confirm a failed batch leaves no generated editor document, a stale Preview leaves `videos.update` untouched, and a successful update contains all current omitted localizations.

## Measurable acceptance criteria

- For a generated document for video A, switching to video B leaves no A-specific JSON, upload context, Preview, or publish eligibility available under B's editor; a generated result that completes after the bound video changes is discarded.
- Every batch includes each requested live-catalog target exactly once; one failed or timed-out batch prevents the merged document from reaching the editor.
- `pt-BR`, `zh-Hans`, and `sr-Latn` remain exactly those spellings from live catalog through package/schema, generated result, editor validation, diff, merge, and final `videos.update` payload; equivalent keys cannot coexist.
- Every Codex login and batch subprocess has an explicit timeout, timeout failures are surfaced as domain errors, and the configured retry count is honored without partial success.
- The Codex child receives the local executable/auth runtime context but not `YOUTUBE_API_KEY`, OAuth credential paths, cloud/CI tokens, or arbitrary application secrets.
- Preview remains read-only and records the fetched YouTube state. If relevant YouTube state changes before Publish, Publish returns a conflict, performs zero writes, disables the stale publish path, and requires a new Preview.
- With unchanged YouTube state, Publish revalidates the editor JSON, writes at most once, and the payload is built from the current resource while preserving every omitted existing localization.
- The end-to-end safety chain is covered by tests from `Codex/package → batches → merge → editor/session state → validation → Preview → Publish → preserved existing YouTube localizations`.
