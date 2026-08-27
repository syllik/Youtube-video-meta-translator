# 🧩 Project Context: YouTube Manual Localization Editor

⬅️ [Back to documentation](README.md) · [Open the user workflow](manual-localizations.md)

> Historical product context: the current runtime is Streamlit with separate
> **Machine translate** and **Manual translate** pages. The migration design
> and current architecture are documented in
> [`superpowers/specs/2026-08-27-streamlit-migration-design.md`](superpowers/specs/2026-08-27-streamlit-migration-design.md).

## Goal

Adapt the existing open-source project:

`jordicor/YouTube-Video-Metadata-Translator`

into a simple local tool for manually publishing prepared YouTube video localizations.

The main use case is:

1. Select an existing YouTube video.
2. Paste manually prepared JSON with localized `title` and `description`.
3. Validate the JSON automatically after every form change.
4. Fetch existing YouTube localizations for the selected video.
5. Show the current diff and validation status.
6. Publish all valid changes in one operation.
7. Preserve every existing localization that is not present in the submitted JSON.

Machine translation is not part of the primary workflow.

The application should remain small and local-first.

---

# Primary User Workflow

The intended workflow should be:

```text
Open local app
    ↓
Authenticate with YouTube
    ↓
Select existing video
    ↓
Paste JSON
    ↓
Automatic validation
    ↓
Review diff
    ↓
Publish
    ↓
Done
```

The important UX goal is to replace repetitive manual work in YouTube Studio.

The user will already have high-quality translations prepared elsewhere.

The app does NOT need to generate translations.

---

# Input Format

The application should accept JSON in this format:

```json
{
  "de": {
    "title": "German title",
    "description": "German description"
  },
  "es": {
    "title": "Spanish title",
    "description": "Spanish description"
  },
  "fr": {
    "title": "French title",
    "description": "French description"
  },
  "ja": {
    "title": "Japanese title",
    "description": "Japanese description"
  }
}
```

The selected video already determines the `video_id`.

Do not require `video_id` inside the JSON.

Do not require channel information or unrelated video metadata inside the JSON.

---

# Critical Safety Requirement

Existing YouTube localizations must NEVER be deleted simply because they are missing from the submitted JSON.

Example:

Existing YouTube localizations:

```text
de
fr
ja
ru
```

Incoming JSON:

```text
de
es
```

Expected result:

```text
de = updated if changed
es = added
fr = preserved
ja = preserved
ru = preserved
```

The final YouTube payload must be based on:

```text
existing localizations
+
incoming localizations
=
merged localizations
```

Never treat the incoming JSON as the complete replacement state.

---

# Existing Project

The upstream repository already contains useful code that should be reused where practical.

Important files:

```text
app.py
youtube_account.py
google_translate.py
templates/home.html
requirements.txt
```

Current responsibilities are approximately:

```text
app.py
- Flask application
- routes
- translation workflow
- DeepL / Google Translate integration

youtube_account.py
- Google OAuth
- YouTube Data API client
- video loading
- localization fetching
- localization publishing

google_translate.py
- Google Translate integration

templates/home.html
- main web UI
```

The existing YouTube OAuth implementation should be kept unless there is a concrete reason to change it.

The existing code already uses:

```text
videos.list(part="snippet,localizations")
```

and:

```text
videos.update(part="snippet,localizations")
```

That behavior should be adapted rather than replaced blindly.

---

# Scope for V1

V1 should only solve manual localization editing.

Required:

- Google / YouTube OAuth
- list existing videos
- select one video
- manual JSON textarea
- JSON validation
- localization validation
- fetch current YouTube localizations
- calculate diff
- preview diff
- publish merged localizations
- success/error feedback
- automated tests for core localization logic

Not required for V1:

- AI translation
- Google Translate
- DeepL
- subtitles / SRT
- audio localization
- dubbing
- Whisper
- bulk editing many videos at once
- CSV
- Excel
- database
- cloud deployment
- user accounts
- React rewrite
- frontend framework migration
- rollback/history system

Do not expand the scope unless required by the implementation.

---

# Architecture Direction

Separate the localization logic from Flask and the YouTube API client.

Prefer pure/testable functions for:

```python
parse_localizations_json(...)
validate_localizations(...)
build_localization_diff(...)
merge_localizations(...)
```

A possible new module:

```text
localizations.py
```

with tests:

```text
tests/test_localizations.py
```

Do not put all new business logic directly into `app.py`.

---

# Data Model

A localization should conceptually look like:

```python
{
    "title": str,
    "description": str
}
```

A localization map should look like:

```python
{
    "de": {
        "title": "...",
        "description": "..."
    },
    "fr": {
        "title": "...",
        "description": "..."
    }
}
```

Language codes should be normalized consistently.

