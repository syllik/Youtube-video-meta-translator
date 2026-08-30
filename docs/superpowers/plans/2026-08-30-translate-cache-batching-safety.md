# Translate Cache, Continuous Batching, and Checkpoint Safety Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove selected-video YouTube reads from harmless target/source widget reruns, process all selected Codex targets from one Generate click, and keep the last validated cumulative draft downloadable and safe to preview/publish.

**Architecture:** Store one selected-video localization resource in common Streamlit session state, keyed by video ID, and invalidate it only for selected-video changes, explicit refresh, page-cache invalidation, or meaningful fresh operations. Keep target selection video-scoped and authoritative, pass the full remaining target sequence to the existing sequential generator, and merge every validated callback batch into the canonical translation draft before rerendering.

**Tech Stack:** Python 3, Streamlit 1.62, existing YouTube Data API v3 service, `unittest`, `streamlit.testing.v1.AppTest`, Markdown documentation.

**Spec:** `docs/superpowers/specs/2026-08-30-translate-cache-batching-safety-design.md`

## Global Constraints

- Preserve `data/youtube-metadata-languages.json` as the only runtime source of valid video metadata localization codes.
- Keep primary-source/reference semantics, exact direct-map JSON, Preview read-only behavior, fresh Publish/Reset safety reads, fresh ETag/`If-Match`, HTTP 412 no-write handling, and omitted-localization preservation.
- Keep Codex non-interactive, `--ephemeral`, read-only, allowlisted, timeout/retry-protected, provider-key-free, and publish-free.
- Add no threads, multiprocessing, background workers, external queues, new providers, paid Google services, `search.list`, or undocumented YouTube Studio endpoints.
- Do not reset history or push. Production code must have a failing regression test before it is written.

---

### Task 1: Cache the selected video resource and test real widget reruns

**Files:**
- Modify: `state/common_state.py`
- Modify: `pages/1_Translate.py`, `pages/2_LLM_prompt.py`
- Modify: `ui/translation_review.py` only for a narrow fresh-resource cache callback if needed
- Create: `tests/test_streamlit_resource_cache.py`

**Interfaces:**
- Add `get_selected_video_resource(service, state, video_id)` returning a validated cached resource for the exact ID.
- Add `invalidate_selected_video_resource(state, video_id=None)` and make `reset_video_cache()` call it.
- Both workflow pages use the helper for ordinary rendering; Preview/Publish/Reset continue to use their meaningful fresh-read paths.

- [ ] **Step 1: Write the failing pure cache test.**

Use a service that appends requested IDs and returns `{"id": video_id, "snippet": {}, "localizations": {}}`. Call the new helper twice for `video-1`; assert the two resources are equal and the call list is exactly `["video-1"]`.

- [ ] **Step 2: Run the test and confirm RED.**

```bash
python3 -m unittest tests.test_streamlit_resource_cache.VideoResourceCacheTests.test_same_video_resource_is_fetched_once -v
```

Expected: the helper is absent or does not cache yet. Fix a test error, not the production behavior, if the test does not fail for that reason.

- [ ] **Step 3: Add real `streamlit.testing.v1.AppTest` regressions.**

Build an AppTest script around the production `render_target_selection()` and cache helper. Persist the service counter in `st.session_state`; set one target, set `[]` (Clear all), and run once more. Assert the selection remains empty and the selected-resource counter is still `1` after initial load. Build a second script for the prompt-page source/target seam and assert widget changes do not increment the selected-resource counter. Do not replace the production multiselect with a fake widget.

- [ ] **Step 4: Run AppTest before the fix.**

```bash
python3 -m unittest tests.test_streamlit_resource_cache -v
```

The call-count tests must fail against direct page fetches. If empty selection already passes on this checkout, retain it as a guard and do not invent a restore bug.

- [ ] **Step 5: Implement the cache boundary.**

Store `{ "video_id": video_id, "resource": resource }` in common state. Fetch only when absent or bound to another video, verify the returned resource ID, and clear it on explicit invalidation. Replace both page direct fetches. Ensure selected-video changes replace the cache and do not reuse the previous video's resource.

- [ ] **Step 6: Wire meaningful fresh-operation updates and verify.**

