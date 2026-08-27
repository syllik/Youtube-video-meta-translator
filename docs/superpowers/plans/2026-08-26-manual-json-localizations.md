# Manual JSON YouTube Localizations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing local YouTube translator into a small editor that accepts localization JSON for one selected video, validates it, previews a diff, and publishes one merged localization update without deleting omitted languages.

**Architecture:** Keep the existing `InstalledAppFlow` OAuth and channel/video listing. Add a dependency-free workflow module for JSON parsing, validation, diff calculation, and YouTube payload generation; add a thin service boundary that fetches the current video before preview/publish and performs at most one write for the selected video. Replace the translation modal with a JSON textarea, a preview report, and an explicit publish action while retaining the existing page layout and pagination.

**Tech Stack:** Python 3.7-compatible standard-library dataclasses/`json`/`unittest`, Flask, Google YouTube Data API v3, Jinja2, existing Bootstrap/CSS.

**Source of truth:** `youtube-manual-localization-editor-context.md` is the authoritative product context for this plan. If an implementation detail below conflicts with that file, follow the context file and update this plan accordingly.

**Spec:** Manual localization editing only; the attached context defines the V1 requirements and boundaries.

## Global Constraints

- Keep the existing YouTube OAuth flow and `token.pickle` behavior unchanged unless a change is required to call the new localization service.
- Version one handles exactly one selected uploaded video per preview/publish operation; do not add batch editing.
- The accepted JSON shape is a non-empty object keyed by exact YouTube localization codes: `{ "es": { "title": "...", "description": "..." } }`.
- A missing localization key in submitted JSON is preserved from YouTube and is never deleted or replaced.
- Fetch the complete current video resource, including `snippet` and `localizations`, before generating a publish payload.
- Parse and validate every submitted entry before any `videos.update` call; one invalid entry blocks the whole publish operation, while valid entries remain available for the preview report.
- Preview performs no YouTube write. Publish re-parses/re-validates and re-fetches current localizations instead of trusting browser state.
- Added, changed, unchanged, and invalid entries must be distinguishable in the service result and rendered in the UI.
- Do not add subtitle-file support, subtitle parsing, subtitle publishing, or unrelated visual redesign. Google Translate and DeepL are outside the V1 workflow, but their existing code and configuration remain untouched until a separate cleanup after the manual workflow is stable.
- Use video IDs for selection and API calls; never use video titles as identifiers.
- Use `textContent`/escaped template output for user-provided JSON and localization values; do not build executable JavaScript strings from video titles.
- Do not add a runtime dependency solely for tests; use `python3 -m unittest` unless the repository gains an explicit test runner later.

---

### Task 1: Analyze the existing repository before changing code

**Files:**
- Read: `app.py`, `youtube_account.py`, `google_translate.py`, `templates/home.html`, `requirements.txt`
- Document findings in the implementation notes or task handoff; do not modify application code in this task.

- [ ] **Step 1: Confirm the existing OAuth and token flow**

Verify the current `InstalledAppFlow`, scopes, callback port, and `token.pickle` behavior. Preserve them unless a later localization change requires an adjustment.

- [ ] **Step 2: Trace the current video and localization flows**

Record how videos are listed, how `videos.list(part="snippet,localizations")` and the existing localization helpers are used, and how the current one-language-at-a-time update is built.

- [ ] **Step 3: Identify machine-translation and UI boundaries**

Record the Google Translate/DeepL imports, initialization, routes, and controls so the manual workflow can be added without making their removal a prerequisite. Do not remove them here.

- [ ] **Step 4: Note API risks before implementation**

Confirm the required `snippet` fields for `videos.update`, the one-video scope, the omitted-language preservation rule, and the need for mocked tests rather than live credentials.

### Task 2: Define the JSON contract and validation model

**Files:**
- Create: `localizations.py`
- Create: `tests/test_localizations.py`
- Create: `tests/__init__.py`

