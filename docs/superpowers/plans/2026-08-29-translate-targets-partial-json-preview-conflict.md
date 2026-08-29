# Translate Targets, Partial JSON, and Preview Conflict Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the primary Translate workflow semantically safe, target-selectable, resumable across Codex batches, and able to download its current internal draft before generation finishes.

**Architecture:** Compare Preview with a publish-relevant snapshot containing the video ID, `WRITABLE_SNIPPET_FIELDS`, and `localizations`; keep ETags only as the HTTP `If-Match` precondition. Normalize target codes against the checked-in metadata catalog, keep target selection video-scoped, and run one bounded Codex batch per Streamlit interaction so validated batches merge into the draft and become downloadable checkpoints.

**Tech Stack:** Python, Streamlit, existing localization validation/merge helpers, Codex CLI batch generator, `unittest`/`pytest` repository tests, Markdown documentation.

**Spec:** User-provided implementation request in this task; repository rules in `AGENTS.md`.

## Global Constraints

- Preserve `data/youtube-metadata-languages.json` as the only source of valid video metadata localization codes.
- Keep canonical BCP-47 casing, authoritative default source metadata, optional source references, direct localization JSON, and omitted YouTube localizations.
- Keep Preview read-only, Publish fresh-fetching the video and using `If-Match`, and reject real stale state or HTTP 412 races.
- Keep the supporting LLM Translation prompt page capped at ten targets; only the primary Translate selector may exceed ten.
- Do not add providers, API integrations, dependencies, background workers, push, or unrelated refactoring.
- Update canonical English documentation only after implementation and tests stabilize.

---

### Task 1: Semantic Preview/Publish freshness

**Files:**
- Modify: `localization_service.py`
- Test: `tests/test_localization_service.py`, `tests/test_translation_review.py` when needed

**Interfaces:** Replace `_resource_snapshot()` with a semantic snapshot that includes `id`, only `WRITABLE_SNIPPET_FIELDS`, and `localizations`; retain fresh ETag use in `update_video_localizations(..., if_match=...)` and the existing 412 conflict path.

- [ ] Add failing tests for ETag-only/read-only snippet drift not blocking publish, writable snippet/localization drift blocking with no write, and existing 412 protection.
- [ ] Run the focused tests and confirm the new semantic cases fail for the current raw snapshot.
- [ ] Implement the narrow snapshot comparison and preserve video identity, fresh planning, fresh ETag, and no-write conflicts.
- [ ] Run localization service and review tests.

### Task 2: Target-code normalization and video-scoped state

**Files:**
- Modify: `llm_localization_package.py`, `state/translation_state.py`, `ui/source_selection.py`, `pages/1_Translate.py`, `pages/2_LLM_prompt.py` only as required by existing flow
- Create: `ui/target_selection.py` if a focused component fits current patterns
- Test: `tests/test_llm_localization_package.py`, `tests/test_translation_state.py`, `tests/test_source_selection.py`, `tests/test_streamlit_pages.py`, `tests/test_target_selection.py` if created

**Interfaces:** Generalize target selection normalization to accept `max_count=10` for the supporting prompt page and no limit for primary Translate; expose canonical missing target candidates and persist only selected-video target codes, normalized after source/video changes.

- [ ] Add failing behavioral tests for all-missing defaults, source exclusion, canonical casing, explicit subsets over ten, external-page cap, video reset, and source-change normalization.
- [ ] Run focused tests and confirm the missing target-selection behavior.
- [ ] Implement one shared normalization path and the primary Translate Target languages control immediately after Source languages.
- [ ] Keep the supporting prompt page's first-ten default and maximum-ten validation intact; run focused UI/state tests.

### Task 3: Explicit Codex targets and per-batch checkpoints

**Files:**
- Modify: `codex_localization_generator.py`, `llm_localization_package.py`
- Test: `tests/test_codex_localization_generator.py`, related package tests

**Interfaces:** Extend `generate_missing_localizations(..., target_codes=None, on_batch_completed=None)` so `None` preserves all-missing behavior, an explicit sequence is validated/canonicalized/order-normalized, an empty sequence does no work, and the callback receives `(batch_index, total_batches, codes, batch_document, cumulative_document)` only after validated merge.

- [ ] Add failing tests for explicit target validation, >10 batching, callback contents/order, invalid or failed batches not checkpointing, prior callbacks surviving later failure, and final parser compatibility.
- [ ] Run the generator tests and confirm the current implementation fails these expectations.
- [ ] Implement the smallest backward-compatible target and callback contract while retaining all-or-nothing behavior inside each batch.
- [ ] Run generator and end-to-end tests.

### Task 4: Resumable Translate generation, draft merge, and download

**Files:**
- Modify: `ui/llm_package.py`, `pages/1_Translate.py`, `state/translation_state.py`
- Test: `tests/test_streamlit_pages.py`, `tests/test_translation_state.py`, `tests/test_translation_draft_handoff.py`, related UI tests

**Interfaces:** Add video-scoped generation checkpoint state and one-batch continuation; after each successful batch call `merge_translation_draft()`, preserve earlier checkpoints on later failure, skip valid current-draft targets on retry, invalidate Preview on every merge, and render adjacent `Generate missing translations` / `Download JSON` controls with deterministic `<video-id>-localizations.json` direct-map content.

- [ ] Add failing tests for one-batch return-to-UI behavior, progress/remaining targets, failed-later-batch messaging, retry subtraction, empty-draft download disabled, non-empty current-draft download enabled, and Preview invalidation.
- [ ] Run focused UI/state tests and confirm the current blocking workflow cannot satisfy the acceptance cases.
- [ ] Implement bounded continuation without threads, multiprocessing, new services, or dependencies; make the current draft the sole download source.
- [ ] Run all affected tests and manually inspect the rendered control flow through existing Streamlit test seams.

### Task 5: Canonical documentation and final verification

**Files:**
- Modify only relevant English docs: `README.md`, `docs/getting-started.md`, `docs/translate-workflow.md`, `docs/llm-localizations.md`, `docs/troubleshooting.md`, `docs/development.md` as needed

- [ ] Update docs to describe target selection/defaults, >10 Codex batching, partial checkpoints, resumable Download JSON, retry behavior, Preview invalidation, semantic freshness, fresh fetch, and `If-Match` publish safety.
- [ ] Run focused tests, then `python -m pytest`, syntax/import checks provided by the repository, `git diff --check`, and inspect the complete diff for scope, widget keys, state isolation, safety, documentation alignment, and secrets.
- [ ] Record the final test/check results and commit hash only if a commit was created; do not push.
