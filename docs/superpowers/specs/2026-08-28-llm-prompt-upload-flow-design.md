# LLM Prompt and Upload Flow Design

**Date:** 2026-08-28
**Status:** Proposed for implementation review

## Goal

Keep the LLM workflow free of provider API keys and paid API calls. The
application prepares one deterministic prompt for the next ten missing YouTube
localizations, accepts the downloadable JSON produced by an external web LLM,
validates it against the live YouTube catalog, and publishes it through the
existing YouTube localization editor.

The application remains the source of truth for supported language codes and
for the video's actual localization state. An external LLM is an untrusted
translation producer; its output must pass local validation before it can be
previewed or published.

## Scope and boundaries

### In scope

- Keep exactly two workflows: Manual translate and LLM translate.
- Remove OpenAI API calls, `OPENAI_API_KEY`, OpenAI service code, and the
  `openai` dependency.
- Keep live language discovery through the authenticated YouTube Data API v3
  `i18nLanguages.list` response.
- Show a localization progress indicator for the selected video.
- Generate a prompt for at most the next ten missing languages.
- Use only the selected video's default title and description as prompt source
  content.
- Add a JSON file uploader that populates the existing editable localization
  form and validates immediately.
- Re-fetch YouTube state after publish and update the progress indicator from
  the fresh API response.

### Out of scope

- Calling OpenAI, ChatGPT, Claude, Gemini, or another LLM from the application.
- Sending existing localizations to the external LLM as translation context.
- Automatically publishing an uploaded file without Preview/Publish actions.
- Supporting wrapper/package JSON formats in the localization editor.
- Maintaining a static language list or falling back to one when the live API
  response is unavailable.

## User flow

1. The user opens **LLM translate** and selects a video.
2. The page loads the selected video's `snippet` and `localizations`, plus a
   fresh YouTube language catalog.
3. The page moves the user to the translation controls below the video list.
4. The page displays:
   - the original `Title`;
   - the original `Description`;
   - the video's `defaultLanguage`;
   - `YouTube translations: current / total`;
   - the number of missing supported languages;
   - the next target language codes and names.
5. The user clicks **Generate prompt for next 10 languages**. If fewer than ten
   languages remain, the prompt contains all remaining languages.
6. The user copies the single displayed prompt to an external web LLM. The
   prompt requires the LLM to create and attach a downloadable UTF-8 JSON file,
   not a Markdown code block or explanatory text.
7. The user clicks **Upload JSON file** and selects the generated `.json` file.
8. The application decodes the file as UTF-8, validates its exact target key
   set and YouTube localization fields, and places valid content in the
   existing editable JSON form.
9. The user edits the JSON if needed, reviews automatic validation, and uses
   **Preview changes** followed by **Publish changes**.
10. After publishing, the application fetches the video's current YouTube
    localizations again and updates the progress indicator. The next prompt is
    then based on the new missing-language set.

An uploaded but unpublished file does not increase the progress count. The
count represents YouTube state, not local form state.

## Language and progress rules

The live catalog returned by the authenticated YouTube API is the only source
of valid codes. The catalog is ordered by `name.casefold()` for deterministic
selection.

Let:

- `defaultCode` be the selected video's `snippet.defaultLanguage`, matched to
  the live catalog case-insensitively and represented with the catalog's
  canonical casing when present;
- `supportedCodes` be the live catalog codes;
- `existingCodes` be the video's current `localizations` keys matched to live
  catalog codes case-insensitively and represented with canonical casing;
- `localizationCodes` be `supportedCodes` excluding `defaultCode`.

The displayed values are:

- `total = len(localizationCodes)`;
- `current = len(localizationCodes ∩ existingCodes)`;
- `missing = localizationCodes - existingCodes`.

The next prompt targets the first ten entries of `missing` in the catalog's
`name.casefold()` order. The default language is never a target. Existing
localizations are used only to calculate `current` and `missing`; they are not
included in the prompt.

## Prompt contract

The prompt is one copyable block containing:

- a role and task instruction for meaning-preserving YouTube metadata
  translation;