**Interfaces:**
- `LocalizationValue(title: str, description: str)` stores one valid submitted or existing localization.
- `LocalizationIssue(language_code: Optional[str], message: str, path: Optional[str] = None)` identifies a document-level or language-specific validation failure; field errors carry paths such as `ja.title`.
- `ParsedLocalizations(entries: Mapping[str, LocalizationValue], issues: Tuple[LocalizationIssue, ...])` exposes `is_valid` and `invalid_entries` properties.
- `parse_localizations_json(raw_json: str, supported_language_codes: Collection[str]) -> ParsedLocalizations` is the parser/validator entry point used by the application; it may delegate field validation to a pure `validate_localizations(...)` helper.

- [ ] **Step 1: Write failing parser tests**

Add tests covering the exact first-version contract:

```python
import json
import unittest

from localizations import LocalizationValue, parse_localizations_json


SUPPORTED = {"en", "es", "fr"}


class ParseLocalizationsTests(unittest.TestCase):
    def test_valid_object_preserves_unicode_and_newlines(self):
        raw = json.dumps({
            "es": {"title": "Título", "description": "Línea 1\nLínea 2"}
        })

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertTrue(result.is_valid)
        self.assertEqual(
            result.entries["es"],
            LocalizationValue("Título", "Línea 1\nLínea 2"),
        )

    def test_malformed_json_is_document_invalid(self):
        result = parse_localizations_json('{"es":', SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertIsNone(result.invalid_entries[0].language_code)
        self.assertIsNone(result.invalid_entries[0].path)

    def test_all_invalid_entries_are_reported(self):
        raw = json.dumps({
            "de": {"title": "Unsupported", "description": "x"},
            "es": {"title": "", "description": "x"},
            "fr": {"title": "Missing description"},
            "en": {"title": 123, "description": "x"},
        })

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            {issue.language_code for issue in result.invalid_entries},
            {"de", "es", "fr", "en"},
        )
        self.assertEqual(result.entries, {})

    def test_valid_entries_remain_reportable_when_another_entry_is_invalid(self):
        raw = json.dumps({
            "es": {"title": "Nuevo", "description": "Nuevo"},
            "de": {"title": 123, "description": "x"},
        })

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertFalse(result.is_valid)
        self.assertEqual(
            result.entries["es"],
            LocalizationValue("Nuevo", "Nuevo"),
        )
        self.assertEqual([issue.language_code for issue in result.invalid_entries], ["de"])

    def test_title_and_description_limits_are_inclusive(self):
        raw = json.dumps({
            "es": {
                "title": "t" * 100,
                "description": "d" * 5000,
            }
        })

        result = parse_localizations_json(raw, SUPPORTED)

        self.assertTrue(result.is_valid)

    def test_empty_document_and_unknown_fields_are_invalid(self):
        empty = parse_localizations_json("{}", SUPPORTED)
        extra = parse_localizations_json(
            json.dumps({"es": {"title": "x", "description": "y", "extra": "z"}}),
            SUPPORTED,
        )

        self.assertFalse(empty.is_valid)
        self.assertFalse(extra.is_valid)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the parser tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_localizations -v
```

Expected: FAIL because `localizations.py` and `parse_localizations_json` do not exist yet.

- [ ] **Step 3: Implement the minimal validation model**

Implement Python 3.7-compatible dataclasses and validation with these rules:

1. Decode only a JSON object; malformed JSON, a JSON scalar, an array, or `null` creates a document-level issue.
2. Require at least one localization entry.
3. Require every key to be a string present in `supported_language_codes`; normalize codes consistently without converting regional variants such as `pt-BR` or `zh-CN` into unrelated generic languages.
4. Require each value to be an object with exactly `title` and `description` string fields; reject missing fields, non-string values, and unknown fields.
5. Reject a title whose stripped value is empty.
6. Allow an empty description, but reject title length above 100 or description length above 5000; do not trim submitted content.
7. Collect every entry issue in one result. If any issue exists, retain valid entries for reporting but mark the result invalid; downstream plan generation must set `payload=None` so a valid-looking subset cannot be written accidentally.
8. Include a field path such as `ja.title` or `ja.description` for field-level issues; document-level JSON errors may have no path.
9. Keep valid entries in deterministic language-code order for later reporting.

