# Unified Translation Workflow Implementation Plan

> **For agentic workers:** This plan is executed inline in the current task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the separate Manual/LLM user workflows with one `Translate` workflow that shares a video-scoped source model across Codex generation, external-LLM prompts, JSON editing, validation, Preview, and Publish.

**Architecture:** Keep the proven localization service and editor pipeline, but make its Streamlit state universal and video-scoped. Add pure helpers that extract the default primary source and selected existing-localization references, filter targets defensively, and build one explicit package consumed by both Codex and prompt flows. Keep the supporting `LLM Translation prompt` page as a thin view over the same state namespace.

**Tech Stack:** Python, Streamlit, YouTube Data API v3, `unittest`/`pytest` test suite, native Streamlit expanders and controls.

**Spec:** User-provided unified translation workflow requirements in the task attachment.

## Global Constraints

- Keep `defaultLanguage` as the authoritative primary source.
- Use only live YouTube catalog codes and preserve their canonical casing.
- Pass selected existing localizations only as optional reference sources.
- Exclude every selected source code from target languages.
- Preserve Preview non-writing, current-state Publish, omitted-localization preservation, validation, retries, and API-key-free Codex execution.
- Keep active repository documentation and UI copy in English.
- Do not add API-key LLM integration, custom Streamlit components, unrelated refactors, or push.

### Task 1: Establish source model and shared state contracts

**Files:**
- Modify: `state/llm_state.py`, `state/manual_state.py`, `state/common_state.py`
- Modify: `llm_localization_package.py`
- Test: `tests/test_llm_localization_package.py`, `tests/test_manual_streamlit_state.py`, `tests/test_common_state.py`

- [ ] Add failing tests for extracting `defaultLanguage` plus existing localization candidates, requiring the default as primary, normalizing selected references per video, and clearing source/editor/prompt/upload/preview state on video change.
- [ ] Implement a shared source-selection namespace keyed to the current selected video, with default-only automatic behavior and deterministic normalization.
- [ ] Add pure source-package helpers that accept explicit selected source codes and produce primary/reference metadata from the selected video.
- [ ] Run the focused package/state tests and keep them green.

### Task 2: Make targets and packages source-aware

**Files:**
- Modify: `llm_localization_package.py`, `codex_localization_generator.py`, `codex_localization_runner.py`
- Test: `tests/test_llm_localization_package.py`, `tests/test_codex_localization_generator.py`, `tests/test_codex_localization_end_to_end.py`, `tests/test_codex_localization_runner.py`

- [ ] Add failing tests proving selected source codes cannot become targets and every Codex batch receives the same primary/reference context.
- [ ] Implement explicit `source.primary`, `source.references`, `targetLanguages`, `expectedLanguageCodes`, and `expectedCount` package semantics while retaining backward-compatible default-source CLI behavior.
- [ ] Update Codex instructions to distinguish authoritative primary metadata from verified reference translations and require exact direct JSON output.
- [ ] Run all package/generator/runner focused tests.

### Task 3: Unify the Streamlit workflow and editor state

**Files:**
- Modify: `streamlit_app.py`, `pages/1_Manual_translate.py`, `pages/2_LLM_translate.py`, `pages/3_LLM_prompt.py`
- Modify: `ui/llm_package.py`, `ui/llm_prompt.py`, `ui/manual_editor.py`
- Modify: `state/manual_state.py`, `state/llm_state.py`
- Test: `tests/test_streamlit_pages.py`, `tests/test_manual_streamlit_state.py`, `tests/test_llm_prompt.py`

- [ ] Add failing source-level/UI harness tests for a single `Translate` page, shared source selection, native expanders, upload/generation handoff, and prompt links back to `Translate`.
- [ ] Rebuild page 1 as `Translate`, remove the user-facing Manual page and navigation link, and use one universal editor state for Codex/generated/uploaded/manual JSON.
- [ ] Keep prompt-specific target/upload state separate, but use the shared source selection and one editor/preview/publish namespace.
- [ ] Render Source languages, Generate translations, Localization JSON, and Preview & publish as native expanders without a manual/LLM mode tab.
- [ ] Run focused Streamlit/state tests and fix widget-key or rerun regressions.

### Task 4: Update sidebar and active documentation

**Files:**
- Modify: `ui/video_list.py`, `ui/sidebar.py`
- Modify: `AGENTS.md`, `README.md`, `docs/README.md`, `docs/getting-started.md`, `docs/llm-localizations.md`, `docs/manual-localizations.md`, `docs/troubleshooting.md`, `docs/development.md`, and any directly stale active links.
- Test: `tests/test_video_list.py`, `tests/test_sidebar.py`, `tests/test_streamlit_pages.py`

- [ ] Add failing structural tests for a full-width Select button below video details and absence of the old two-workflow navigation/copy in active docs/UI.
- [ ] Move Select below the card details with `use_container_width=True`, preserving selected primary styling and disabled behavior.
- [ ] Update active docs and `AGENTS.md` to describe `Translate` plus supporting prompt page, shared source semantics, video-change reset, and identical Codex/external-LLM source context. Retain historical design artifacts unless they are active links.
- [ ] Prove stale active terminology and dead workflow links are absent with targeted searches.

### Task 5: Regression validation and final review

**Files:**
- Modify: focused tests as required by the implementation; no unrelated files.

- [ ] Run focused tests for source extraction, state reset, package/prompt/Codex batches, sidebar, and unified pages.
- [ ] Run `python -m pytest` and syntax/import validation used by the repository.
- [ ] Run `git diff --check`, inspect `git diff`, verify stale terminology, source/target exclusion, duplicate widget keys, safe Preview/Publish behavior, and preserved localizations.
- [ ] Fix regressions, stage only scoped files, and create one commit: `feat: unify translation workflow and source context`.
- [ ] Do not push.