- the default source language;
- the default video's original title and description;
- a `targetLanguages` list containing only the next missing languages, each with
  its exact `code` and display `name`;
- an explicit expected target-code list and expected count;
- strict output and downloadable-file instructions.

The prompt must require the following output contract:

```json
{
  "de": {
    "title": "Translated title",
    "description": "Translated description"
  }
}
```

The output must:

- be a JSON object keyed directly by the exact target language codes;
- contain exactly one `title` and one `description` per target code;
- contain no `source`, `catalog`, `languages`, `outputContract`,
  `schemaVersion`, language names as keys, Markdown fences, or prose;
- preserve meaning, tone, proper names, URLs, hashtags, technical tokens, and
  meaningful line breaks;
- obey YouTube's title and description length limits;
- be attached as a downloadable `.json` file.

The prompt must instruct the external LLM to compare its final key set with
the expected list before creating the file. This is a mitigation, not a trust
boundary; the application validator remains authoritative.

## Upload and validation contract

The uploader accepts JSON files and reads them as UTF-8. On upload, the
application validates the decoded object against the exact current target
codes for the generated prompt:

- the root value is a non-empty JSON object;
- every key is one of the expected target codes, matched case-insensitively and
  stored using the catalog's canonical casing;
- every expected target code appears exactly once after normalization;
- no wrapper or metadata keys are present;
- each value contains only `title` and `description`;
- both fields are strings, `title` is non-empty and within 100 characters, and
  `description` is within 5000 characters.

Invalid files remain out of the form and show actionable paths for missing,
extra, malformed, or over-limit entries. A valid file replaces the form's
submitted localization JSON for the current batch and remains editable.

The existing localization merge behavior remains responsible for preserving
YouTube localizations omitted from the submitted JSON at publish time. The
uploaded batch therefore needs to contain only the next missing languages.

## Application changes

- Refactor the existing LLM prompt helper so it builds context from the
  default source and target languages only; it must not include
  `existingLocalizations`.
- Replace the current OpenAI generation control with:
  - progress and missing-language summary;
  - next-ten target selection;
  - copyable prompt display;
  - JSON file uploader;
  - direct handoff to the shared manual editor state.
- Add exact-batch validation while retaining the shared YouTube localization
  validation and preview/publish behavior.
- Re-fetch the selected video after a successful publish before calculating
  progress or generating the next prompt.
- Remove `services/openai_translation_service.py`, its tests, OpenAI-specific
  state and error handling, the `openai` requirement, and active documentation
  for OpenAI API keys, model configuration, or billing.
- Keep the Google OAuth flow and live `i18nLanguages.list` catalog unchanged.
- Update `AGENTS.md`, `README.md`, and active documentation so they describe
  the prompt-copy → external LLM downloadable JSON → upload → validate →
  preview → publish flow.

## Test strategy

Add or update credential-free tests for:

- progress calculation with existing codes and default-code exclusion;
- deterministic next-ten selection using `name.casefold()`;
- prompt source containing only the default title/description and target list,
  with no existing localization content;
- exact-batch acceptance of a valid direct map;
- rejection of missing, extra, wrapper, malformed, and over-limit data;
- UTF-8 file loading and handoff into the editor state;
- the LLM page exposing the uploader and not constructing an OpenAI client;
- publish followed by a fresh YouTube-state progress calculation.

Existing Manual workflow tests must continue to pass, including preservation of
omitted localizations and validation before any YouTube write.

## Acceptance criteria

- No active application code, dependency, environment variable, or current
  documentation requires an OpenAI API key.
- Selecting a video shows the actual `current / total` YouTube localization
  progress and the next missing targets.
- The generated prompt contains only default source metadata and no existing
  localization content.
- The external LLM can be instructed to create a downloadable JSON file whose
  root is directly compatible with the YouTube localization API.
- Uploading a valid batch fills the editable form and uploading invalid JSON
  cannot make Preview or Publish available.
- After publish, the count is based on a fresh YouTube API response.
- The complete credential-free test suite, compilation check, dependency check,
  and diff checks pass.