Use `json.loads` only for parsing; do not call YouTube, translation services, or filesystem APIs from this module.

- [ ] **Step 4: Run the parser tests and verify they pass**

Run:

```bash
python3 -m unittest tests.test_localizations -v
```

Expected: PASS for all parser and validation cases.

- [ ] **Step 5: Commit the self-contained parser work**

```bash
git add localizations.py tests/__init__.py tests/test_localizations.py
git commit -m "feat: add manual localization JSON validation"
```

### Task 3: Add diff calculation and safe merged payload generation

**Files:**
- Modify: `localizations.py`
- Modify: `tests/test_localizations.py`

**Interfaces:**
- `LocalizationDiff(language_code: str, status: str, submitted: LocalizationValue, existing: Optional[LocalizationValue])` uses only `added`, `changed`, or `unchanged` statuses for valid entries.
- `LocalizationPlan(diffs: Tuple[LocalizationDiff, ...], issues: Tuple[LocalizationIssue, ...], payload: Optional[Dict[str, Any]], preserved_language_codes: Tuple[str, ...])` exposes `is_valid` and `has_changes` properties.
- `build_localization_diff(existing: Mapping[str, LocalizationValue], submitted: Mapping[str, LocalizationValue]) -> Tuple[LocalizationDiff, ...]` compares exact title and description values.
- `merge_localizations(existing: Mapping[str, LocalizationValue], submitted: Mapping[str, LocalizationValue]) -> Dict[str, Dict[str, str]]` starts with every existing localization and replaces/adds only submitted valid codes.
- `build_video_update_payload(video_resource: Mapping[str, Any], submitted: Mapping[str, LocalizationValue]) -> Dict[str, Any]` returns one YouTube `videos.update` body.
- `build_localization_plan(video_resource: Mapping[str, Any], parsed: ParsedLocalizations) -> LocalizationPlan` returns no payload when parsing contains any issue.

- [ ] **Step 1: Write failing diff and payload tests**

Add tests with this fixture:

```python
VIDEO_RESOURCE = {
    "id": "video-1",
    "snippet": {
        "title": "Original title",
        "description": "Original description",
        "categoryId": "22",
        "defaultLanguage": "en",
        "tags": ["keep-me"],
    },
    "localizations": {
        "de": {"title": "Alt", "description": "Alt"},
        "fr": {"title": "Même", "description": "Même"},
    },
}
```

Cover these behaviors:

```python
def test_diff_reports_added_changed_and_unchanged(self):
    existing = {
        "de": LocalizationValue("Alt", "Alt"),
        "fr": LocalizationValue("Même", "Même"),
    }
    submitted = {
        "de": LocalizationValue("Nouveau", "Alt"),
        "fr": LocalizationValue("Même", "Même"),
        "es": LocalizationValue("Nuevo", "Nuevo"),
    }

    result = build_localization_diff(existing, submitted)

    self.assertEqual(
        [(item.language_code, item.status) for item in result],
        [("de", "changed"), ("es", "added"), ("fr", "unchanged")],
    )


def test_payload_merges_submitted_values_and_preserves_omitted_languages(self):
    submitted = {"es": LocalizationValue("Nuevo", "Nuevo")}

    payload = build_video_update_payload(VIDEO_RESOURCE, submitted)

    self.assertEqual(payload["localizations"]["de"], {"title": "Alt", "description": "Alt"})
    self.assertEqual(payload["localizations"]["fr"], {"title": "Même", "description": "Même"})
    self.assertEqual(payload["localizations"]["es"], {"title": "Nuevo", "description": "Nuevo"})
    self.assertEqual(payload["snippet"]["tags"], ["keep-me"])


def test_payload_does_not_mutate_the_fetched_resource(self):
    submitted = {"de": LocalizationValue("Nouveau", "Nouveau")}

    build_video_update_payload(VIDEO_RESOURCE, submitted)

    self.assertEqual(VIDEO_RESOURCE["localizations"]["de"]["title"], "Alt")


def test_invalid_plan_has_no_payload(self):
    parsed = ParsedLocalizations(
        entries={},
        issues=(LocalizationIssue("es", "invalid title"),),
    )

    plan = build_localization_plan(VIDEO_RESOURCE, parsed)

    self.assertFalse(plan.is_valid)
    self.assertIsNone(plan.payload)
```