If Preview/Publish returns a fresh resource, update only the cache copy through a narrow callback; leave service fresh-fetch and write guards unchanged. Run:

```bash
python3 -m unittest tests.test_streamlit_resource_cache tests.test_streamlit_pages tests.test_streamlit_state tests.test_target_selection tests.test_source_selection tests.test_localization_service tests.test_translation_service tests.test_translation_review -v
```

Review the diff for network calls inside widget rendering and for cache entries crossing video IDs.

### Task 2: Lock target selection semantics across video, source, and empty states

**Files:**
- Modify: `state/translation_state.py`, `ui/target_selection.py`, or `ui/llm_prompt.py` only if a failing regression proves a defect
- Modify: `tests/test_target_selection.py`, `tests/test_streamlit_state.py`, `tests/test_streamlit_resource_cache.py`

**Interfaces:**
- `sync_translation_target_selection()` initializes all missing targets only when `target_video_id` changes and otherwise returns the normalized persisted explicit selection, including `()`.
- Source normalization can remove newly excluded source codes but cannot restore other user-removed targets.
- The prompt page keeps its first-ten default and ten-target limit; primary Translate remains uncapped.

- [ ] **Step 1: Add state-first regressions.**

Assert first sync for `video-1` returns `("de", "fr")`; set `selected_target_codes = ()`; assert a same-video sync returns `()`. Assert a new video initializes from that video's missing codes, and source exclusion removes only the newly source code.

- [ ] **Step 2: Run focused tests and verify RED where applicable.**

```bash
python3 -m unittest tests.test_target_selection tests.test_streamlit_state tests.test_llm_prompt -v
```

If an existing case already passes, keep it as a regression and make no speculative state change.

- [ ] **Step 3: Implement only a proven initialization/normalization fix.**

Preserve the current video ID boundary and canonical catalog ordering. If AppTest exposes an ambiguity between uninitialized and empty, store an explicit initialization marker; never treat empty as a request to reinitialize defaults.

- [ ] **Step 4: Re-run target and AppTest coverage.**

```bash
python3 -m unittest tests.test_target_selection tests.test_llm_prompt tests.test_llm_localization_package tests.test_streamlit_resource_cache -v
```

### Task 3: Remove UI one-batch truncation and preserve every validated checkpoint

**Files:**
- Modify: `ui/llm_package.py`
- Modify: `state/translation_state.py` only if a failing checkpoint test proves a state defect
- Modify: `tests/test_llm_package_ui.py`, `tests/test_translation_draft_handoff.py`, `tests/test_translation_state.py`
- Modify: `codex_localization_generator.py` only if existing callback/validation tests expose a Critical/High defect

**Interfaces:**
- One `render_llm_translation_controls()` Generate action passes all `remaining_codes` to one `generate_missing_localizations()` call.
- The existing `on_batch_completed(index, total, codes, batch_document, cumulative_document)` callback merges only the validated batch and records progress.
- The canonical download source is `state["draft"]`; retries derive remaining codes from valid draft entries.

- [ ] **Step 1: Add the failing 25-target one-click test.**

Use 25 catalog targets and a generator seam that records `kwargs["target_codes"]`, invokes the callback for ordered `(0..9)`, `(10..19)`, `(20..24)` batches, and returns the cumulative document. Assert the generator was called once with all 25 codes and the draft contains 25 validated entries.

- [ ] **Step 2: Run RED against the current slice.**

```bash
python3 -m unittest tests.test_llm_package_ui.LlmPackageUiTests.test_one_generate_click_processes_all_remaining_batches -v
```

Expected: the current UI passes only `remaining_codes[:LLM_BATCH_SIZE]`.

- [ ] **Step 3: Add the failing late-failure/download test.**

Have the generator callback merge batches 1 and 2, then raise `CodexGenerationError` for batch 3. Assert after the UI returns that earlier entries remain, failed entries are absent, status is idle, Preview is invalid, and the rendered Download data equals the exact 20-entry draft rather than the pre-operation snapshot. Assert a retry requests only the remaining codes.

- [ ] **Step 4: Run the focused UI tests and verify RED.**

```bash
python3 -m unittest tests.test_llm_package_ui tests.test_translation_draft_handoff tests.test_translation_state -v
```

- [ ] **Step 5: Implement the minimal UI fix.**

