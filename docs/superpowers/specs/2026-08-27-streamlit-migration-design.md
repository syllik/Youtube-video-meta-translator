# Streamlit UI Migration Design

## Goal

Replace the current Flask/HTML/CSS interface with a Streamlit application
whose two workflows are visibly and architecturally separate:

- `Machine translate` keeps the current multi-video, multi-language workflow,
  including DeepL, Google fallback, overwrite, and trim behavior.
- `Manual translate` handles one selected video at a time with prepared JSON,
  validation, diff preview, and one safe merged YouTube update.

The video list remains the primary content on both pages. The only controls
shown on a page are the controls required by that page's workflow.

## Scope and non-goals

In scope:

- Streamlit as the only runtime UI and application entry point.
- Two navigable Streamlit pages with a clear mode switch.
- Shared channel and video-list presentation.
- Clear pagination with URL parameters and small default loads.
- Robust Streamlit session state separated by common, machine, and manual
  namespaces.
- Reuse of the existing YouTube OAuth, video listing, translation providers,
  and pure manual-localization logic where practical.
- Credential-free tests for pagination state, page rendering decisions,
  machine workflow orchestration, and manual workflow state transitions.

Out of scope:

- React or another frontend framework.
- Subtitles, SRT, audio localization, dubbing, or AI translation.
- Database, user accounts, cloud deployment, or multi-channel management.
- A new translation provider.
- Batch manual editing; manual mode remains one video per operation.

## Product structure

The application is launched with:

```text
streamlit run streamlit_app.py
```

Streamlit's multipage navigation exposes exactly two workflow pages:

```text
Machine translate
Manual translate
```

The root script provides the shared application configuration and an optional
short start screen with links to the two workflows. It does not render
machine or manual controls. Each workflow page renders the shared channel
header and video list, then its own controls.

### Shared page shell

Both workflow pages use the same visual order:

1. Page title and one-sentence explanation of the current mode.
2. Channel identity, refresh action, and total video count.
3. Mode-specific control panel.
4. Video list with thumbnail, title, description preview, video ID affordance,
   and current localization badges.
5. Pagination summary and controls.

If channel data is loading, the page shows a progress state. If the channel is
empty, it shows an empty state with a refresh action. If an API error occurs,
the page shows a short recovery instruction and does not render controls that
would submit incomplete data.

### Machine translate page

The machine page contains only machine-translation controls:

- video checkboxes keyed by stable YouTube video ID;
- `Select all visible` for the current page;
- `Select all channel videos` only when the user has deliberately selected
  `all` and the full list is available;
- language multi-select;
- DeepL preference with a visible Google fallback explanation;
- `Overwrite existing`;
- `Trim if too long`;
- a run button with a selection summary such as `3 videos · 2 languages`;
- progress, skipped, trimmed, success, quota, and provider-error feedback.

If no videos are checked, the run button is disabled. If no languages are
selected, the run button is disabled. If an existing language is selected and
overwrite is off, the page explains why it is unavailable instead of silently
ignoring it. The operation uses IDs, never titles.

The machine workflow keeps its current behavior: for each selected video and
language, use DeepL when explicitly preferred and available, otherwise use
Google Translation, then publish according to the overwrite and trim settings.
The translation provider code is not imported by the manual page.

### Manual translate page

The manual page contains only manual-localization controls:

- one radio control per video, keyed by stable YouTube video ID;
- a selected-video summary with title and YouTube link;
- a monospace JSON textarea;
- compact format help and the supported JSON example;
- local JSON validation feedback;
- an explicit `Preview changes` action that fetches current YouTube state;
- a diff report for added, changed, and unchanged languages;
- a preserved-language summary;
- a `Publish changes` action enabled only for the latest valid preview.

The editor is hidden until a video is selected. Machine controls, language
multi-selects, provider settings, and machine progress are not rendered on
this page.

The manual flow is:

```text
if no video selected
    show selection guidance and keep editor/actions disabled
else if JSON is empty or malformed
    show local validation error and keep preview/publish disabled
else if JSON is locally valid but preview has not been requested
    show valid-input state and enable Preview changes
else if preview contains validation or YouTube errors
    show field-level errors and keep Publish disabled
else if preview is valid and has changes
    show diff and enable Publish changes
else if preview is valid with no changes
    show no-op state and keep Publish disabled
```