- [ ] **Step 2: Run the focused tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_localizations -v
```

Expected: FAIL because the diff/payload interfaces are not implemented.

- [ ] **Step 3: Implement deterministic diffing and payload merging**

Implement the following rules:

1. Compare only submitted language codes, sorted by code.
2. Mark `added` when the code is absent from current YouTube localizations.
3. Mark `changed` when either title or description differs.
4. Mark `unchanged` only when both fields match exactly.
5. Deep-copy the fetched resource before constructing the body.
6. Start the outgoing `localizations` map from every existing YouTube localization, then replace/add only submitted valid codes. Never construct the map from submitted entries alone.
7. Preserve writable `snippet` fields needed by YouTube (`title`, `description`, `categoryId`, `tags`, `defaultLanguage`, and `defaultAudioLanguage`) when present; do not invent `defaultLanguage`.
8. Calculate diff rows for valid entries even when parser issues exist, but return a plan with `payload=None` if parser issues exist or the source resource lacks the required `id`, `snippet.title`, `snippet.description`, or `snippet.categoryId` fields.
9. Record omitted existing localization codes in `preserved_language_codes` for the preview summary.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run:

```bash
python3 -m unittest tests.test_localizations -v
```

Expected: PASS, including proof that omitted languages remain in the generated payload.

- [ ] **Step 5: Commit the diff and payload work**

```bash
git add localizations.py tests/test_localizations.py
git commit -m "feat: calculate localization diffs and merged update payloads"
```

### Task 4: Expose a narrow YouTube localization read/write boundary

**Files:**
- Modify: `youtube_account.py`
- Create: `tests/test_youtube_localization_api.py`

**Interfaces:**
- `YoutubeApi.get_video_with_localizations(video_id: str) -> Dict[str, Any]` fetches one complete video resource with `part='snippet,localizations'` and raises a clear error when no single item is returned.
- `YoutubeApi.update_video_localizations(payload: Mapping[str, Any]) -> Dict[str, Any]` is the safe bulk boundary equivalent to the context's `update_video_localizations(video_id, localizations)` example: it performs exactly one `videos.update(part='snippet,localizations', body=payload)` call for the selected video. The payload includes merged localizations and only the required preserved `snippet` fields.

- [ ] **Step 1: Write failing API-boundary tests**

Use `unittest.mock.Mock` to verify the resource and request shape without OAuth or network access:

```python
from unittest.mock import Mock

from youtube_account import YoutubeApi


def test_get_video_with_localizations_requests_both_required_parts():
    account = object.__new__(YoutubeApi)
    account.youtube = Mock()
    account.youtube.videos.return_value.list.return_value.execute.return_value = {
        "items": [{"id": "video-1", "snippet": {}, "localizations": {}}]
    }

    result = account.get_video_with_localizations("video-1")

    self.assertEqual(result["id"], "video-1")
    account.youtube.videos.return_value.list.assert_called_once_with(
        part="snippet,localizations", id="video-1"
    )