Use the language-code conventions already compatible with YouTube Data API.

Examples:

```text
en
de
es
fr
ru
ja
vi
tr
hi
ar
id
pt-BR
```

Do not silently convert regional variants into unrelated generic languages.

---

# Validation

All JSON must be validated before any YouTube write request.

Validation should catch at least:

- invalid JSON syntax
- root value is not an object
- invalid language entry
- localization is not an object
- missing `title`
- missing `description`
- title is not a string
- description is not a string
- empty title if YouTube does not allow it
- title over YouTube limit
- description over YouTube limit

Do not silently truncate content in V1.

If something exceeds the allowed limit, return a validation error.

The UI should show which language and field failed.

Example:

```text
ja.title
Title is too long: 112 / 100 characters
```

No YouTube mutation should happen if validation fails.

---

# Diff Model

Before publishing, compare incoming localizations with the current YouTube state.

Each incoming language should receive a status:

```text
added
changed
unchanged
```

Existing languages absent from the JSON are:

```text
preserved
```

They do not need to appear in the main change list unless useful for the UI.

Example preview:

```text
Added: 2
Changed: 3
Unchanged: 7
Preserved existing: 5
```

Example language entries:

```json
[
  {
    "language": "de",
    "status": "changed",
    "before": {
      "title": "Old German title",
      "description": "Old German description"
    },
    "after": {
      "title": "New German title",
      "description": "New German description"
    }
  },
  {
    "language": "es",
    "status": "added",
    "before": null,
    "after": {
      "title": "Spanish title",
      "description": "Spanish description"
    }
  }
]
```

---

# Preview Endpoint

Add a route approximately equivalent to:

```text
POST /api/localizations/preview
```

Suggested request:

```json
{
  "video_id": "abc123",
  "localizations": {
    "de": {
      "title": "...",
      "description": "..."
    }
  }
}
```

The server should:

1. validate input
2. fetch current YouTube localizations
3. calculate diff
4. return preview information
5. perform NO write request

Suggested response:

```json
{
  "valid": true,
  "summary": {
    "added": 2,
    "changed": 3,
    "unchanged": 7
  },
  "languages": []
}
```

If invalid:

```json
{
  "valid": false,
  "errors": [
    {
      "path": "ja.title",
      "message": "Title is too long"
    }
  ]
}
```

---

# Publish Endpoint

Add a route approximately equivalent to:

```text
POST /api/localizations/publish
```

Important:

The backend MUST validate again during publish.

Do not trust a previous preview response.

Publish flow:

```text
validate incoming JSON
    ↓
fetch latest YouTube video state again
    ↓
fetch latest localizations again
    ↓
merge existing + incoming
    ↓
build safe YouTube update payload
    ↓
videos.update(...)
    ↓
return result
```

This second fetch is important because YouTube state may have changed between validation and Publish.

---

# YouTube API Changes

The current implementation updates one localization at a time.

For this workflow, prefer adding a bulk method such as:

```python
update_video_localizations(
    video_id: str,
    localizations: dict
)
```

The intended logic is:

```text
videos.list
    ↓
existing snippet + localizations
    ↓
merge all incoming languages
    ↓
one videos.update call
```

Avoid one `videos.update` request per language unless the API requires it.

The app should not accidentally modify unrelated video fields.

When constructing an update payload, inspect carefully which `snippet` fields YouTube expects and which fields should be preserved.

---

# UI

Do not redesign the entire application.

V1 can use the existing Flask template architecture.

The main new UI should be simple.

Example:

```text
Selected video
------------------------------------------------
Waterfall Before the Storm
youtube.com/watch?v=abc123
------------------------------------------------

Localizations JSON

┌─────────────────────────────────────────────┐
│ {                                           │
│   "de": { ... },                            │
│   "es": { ... },                            │
│   "ja": { ... }                             │
│ }                                           │
└─────────────────────────────────────────────┘

Validation runs automatically after the Manual radio button and JSON are set, and after either one changes.
```

After automatic validation:

```text
2 added
3 changed
7 unchanged

+ Spanish
+ Arabic

~ German
~ Japanese
~ French

= Russian
= Vietnamese

[ Cancel ]            [ Publish 5 changes ]
```

The localization form should appear only after a single Manual radio button is
selected. The checkbox selection used by the legacy translator is independent.
Validation should run after every JSON change and after switching the selected
Manual video. The Publish button should be unavailable if the current input is
invalid or validation is still pending.

---

# JSON Editor UX

The textarea should support normal raw JSON paste.

Nice-to-have but not required:

- monospace font
- preserve indentation
- useful syntax error position
- line/column for malformed JSON

Do not introduce a heavy code editor dependency unless clearly justified.

A simple textarea is acceptable.

---

# Error Handling

Distinguish:

