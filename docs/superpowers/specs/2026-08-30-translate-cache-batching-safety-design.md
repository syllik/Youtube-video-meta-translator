# Translate Cache, Continuous Batching, and Checkpoint Safety Design

## Goal

Make target editing independent of YouTube reads after the selected video resource is loaded, process the complete selected Codex queue from one Generate action, and keep every validated checkpoint as the canonical downloadable and previewable draft.

## Scope and constraints

- The current selected-video baseline is the existing checkout at `e52b49e`; no history reset or push is part of this work.
- `data/youtube-metadata-languages.json` remains the only runtime source of valid video metadata localization codes.
- The existing sequential Codex runner, `--ephemeral` execution, read-only sandbox, environment allowlist, exact schema, timeout, retry, and safe error handling remain in place.
- No threads, multiprocessing, background workers, queues, new translation providers, paid Google services, provider API keys, `search.list`, or undocumented YouTube Studio endpoints are added.
- Preview stays read-only. Publish continues to validate, fetch fresh state, preserve omitted localizations, use fresh ETag with `If-Match`, and treat HTTP 412 as a no-write conflict. Reset remains a separate destructive operation.

## Architecture

### Video-resource boundary

Common session state owns a cache entry for the selected video's full localization resource. The entry is keyed by the exact video ID and contains the resource returned by `get_video_with_localizations`. A page asks for the resource through one helper:

```text
get_selected_video_resource(service, session_state, video_id)
```

The helper fetches when there is no entry or the cached entry belongs to another video, then validates that the returned resource has the requested ID before storing it. A normal Streamlit rerun caused by target/source widgets reads the same entry and performs no selected-video YouTube read. A selected-video change replaces the entry; an explicit sidebar refresh clears it. Page-list cache invalidation also clears it so the next selected-video render obtains current state.

Preview, Publish, and Reset retain their own meaningful fresh-read behavior. A fresh resource returned by Preview/Publish may update the selected-resource cache through the page callback so a rerun does not immediately re-read the same video. A successful Publish or Reset invalidates normal page-derived cache before rerendering.

### Target selection state

The primary Translate target state is scoped by `target_video_id`. On the first render for a new video, it initializes once to all currently missing catalog languages after source exclusions. On later reruns, including an empty widget value, it normalizes only the persisted explicit selection against current catalog candidates. Empty is a valid authoritative selection and never triggers default initialization.

Changing source selection removes codes that are now source languages, but does not restore other codes the user previously removed. Changing video creates a new selection and clears translation draft/Preview state through the existing video-binding rules. Widget keys remain stable for the same video and source set.

The supporting LLM Translation prompt page uses the same cached resource and source state, while its existing first-ten default and ten-target limit remain unchanged. The primary Translate selector remains uncapped; the generator supplies batches of ten.

### Continuous generation and checkpoints

The primary UI computes the selected canonical codes and subtracts valid entries already present in the current draft. It passes the full remaining sequence to `generate_missing_localizations` once per Generate click. The generator already partitions the sequence into ordered batches and validates each result before merging it into its local cumulative document.

After each validated generator batch, `on_batch_completed` is the transaction boundary:

1. merge only that validated batch into `state["draft"]`;
2. preserve all earlier valid entries and external-upload entries;
3. record completed codes, completed batch count, and last batch codes;
4. clear any generation error; and
5. invalidate the Preview fingerprint through the existing draft merge helper.

If a later batch fails, the failed batch never reaches the callback. The UI records the error, restores idle status, and reruns so the controls are rendered from the last valid cumulative draft. A retry recomputes remaining selected codes from that draft and therefore starts after the completed checkpoints without regenerating them.

Progress shown during a retry combines the already completed batch count with the local callback index. A target-selection change intentionally starts a new generation bookkeeping scope while retaining the draft; valid draft entries are still skipped.

### Download and Preview invariant

`state["draft"]` is the sole internal source for Download JSON. It is a direct UTF-8 localization map with no wrapper fields. The UI always serializes the current draft at render time, and every generation success or failure reruns before returning to idle controls. Therefore the download is disabled for `{}`, equals the cumulative draft after each successful checkpoint, and remains equal to the last valid cumulative draft after a later failure.

Any draft mutation invalidates the Preview fingerprint. Preview displays the exact draft used for its result, and Publish is enabled only while that Preview fingerprint is current. Publish still compares the fresh resource with the Preview resource using the existing publish-relevant snapshot and never writes after a stale-state or 412 conflict.

## Files and responsibilities

- `state/common_state.py`: selected-resource cache and explicit invalidation boundary.
- `pages/1_Translate.py`, `pages/2_LLM_prompt.py`: obtain selected resources through the cache and wire meaningful fresh-operation cache updates.
- `state/translation_state.py`, `ui/target_selection.py`: video-scoped authoritative target semantics and Preview invalidation preservation.
- `ui/llm_package.py`: full-queue generation, checkpoint progress, rerender after success/failure, and current-draft Download serialization.
- Existing generator/service files: only narrow changes if tests demonstrate a Critical/High defect in their current contracts.
- Focused test modules plus a real `streamlit.testing.v1.AppTest` seam: widget lifecycle, call counts, batching, checkpoint recovery, download state, and safety invariants.
- English workflow documentation: describe the cache-independent widget rerun behavior, one-click sequential batches, checkpoint/retry semantics, and fresh Preview/Publish reads.

## Verification requirements

The implementation must include failing-then-passing regressions for target removal/Clear all, one-time defaults, source exclusion, both page call counts, full 10-sized batching, checkpoint preservation, retry subtraction, current-draft downloads, Preview invalidation, video isolation, uploads, omitted-localization preservation, stale Preview/412 protection, static catalog use, and forbidden provider dependencies. Verification consists of focused tests, the complete repository `unittest` suite, real AppTest reruns, syntax/import checks, dependency scans, `git diff --check`, and a final Critical/High review of the changed data-flow boundaries.