def test_update_video_localizations_makes_one_write_with_supplied_payload():
    account = object.__new__(YoutubeApi)
    account.youtube = Mock()
    account.youtube.videos.return_value.update.return_value.execute.return_value = {"ok": True}
    payload = {"id": "video-1", "localizations": {"es": {"title": "x", "description": "y"}}}

    result = account.update_video_localizations(payload)

    self.assertEqual(result, {"ok": True})
    account.youtube.videos.return_value.update.assert_called_once_with(
        part="snippet,localizations", body=payload
    )
```

Wrap the two functions in a `unittest.TestCase` so the assertions use `self` consistently.

- [ ] **Step 2: Run the API-boundary tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_youtube_localization_api -v
```

Expected: FAIL because the new methods do not exist.

- [ ] **Step 3: Implement the two methods without changing OAuth**

Add the methods beside the existing localization helpers. The read method must use the authenticated `self.youtube` client, return the only item, and reject an empty/multiple response with a normal application exception. The write method must only forward the already-generated payload and must not fetch, merge, trim, translate, or fabricate metadata.

Do not modify `check_credentials`, the OAuth scope, the local callback port, or token storage in this task.

- [ ] **Step 4: Run the API-boundary tests and verify they pass**

Run:

```bash
python3 -m unittest tests.test_youtube_localization_api -v
```

Expected: PASS with exactly one read assertion and one write assertion.

- [ ] **Step 5: Fix only the listing state needed by the editor**

Update `set_video_page` so a request for a different page clears and reloads `page_videos` instead of reusing the previous page. Update `set_language_names` in `app.py` to derive names for the current page on every GET rather than relying on the process-global `language_names_added` flag. Keep the existing pagination UI and API calls otherwise unchanged.

- [ ] **Step 6: Run all current focused tests**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS for parser, diff/payload, and YouTube-boundary tests.

- [ ] **Step 7: Commit the YouTube boundary work**

```bash
git add youtube_account.py app.py tests/test_youtube_localization_api.py
git commit -m "feat: add YouTube localization read and write boundary"
```

### Task 5: Add a validation-first localization service

**Files:**
- Create: `localization_service.py`
- Create: `tests/test_localization_service.py`

**Interfaces:**
- `LocalizationOperationResult(video: Optional[Mapping[str, Any]], plan: LocalizationPlan, wrote: bool)` is the service result consumed by Flask serialization.
- `preview_localizations(youtube_api: Any, video_id: str, raw_json: str, supported_language_codes: Collection[str]) -> LocalizationOperationResult` validates first, then fetches current data for a valid document, and never writes.
- `publish_localizations(youtube_api: Any, video_id: str, raw_json: str, supported_language_codes: Collection[str]) -> LocalizationOperationResult` validates first, fetches current data before publishing, and writes once only when the plan has valid added/changed entries.

- [ ] **Step 1: Write failing service tests**

Create a fake account that records call order and write count:

```python
class FakeYoutubeApi:
    def __init__(self, video):
        self.video = video
        self.events = []
        self.update_calls = []

    def get_video_with_localizations(self, video_id):
        self.events.append(("get", video_id))
        return self.video

    def update_video_localizations(self, payload):
        self.events.append(("update", payload["id"]))
        self.update_calls.append(payload)
        return {"id": payload["id"]}
```

Test all of these invariants:

```python
def test_invalid_json_does_not_fetch_or_write(self):
    api = FakeYoutubeApi(VIDEO_RESOURCE)

    result = publish_localizations(api, "video-1", '{"es": {"title": 4}}', {"es"})

    self.assertFalse(result.plan.is_valid)
    self.assertFalse(result.wrote)
    self.assertEqual(api.events, [])
    self.assertEqual(api.update_calls, [])


def test_valid_publish_fetches_current_data_before_one_write(self):
    api = FakeYoutubeApi(VIDEO_RESOURCE)
    raw = json.dumps({"es": {"title": "Nuevo", "description": "Nuevo"}})

    result = publish_localizations(api, "video-1", raw, {"es"})

    self.assertTrue(result.wrote)
    self.assertEqual([event[0] for event in api.events], ["get", "update"])
    self.assertEqual(len(api.update_calls), 1)
    self.assertIn("de", api.update_calls[0]["localizations"])


def test_unchanged_publish_does_not_write(self):
    api = FakeYoutubeApi(VIDEO_RESOURCE)
    raw = json.dumps({"fr": {"title": "Même", "description": "Même"}})

    result = publish_localizations(api, "video-1", raw, {"fr"})

    self.assertFalse(result.wrote)
    self.assertEqual(api.events, [("get", "video-1")])
```