Local parsing happens without a YouTube request. Preview performs no write.
Publish validates again, fetches the latest video, rebuilds the merge, and
performs at most one `videos.update` call. Existing localizations omitted from
the submitted JSON are always preserved. If the editor video or raw JSON
changes after preview, the preview becomes stale and Publish is disabled.

## Architecture

The target structure is:

```text
streamlit_app.py
pages/
  1_Machine_translate.py
  2_Manual_translate.py
ui/
  channel_header.py
  video_list.py
  pagination.py
  feedback.py
  machine_controls.py
  manual_editor.py
services/
  youtube_service.py
  machine_translation_service.py
  manual_localization_service.py
state/
  common_state.py
  machine_state.py
  manual_state.py
models.py
localizations.py
```

The exact filenames may be adjusted during implementation if the existing
modules provide a cleaner seam, but the boundaries are mandatory:

- UI modules render widgets and translate service results into readable
  feedback. They do not call raw Google client methods.
- `youtube_service.py` owns OAuth, channel metadata, video listing, page-token
  traversal, current localization reads, and safe update calls.
- `machine_translation_service.py` owns provider selection, fallback, legacy
  translation settings, and batch orchestration. It does not know about
  Streamlit widgets.
- `manual_localization_service.py` owns the existing parse/validate/diff/merge
  orchestration. It does not import DeepL or Google Translation.
- `localizations.py` remains pure and credential-free.
- State modules define initialization, reset, and stale-result rules. UI code
  may read and update state only through these helpers.

The current `youtube_account.py` contains both YouTube access and legacy
translation-era mutable state. During migration, YouTube access is extracted
behind the service boundary. The migration must not duplicate title-based
selection or create a second localization merge implementation.

After the Streamlit entry point and tests are working, remove the Flask
runtime path from the application: `app.py`, Flask routes, Jinja templates,
and the old CSS/JavaScript UI are no longer launchable application code.
Provider modules and pure localization modules remain because their logic is
used by the new pages.

## Shared video data and caching

The shared video model contains at least:

```text
id
title
description
thumbnail_url
current_language_codes
current_language_names
```

All widget keys and service calls use `id`. Titles are display-only, so
duplicate titles cannot cross-select or publish the wrong video.

The YouTube client/auth object is initialized lazily and kept in a
Streamlit-compatible resource cache or session-owned service. Importing a
page must not start OAuth. Video-page results are cached in session state by
`(channel, limit, page)`; a Refresh action clears only the common video cache
and cursor map, then reloads the requested page.

If a common load fails:

```text
if OAuth is missing or expired
    show Sign in / re-authorize guidance
else if quotaExceeded
    show quota-specific recovery guidance
else if the YouTube request fails
    show a safe generic error and keep the last successful state when present
else if no videos exist
    show the empty state
```

## Pagination and URL contract

Pagination is shared by both pages and uses the URL as the source of truth:

```text
?page=1&limit=10
?page=2&limit=20
?page=1&limit=all
```

Allowed limits are exactly `10`, `20`, `50`, and `all`. The default is
`page=1&limit=10`. The URL uses `all`, not the channel count, so the meaning is
stable when the channel changes.

The page shows all of the following in one compact block:

```text
Videos 11–20 of 117 · Page 2 of 6 · 20 per page
[Previous] [2 / 6] [Next]
```

The page selector may jump to a known page or a later page by traversing
YouTube page tokens. Previous and Next are disabled at the boundaries. When
`limit=all`, the page states that all videos are loaded and hides meaningless
page navigation.

URL/state rules:

```text
if page is missing
    use 1 and write the canonical query parameter
if limit is missing
    use 10 and write the canonical query parameter
if limit is invalid
    use 10 and replace it in the URL
if page is below 1 or above the known page count
    clamp it and replace it in the URL
if limit changes
    reset page to 1, clear page-token/video cache, and reload
if page changes
    keep the current limit, preserve mode-specific selection state, and load
    only the requested page
```

The YouTube API is cursor-based. The service stores page tokens by limit and
page in common session state. If a requested token is unknown, it walks from
the nearest known token, caches each traversed token, and then fetches the
requested page. It never assumes that a numeric page can be fetched with an
offset. `all` fetches all playlist pages internally with API batches of at most
50 and is intentionally opt-in.