```text
JSON validation error
YouTube API error
OAuth error
quota exceeded
video not found
network/API failure
```

Do not expose raw Python tracebacks to the normal UI.

Log detailed errors server-side.

Return understandable API responses to the frontend.

---

# Machine Translation

The current project includes Google Translate and DeepL.

Do NOT make removal of those systems the first implementation task.

First make the manual JSON workflow functional and tested.

After that, machine translation can be removed in a separate cleanup task/commit.

Desired final state:

```text
manual JSON localization editor
```

not:

```text
translation generator
```

Possible later cleanup:

```text
remove google_translate.py
remove DeepL dependency
remove translation provider settings
remove old translation routes
remove old translation controls
```

But keep cleanup separate from the core feature where practical.

---

# Testing Requirements

Add automated tests before relying on the new workflow.

At minimum test:

## Parsing

```text
valid JSON
invalid JSON
empty JSON object
wrong root type
```

## Validation

```text
missing title
missing description
wrong title type
wrong description type
title too long
description too long
valid regional language code
```

## Diff

```text
new language -> added
different content -> changed
identical content -> unchanged
```

## Merge

Critical test:

Existing:

```json
{
  "de": {
    "title": "Old DE",
    "description": "..."
  },
  "ru": {
    "title": "RU",
    "description": "..."
  }
}
```

Incoming:

```json
{
  "de": {
    "title": "New DE",
    "description": "..."
  },
  "fr": {
    "title": "FR",
    "description": "..."
  }
}
```

Expected merged result:

```json
{
  "de": {
    "title": "New DE",
    "description": "..."
  },
  "ru": {
    "title": "RU",
    "description": "..."
  },
  "fr": {
    "title": "FR",
    "description": "..."
  }
}
```

`ru` MUST remain.

## API payload generation

Test that:

- existing localizations are preserved
- incoming localizations are added
- changed localizations are replaced
- unrelated metadata is not unintentionally dropped
- validation failure causes zero mutation calls

Mock the YouTube API in unit tests.

Do not require real YouTube credentials to run the automated test suite.

---

# Real Smoke Test

After automated tests pass, test with one non-critical YouTube video.

Initial state:

```text
English default
Russian localization
German localization
```

Incoming JSON:

```text
German -> change
French -> add
Japanese -> add
```

Expected final state:

```text
English -> intact
Russian -> intact
German -> updated
French -> added
Japanese -> added
```

The most important smoke-test assertion is that an existing language omitted from JSON does not disappear.

---

# Development Strategy

Work incrementally.

Suggested order:

## Task 1

Analyze the existing repository and document:

- OAuth flow
- current video loading flow
- current localization read flow
- current localization update flow
- machine translation dependencies
- relevant frontend code
- YouTube API risks

Do not modify code yet.

## Task 2

Add pure localization parsing/validation/diff/merge functions with tests.

## Task 3

Add a safe bulk YouTube localization update method with mocked tests.

## Task 4

Add preview endpoint.

## Task 5

Add publish endpoint.

## Task 6

Add the manual JSON UI.

## Task 7

Add integration/error handling tests and verify the complete workflow locally.

## Task 8

Perform real YouTube smoke test manually.

## Task 9

Only after the manual flow is stable, remove unused machine-translation code in a separate cleanup change.

---

# Git Strategy

Do not make one giant unreviewable change.

Use small logical commits.

Example:

```text
test: add localization parser and validation coverage

feat: add localization diff and merge logic

feat: add bulk YouTube localization update

feat: add localization preview endpoint

feat: add localization publish endpoint

feat: add manual JSON localization UI

refactor: remove unused translation providers
```

Prefer one feature branch for the complete manual JSON feature, with several coherent commits.

Suggested branch:

```text
feat/manual-json-localizations
```

---

# Review Checklist

Before considering the feature complete, review specifically for:

1. Can an omitted language accidentally be deleted?
2. Can malformed JSON trigger a write?
3. Can partially invalid localization data trigger a write?
4. Does Publish re-fetch current YouTube state?
5. Are unrelated snippet fields modified?
6. Is there more than one unnecessary `videos.update` call?
7. Can an unchanged localization cause unnecessary writes?
8. Are title/description limits validated correctly?
9. Are regional language codes handled correctly?
10. Are API/OAuth errors surfaced cleanly?
11. Can tests run without real YouTube credentials?
12. Did the implementation introduce unnecessary dependencies or architecture?

---

# Definition of Done

The feature is complete when this works reliably:

```text
select video
↓
paste prepared localization JSON
↓
automatic validation
↓
see added / changed / unchanged entries
↓
Publish
↓
all submitted localizations appear correctly on YouTube
↓
all existing omitted localizations remain untouched
```

The final V1 should feel like a small metadata utility, not a translation platform.