- [ ] **Step 2: Run the service tests and verify they fail**

Run:

```bash
python3 -m unittest tests.test_localization_service -v
```

Expected: FAIL because the service module and interfaces do not exist.

- [ ] **Step 3: Implement validation-first orchestration**

Implement this exact sequence for both operations:

1. Call `parse_localizations_json` before any YouTube API method.
2. If invalid, return a result with `video=None`, the issues, `payload=None`, and `wrote=False`.
3. For a valid document, call `get_video_with_localizations(video_id)` and pass the fetched resource to `build_localization_plan`.
4. Preview returns the plan without calling the update method.
5. Publish returns without writing when the plan is invalid or has no changes.
6. Publish calls the bulk `update_video_localizations(plan.payload)` boundary once when the plan contains added/changed entries, then returns `wrote=True`.
7. Let API exceptions propagate to the Flask layer so failures are reported as failures rather than as an empty localization set or a successful operation.

This guarantees that invalid JSON, invalid fields, unsupported languages, and source-resource validation failures cannot reach a write request.

- [ ] **Step 4: Run the service tests and verify they pass**

Run:

```bash
python3 -m unittest tests.test_localization_service -v
```

Expected: PASS, including zero write calls for invalid and unchanged input.

- [ ] **Step 5: Commit the service work**

```bash
git add localization_service.py tests/test_localization_service.py
git commit -m "feat: validate localization changes before publishing"
```

### Task 6: Add preview and publish endpoints without making translation cleanup a prerequisite

**Files:**
- Modify: `app.py`
- Modify: `tests/test_localization_service.py`

**Interfaces:**
- `POST /api/localizations/preview` accepts `{ "video_id": str, "localizations": object }` as the canonical request shape from the context and returns the serialized diff without writing.
- `POST /api/localizations/publish` accepts the same body, revalidates and re-fetches, then returns the serialized result and write status.
- If the UI transports the raw textarea as `localizations_json` so malformed JSON can be reported, the server must parse it into the same canonical localization map before building a plan; neither transport may bypass validation.
- Invalid request envelopes return HTTP 400; invalid localization documents return HTTP 422; YouTube read/write failures return a non-2xx response with a useful error message.

- [ ] **Step 1: Add endpoint-level service contract tests**

Keep the tests independent of OAuth by testing the response serializer and service result mapping with a fake account. Assert that the JSON response contains:

```python
{
    "valid": True,
    "summary": {"added": 1, "changed": 1, "unchanged": 1},
    "languages": [
        {"language": "es", "status": "added", "before": None, "after": {"title": "x", "description": "y"}},
        {"language": "fr", "status": "changed", "before": {"title": "old", "description": "old"}, "after": {"title": "new", "description": "new"}},
        {"language": "de", "status": "unchanged", "before": {"title": "x", "description": "y"}, "after": {"title": "x", "description": "y"}},
    ],
    "errors": [],
    "preserved_language_codes": ["it"],
}
```

For an invalid document, assert `valid is False`, all error paths/messages are present, and the fake account has zero update calls.

- [ ] **Step 2: Add the manual endpoints without removing translation systems**

In `app.py`, add the two `/api/localizations/...` routes and their request/response helpers. Keep the existing Google Translate/DeepL imports, initialization, routes, and configuration in this core change; their removal belongs to a separate cleanup after the manual workflow is stable. The new manual routes must not invoke machine translation.