Remove only the UI slice; pass complete `remaining_codes` with `batch_size=LLM_BATCH_SIZE`. Use callback index plus stored completed count for progress. Keep `merge_translation_draft()` as the checkpoint boundary. On generation failure, store the error, restore idle, and rerun so Download renders from the last valid draft; do not retry automatically. Serialize Download from `state.get("draft")` at render time.

- [ ] **Step 6: Verify batching, failure, retry, and download behavior.**

```bash
python3 -m unittest tests.test_llm_package_ui tests.test_translation_draft_handoff tests.test_translation_state tests.test_codex_localization_generator tests.test_codex_localization_end_to_end -v
```

Review `codex_localization_generator.py` and `codex_localization_runner.py` for only Critical/High issues: exact targets, invalid JSON, duplicate/missing languages, timeout/retry, safe output, ephemeral read-only execution, and no publishing.

### Task 4: Recheck publish safety and update canonical English documentation

**Files:**
- Modify: `localization_service.py` only if a focused safety regression proves a high-impact defect
- Modify: `tests/test_localization_service.py`, `tests/test_translation_service.py`, `tests/test_translation_review.py` only for missing required assertions
- Modify: `docs/translate-workflow.md`, `docs/llm-localizations.md`, and other English docs only where current wording is false

- [ ] **Step 1: Run safety regressions before edits.**

```bash
python3 -m unittest tests.test_localization_service tests.test_translation_service tests.test_translation_review tests.test_translation_state -v
```

Confirm ETag-only/read-only drift does not create a false semantic conflict, writable/localization drift creates a no-write conflict, draft mutation invalidates Preview, omitted localizations are preserved, and HTTP 412 remains no-write.

- [ ] **Step 2: Update docs after behavior stabilizes.**

Document that harmless widget reruns use the cached resource, explicit Refresh/Preview/Publish/Reset have fresh-read semantics, one Generate click runs all ten-sized sequential batches, each successful batch invalidates Preview, later failure preserves checkpoints, retry skips valid draft entries, Download uses the current draft, and empty target selection is authoritative.

- [ ] **Step 3: Verify docs and dependency constraints.**

```bash
rg -n -i 'one batch|click.*again|Cloud Translation|google-cloud-translate|translation.googleapis.com|Vertex AI|Gemini API|search\.list|provider API key' README.md docs requirements.txt *.py pages ui state services tests
python3 -m unittest tests.test_streamlit_pages tests.test_language_catalog tests.test_youtube_languages tests.test_generate_codex_localizations -v
```

### Task 5: Full verification and cyclical Critical/High review

**Files:**
- Modify only files justified by failing regressions in Tasks 1–4.

- [ ] **Step 1: Run the focused acceptance suite.**

```bash
python3 -m unittest tests.test_streamlit_resource_cache tests.test_target_selection tests.test_streamlit_state tests.test_llm_package_ui tests.test_translation_draft_handoff tests.test_translation_state tests.test_codex_localization_generator tests.test_codex_localization_runner tests.test_localization_service tests.test_translation_service tests.test_translation_review -v
```

- [ ] **Step 2: Reproduce the original flows with AppTest.**

Verify one initial selected-video read, zero reads for target/source edits and Clear all, one new read on video switch, one-click 10/10/5 generation, batch-3 failure retaining batch-1/2 Download, and retry requesting only remaining targets.

- [ ] **Step 3: Run complete tests and static checks.**

```bash
python3 -m unittest discover -v
python3 -m compileall -q .
git diff --check
```

Inspect requirements/imports for forbidden provider SDKs and the worktree for generated secrets or temporary files.

- [ ] **Step 4: Review the complete diff for Critical/High findings.**

Check cache/video identity leakage, target repopulation, stale Download, duplicate generation, lost checkpoints, Preview/Publish mismatch, accidental writes, omitted-localization loss, widget-triggered API calls, unsafe runner behavior, and false success after failure. If any finding remains, add its failing regression, implement one minimal fix, repeat focused/full tests, reproduce, and review again.

- [ ] **Step 5: Final verification before handoff.**

Run the complete suite and `git diff --check` again immediately before reporting. Provide the worktree path, branch, commits, exact test count, and any limitation. Do not push or claim merge readiness.
