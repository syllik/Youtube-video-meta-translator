# Translate Sidebar, Reset, Draft, and FAQ Design

## Status

Approved in chat on 2026-08-29. This document describes the implementation that
will be applied to the existing unified Translate workflow on `main`.

## Scope and constraints

The application keeps one Translate workflow and one supporting LLM Translation
prompt page. This change does not restore legacy pages or create a second
pagination, editor, or publishing architecture.

The live YouTube Data API `i18nLanguages.list` catalog remains the only source
of valid localization language codes. Existing Preview and Publish safety
semantics remain in place: Preview never writes, Publish requires valid JSON
and a current Preview, and omitted existing localizations are preserved.

All user-facing copy and repository documentation remain in English. No push is
performed automatically.

## Design

### Shared bootstrap and live catalog

`bootstrap_app_context()` will fetch the live language catalog once as part of
the shared YouTube bootstrap and expose it through `AppContext`. The sidebar
uses its codes to calculate each card's localization counts, while Translate
and the LLM prompt page reuse the same catalog object instead of fetching a
second copy during the same run.

The FAQ page uses a separate static bootstrap. It configures the Streamlit page
and renders static content only; it does not construct `YoutubeService`, invoke
OAuth, fetch channel/video data, or render the persistent video sidebar.

### Sidebar layout and video summaries

The channel block renders the image as a full-width row followed by one compact
vertical text column: channel label, name, description, channel ID, total video
count, YouTube/RSS links, and Refresh.

Video cards retain the thumbnail and title, then render only default language,
`Localizations: done / undone`, and video ID. `done` counts existing
localization entries except the default language. `undone` counts live catalog
codes that are absent from the existing entries, also excluding the default
language. Descriptions and localization badges are removed.

The selected card receives a subtle lighter background and shadow. The
thumbnail remains bright, and the external-link icon is always visible in a
small top-right floating control.

### Cursor-backed pagination and Load more

The current `common.page_tokens_by_limit` and
`common.video_pages_by_limit` caches remain authoritative. Common state gains a
small accumulation descriptor containing the selected limit, starting page,
and last appended page.

For numeric limits, the initial render loads the URL-selected page and shows
only that page. `Load more` advances from the last appended page, loads the next
cursor-backed page if needed, and renders the combined range without duplicate
video IDs. Changing the URL page resets the accumulation descriptor while
retaining reusable page cache entries, so page 2 starts with only page 2 and
then appends page 3, page 4, and so on. The control is hidden for `all` and when
there is no next numeric page.

Previous and Next become icon-only controls with accessible labels/tooltips;
the page selector and URL `page`/`limit` contract remain unchanged. Loading a
batch uses a visible spinner and the action is guarded against repeated
execution during the operation.

### Manual draft lifecycle

Manual state gains an explicit loaded-video marker and a reload request. A
video change clears the old draft and loads the selected video's current live
localizations as direct JSON, excluding the default language as a localization
key. The JSON is the editable draft.

A normal Streamlit rerun does not reload this draft. A reload happens only on
video change, successful Publish, successful Reset, explicit Refresh, or an
equivalent explicit reload request. Reloading invalidates any stale Preview and
updates the editor widget value for the selected video.

The editor UI is split into separate sections. `Localization JSON Example`
renders only a read-only example. `Manual edit` renders the editable text area.
`Preview & Publish` is rendered separately after the generation controls, with
Preview at the left edge and Publish at the right edge.

### Merge semantics for Codex and external LLM results

Generated and uploaded direct localization documents are merged into the
current editor draft before the shared validation path. An incoming language
replaces only the matching language entry; all other draft entries remain.
The upload path validates UTF-8, exact requested language coverage, and the
existing upload contract before changing state. A malformed upload leaves the
draft untouched.

The merged text is passed through the existing editor validation, Preview, and
Publish flow. No source-specific publishing operation is introduced.

### Destructive Reset languages flow

Each video card renders a full-width `Reset languages` control. The control
uses native browser `window.confirm()` with the video title/ID and a clear
warning that all YouTube localizations will be deleted, only default metadata
will remain, and desired translations must be saved first. Cancel does not
navigate or call an API.

An affirmed reset navigates with a narrowly scoped pending-reset query value.
The shared sidebar consumes that value and calls a separate reset service
operation for the exact video ID. The reset service fetches current video data,
builds a payload with `localizations: {}`, preserves the default title,
description, `defaultLanguage`, and the existing writable snippet fields, then
performs one update. It does not route through an empty manual JSON document,
which preserves ordinary Publish's omitted-language behavior.

On success, page/video caches are invalidated, a selected-video reload is
requested when applicable, progress is recalculated from fresh data, and a
success message is displayed after rerun. Errors produce actionable feedback
and do not silently clear the draft.

### Translate page and LLM prompt page

After the Translate title/caption, the page renders these sections in order:

1. `Localization JSON Example`
2. `Manual edit`
3. `Source languages`
4. `Generate translations`
5. `Preview & Publish`

The existing shared source selection remains authoritative: the default
language is the primary source and selected existing localizations are only
verified references. The LLM prompt page keeps this shared selection and
breaks its larger content into logical expanders, including a short English
quality guide recommending two or three good source translations when
available, while keeping the default source authoritative.

### FAQ

`pages/3_FAQ.py` renders a static English FAQ with short expanders covering the
tool, workflow, Manual edit, Codex, the LLM prompt, multiple source languages,
Preview versus Publish, Reset, omitted JSON keys, safety, failure handling, and
the fact that FAQ works without YouTube OAuth/API access.

The root navigation exposes Translate, LLM Translation prompt, and FAQ.

## Error handling and operation states

Visible spinners or progress messages cover bootstrap channel/video/catalog
loads, selected-video loads, Refresh, Load more, Reset, Codex generation,
Preview, and Publish. Buttons and reset controls do not permit a second request
while the corresponding operation is active. Existing YouTube quota, missing
video, validation, and connection feedback patterns are reused.

## Test strategy

Focused pure/state tests will cover:

- live-localization serialization and default-language exclusion;
- draft preservation across rerun and reload on explicit lifecycle events;
- merge and overlapping-language replacement for Codex and upload results;
- omitted-language preservation for normal Publish;
- live-catalog `done / undone` counts;
- numeric append pagination, repeated append deduplication, page reset, and
  `all` behavior;
- reset payload preservation, exact video targeting, separate service path, and
  state/cache invalidation;
- static FAQ rendering without YouTube bootstrap/service construction.

The existing full test suite, syntax/import checks, formatter/linter commands
already defined by the repository, and `git diff --check` will run after
implementation.

## Documentation updates

The implementation change will update `README.md`, `AGENTS.md`, and the
relevant workflow documents under `docs/` so they describe the unified Translate
workflow, Manual edit draft and merge semantics, omitted-language preservation,
Reset safety, Load more, source-quality guidance, FAQ, and FAQ's independence
from YouTube OAuth/API state. Stale references to removed workflows or controls
will be removed.