The same `page` and `limit` query parameters are used after switching between
the two pages, so the video list does not unexpectedly jump to a different
position. Mode-specific selections remain in their own namespace and are not
submitted across pages.

## State model

State is split into three explicit namespaces. Widget keys include the
namespace and stable IDs to prevent accidental collisions.

### Common state

```text
common.auth_status
common.youtube_service
common.channel
common.total_video_count
common.page
common.limit
common.page_tokens_by_limit
common.video_pages_by_limit
common.load_status
common.load_error
common.last_refresh_id
```

### Machine state

```text
machine.selected_video_ids
machine.select_all_visible
machine.select_all_channel
machine.selected_language_codes
machine.prefer_deepl
machine.overwrite
machine.trim
machine.operation_status
machine.operation_result
machine.operation_error
```

### Manual state

```text
manual.selected_video_id
manual.raw_json
manual.local_validation
manual.preview_result
manual.preview_fingerprint
manual.operation_status
manual.operation_error
```

State transition rules:

```text
if the selected manual video changes
    clear preview result and fingerprint
if manual raw JSON changes
    run local validation, clear preview result, and disable Publish
if Preview succeeds
    store video ID + raw JSON fingerprint with the result
if Publish is clicked and fingerprint no longer matches
    do not call YouTube; ask for a new preview
if machine translation starts
    disable machine inputs for the operation and show progress
if machine translation finishes
    clear common video cache and reload the same canonical page/limit
if common refresh or limit change occurs
    invalidate only page-derived video data; keep independent mode settings
if a mode page is rendered
    do not initialize or mutate the other mode's widgets or operation result
```

## Error and feedback model

The UI maps errors into user-facing categories:

- `oauth_required`: authorize or re-authorize the channel;
- `quota_exceeded`: wait for quota reset and avoid repeated submits;
- `video_not_found`: refresh the video list and select again;
- `invalid_json` / `invalid_localization`: show path and field guidance;
- `translation_unavailable`: choose another language or configure a provider;
- `translation_failed`: identify the provider fallback outcome without exposing
  credentials;
- `youtube_api`: retry after checking connectivity;
- `operation_in_progress`: keep controls disabled until completion.

No normal UI path displays Python tracebacks, access tokens, credential paths,
or raw provider secrets. Logs may retain diagnostic details locally without
including submitted localization content unless already part of existing
logging behavior.

## Testing strategy

Keep the existing pure localization tests and add Streamlit-independent tests
for the new seams:

1. URL pagination parsing and canonicalization for missing, invalid, boundary,
   and `all` values.
2. Cursor traversal and cache invalidation when `limit` or refresh changes.
3. Stable ID-based machine selection with duplicate display titles.
4. Machine provider fallback, overwrite/trim propagation, and no update when
   selection or language input is incomplete.
5. Manual state invalidation when video or JSON changes, stale-preview
   rejection, no-op publish suppression, and one-update publish behavior.
6. Page-level rendering decisions: machine controls never appear on the manual
   page and manual controls never appear on the machine page.
7. YouTube service requests remain mocked; no test publishes to a live channel.

Run the full credential-free suite with:

```bash
python -m unittest discover -s tests -v
python -m compileall -q streamlit_app.py pages ui services state localizations.py
git diff --check
```

## Acceptance criteria

- The app starts through Streamlit and does not require Flask to run.
- The user can switch between exactly two pages: Machine translate and Manual
  translate.
- Both pages show the same readable video list and channel context.
- Machine mode retains multi-video/multi-language DeepL/Google, overwrite, and
  trim behavior.
- Manual mode is single-video, radio-based, JSON-driven, preview-first, and
  preserves omitted localizations.
- No machine-only control is visible on the manual page, and no manual-only
  editor is visible on the machine page.
- The initial request loads at most 10 videos.
- The only page-size choices are `10 / 20 / 50 / all`, with `10` as default.
- `page` and `limit` are visible and reproducible in the URL.
- Pagination explains the current range and total, handles YouTube cursors, and
  does not show stale videos after navigation.
- Selection and operation state is namespaced, ID-based, and resilient to
  Streamlit reruns.
- Manual publish always revalidates and refetches current YouTube state before
  a write.
- The old Flask/HTML/CSS runtime path is removed after the Streamlit path is
  verified.