Keep the existing `YoutubeApi()` construction, OAuth, channel loading, video listing, and quota page behavior. Do not change credential scopes or add a new OAuth flow.

- [ ] **Step 3: Add request parsing and response serialization**

Add a small helper that uses `request.get_json(silent=True)`, checks that the body is an object, requires a non-empty string `video_id`, and accepts the context's `localizations` object. If the browser transports raw textarea text as `localizations_json`, parse it into the canonical object before validation. Do not accept browser-provided diff data or update payloads as authoritative.

Serialize each plan entry as `language`, `status`, `before`, and `after`, matching the context example. Serialize invalid issues as `path` and `message`, using the explicit field path from `LocalizationIssue`. Include `valid`, `summary` with `added`/`changed`/`unchanged` counts, `languages`, `errors`, and preserved-language information; publish responses may additionally include `wrote`.

Ensure the preview handler never invokes `update_video_localizations`, and ensure the publish handler calls `publish_localizations`, which performs the validation-first sequence.

- [ ] **Step 4: Run service and endpoint contract tests**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS, with no test requiring OAuth credentials, `config/account_client_secrets_main.json`, or a live YouTube API.

- [ ] **Step 5: Commit the endpoint work**

```bash
git add app.py tests/test_localization_service.py
git commit -m "feat: add localization preview and publish endpoints"
```

### Task 7: Replace the homepage controls with single-video JSON editing

**Files:**
- Modify: `templates/home.html`
- Modify: `static/css/home.css`

**Interfaces:**
- Each video row exposes its YouTube ID through a card-level Select button; the browser sends that ID unchanged.
- The JSON textarea accepts raw JSON in the context's localization-map format. The browser sends it as `localizations` after parsing, or as `localizations_json` when raw-text transport is needed for server-side syntax-error reporting; both paths use the same backend validation.
- The preview panel renders statuses `added`, `changed`, `unchanged`, and `invalid` plus preserved-language count.
- The publish button is disabled until the latest preview is valid and contains at least one added/changed entry; the backend still revalidates independently.

- [ ] **Step 1: Replace title-based multi-selection with one ID-based selection**

Change the existing video checkbox to a card-level Select button keyed by `{{ video.id }}`. Keep the thumbnail, title, description, language count, and pagination. Remove the “select all” and all-channel behaviors because version one edits one video at a time.

- [ ] **Step 2: Add the minimal JSON editor controls**

Replace the language/DeepL/overwrite/trim controls with:

1. A labeled `<textarea id="localizations-json">`.
2. A `Validate and preview` button.
3. A disabled `Publish changes` button.
4. A report container with separate sections for valid diff entries, invalid entries, and preserved existing languages.

Use a short example placeholder showing the accepted shape, but do not use placeholder content as a submitted default.

- [ ] **Step 3: Wire preview and publish requests**

Implement browser functions with these request bodies:

```javascript
{
    video_id: selectedVideoId,
    localizations: JSON.parse(document.getElementById("localizations-json").value)
}
```

Preview must clear the old report, disable publish while waiting, call `/api/localizations/preview`, and render every returned entry. Invalid JSON is shown as a validation error and keeps publish disabled. Valid responses enable publish only when the summary contains at least one `added` or `changed` entry.

Publish must call `/api/localizations/publish` with the same current video ID and current localization JSON, show the returned write result, and reload the page only after a successful write. Network or non-2xx responses must remain visible as errors and must not be presented as “All tasks completed successfully.”

Render server-returned titles/descriptions with DOM text APIs or escaped HTML; never interpolate them into executable JavaScript.

- [ ] **Step 4: Add only the CSS needed for the editor report**

Add compact styles for the textarea, report rows, and status colors while retaining the existing dark layout, channel header, video list, thumbnails, and pagination. Do not introduce a new frontend framework or redesign the page.

- [ ] **Step 5: Perform a template/static review**

Verify the template has no references to `selected_videos`, `selected_languages`, `useDeepL`, `overwrite`, `trim_checked`, `/languages`, `/error`, `selectAllChannelVideos`, or title-to-JavaScript escaping. Verify every API call sends an ID and only the canonical localization map or the explicitly supported raw-JSON transport; never send browser-generated diffs or update payloads.

- [ ] **Step 6: Commit the editor UI**

```bash
git add templates/home.html static/css/home.css
git commit -m "feat: add manual localization JSON editor UI"
```

### Task 8: Complete focused verification and preserve scope

**Files:**
- Modify: `README.md`
- No subtitle files created or changed.

- [ ] **Step 1: Run the complete automated test suite**

Run:

```bash
python3 -m unittest discover -s tests -v
```

Expected: PASS for JSON parsing, invalid-entry aggregation, diff statuses, omitted-language preservation, payload generation, validation-before-write, no-op unchanged publishing, and YouTube API call shape.

- [ ] **Step 2: Run static repository checks**

Run:

```bash
git diff --check
rg -n "selected_videos|selected_languages|/languages|/error|subtitle|caption" app.py localizations.py localization_service.py templates/home.html tests
```

Expected: the new manual path does not invoke machine translation, no subtitle feature is present, and no whitespace errors are reported. Existing Google Translate/DeepL files, imports, and dependency declarations may remain in this slice because their removal is a separate cleanup task.

- [ ] **Step 3: Update the README workflow section only**

Replace the old “translate selected videos/languages” instructions with the actual first-version flow: select one uploaded video, paste the localization JSON, preview added/changed/unchanged/invalid entries, then publish. State that omitted existing languages are preserved and subtitle files are unsupported. Leave unrelated setup and OAuth documentation unchanged.

- [ ] **Step 4: Review the final diff against the constraints**

Confirm all of the following before declaring the plan implemented:

1. OAuth code and scope remain available.
2. Every publish path fetches current `snippet,localizations` before writing.
3. Any parser/validation issue produces zero `videos.update` calls.
4. Payload generation merges submitted entries into current localizations instead of replacing the map.
5. One valid selected video results in at most one update request.
6. Added, changed, unchanged, and invalid results are visible in the preview response and UI.
7. No subtitle parsing or publishing was added.
8. No unrelated page redesign or batch workflow was introduced.

- [ ] **Step 5: Commit the documentation and final verification adjustments**

```bash
git add README.md
git commit -m "docs: document manual localization workflow"
```

### Task 9: Perform the real YouTube smoke test after automated verification

This task requires explicit access to a non-critical YouTube video and valid OAuth credentials; it is not part of the credential-free automated suite.

- [ ] **Step 1: Confirm the initial state**

Use one non-critical uploaded video with English as the default plus existing Russian and German localizations. Save the observed state before publishing.

- [ ] **Step 2: Preview a mixed change set**

Submit JSON that changes German and adds French and Japanese. Confirm the preview reports `changed` and `added` entries, performs no write, and reports omitted existing languages as preserved.

- [ ] **Step 3: Publish and verify preservation**

Publish the same input once. Confirm English and Russian remain intact, German is updated, and French/Japanese are added. Do not use a critical production video or claim the smoke test passed without observing the final YouTube state.

### Task 10: Keep machine-translation cleanup separate

- [ ] **Step 1: Do not block the manual feature on cleanup**

Leave `google_translate.py`, DeepL configuration, provider dependencies, and legacy translation backend routes/initialization untouched while the manual JSON workflow is being implemented and stabilized. Replacing the homepage controls with the manual editor in Task 7 is part of the V1 UI and is not provider cleanup.

- [ ] **Step 2: Plan cleanup as a separate reviewed change**

Only after the manual flow and smoke test are stable, decide whether to remove unused machine-translation code in a separate commit. Re-run the full suite and update documentation if that cleanup is authorized.
