# ✨ LLM localizations

Use this workflow to prepare title and description localizations with an
external LLM without connecting an LLM provider API to this project.

⬅️ [Back to documentation](README.md) · ➡️ [Manual localizations](manual-localizations.md)

## End-to-end flow

```text
Select one video in the persistent sidebar
      ↓
Fetch the current YouTube i18nLanguages.list catalog through OAuth
      ↓
Fetch the video's default title/description and existing localizations
      ↓
Click **Generate missing translations** for local Codex CLI batching, or open
the supporting LLM Translation prompt page and copy the prompt
      ↓
Automatic generation loads one merged JSON result, or paste the prompt into an
external LLM and download its JSON result
      ↓
Upload the fallback JSON result and validate it locally
      ↓
Edit → Preview changes → Publish changes
```

The app does not call an LLM provider or require an API key. The automatic
button uses the existing locally authenticated Codex CLI batching helper to
generate every currently missing language in sequential batches of at most ten
and loads one merged JSON object into the editor. The downloaded fallback file
is untrusted until local upload validation accepts it; either result remains
editable in the shared localization form.

## Choose targets and copy the prompt

The LLM Translation prompt page shows `YouTube translations: current / total`
progress from the selected video's current YouTube localizations. The selected
video's default language is excluded from both values. Its live-catalog
multiselect contains only missing target languages, selects the first ten
missing targets by default, and allows no more than ten selections.

Copy the prompt from the read-only native Streamlit code block, paste it into an external LLM, and ask for one attached,
downloadable UTF-8 `.json` file. The prompt includes the default title,
description, and default-language code when available, plus the exact selected
target codes. Existing localizations are not sent as prompt context.

The prompt page includes convenience links to [ChatGPT](https://chatgpt.com/),
[Google Gemini](https://gemini.google.com/), [Claude](https://claude.ai/),
[Microsoft Copilot](https://copilot.microsoft.com/),
[Perplexity](https://www.perplexity.ai/), and
[Mistral](https://chat.mistral.ai/). These links only open those websites; the
app sends no video data to them. Free-tier access can vary by account, region,
and provider limits.

## What is sent for context

Each request contains:

- the selected video's `snippet.title`;
- the selected video's `snippet.description`;
- `snippet.defaultLanguage`, when YouTube provides it;
- the current batch of up to 10 live YouTube language entries, including their
  exact BCP-47 codes.

The default title and description are always the translation source.
Existing localizations are used only for progress and missing-target calculation.

## Output contract

The model must return one direct JSON object:

```json
{
  "de": {
    "title": "German title",
    "description": "German description"
  },
  "fr": {
    "title": "French title",
    "description": "French description"
  }
}
```

Upload this exact downloadable JSON file on **LLM translate**. The app checks
UTF-8 decoding, the exact requested key set, duplicate keys, field types, and
YouTube length limits before it updates the editable form. Wrapper objects are
invalid. Do not use keys such
as `catalog`, `languages`, `outputContract`, `schemaVersion`, or `source` as
localization keys; those caused the old pasted-package errors.

The prompt also requires meaning-preserving translation, proper names, URLs,
hashtags, technical tokens, tone, and meaningful line breaks to be preserved.
Titles are limited to 100 characters and descriptions to 5,000 characters.

## Configuration

No OpenAI or other LLM API key is required. The live catalog and publishing
use the existing Google OAuth setup; see [Configuration](configuration.md).

## Automatic local Codex CLI generation

Automatic Codex translation requires the local Codex CLI. Installing the
Python requirements does not install it. Node.js and npm must be available for
this installation method.

Install and verify the CLI:

```bash
npm install -g @openai/codex
codex --version
```

Authenticate the local CLI with the ChatGPT sign-in flow and verify the
session:

```bash
codex login
codex login status
```

No OpenAI API key is required. The helper removes `OPENAI_API_KEY` and
`CODEX_API_KEY` from the child process environment, while retaining the local
Codex authentication context. Usage follows the limits of the signed-in
ChatGPT/Codex account; this workflow is not free or unlimited.

On **LLM translate**, click **Generate missing translations** to check the
Codex login and generate all currently missing non-default catalog targets.
The current Streamlit implementation:

- calculates missing translations from the selected video's current YouTube
  state and fresh live language catalog;
- processes the missing languages in sequential batches of 1–10;
- validates each batch, retries a failed Codex batch once, and stops with an
  error if the retry also fails;
- merges the validated batches and validates the final direct localization map;
- loads the merged JSON into the existing editable localization editor.

This reuses the existing editor; it does not create a separate automatic
publishing workflow or integrate an LLM provider into the app.

For every run, the helper fetches the current video and a fresh live YouTube
language catalog through the existing YouTube OAuth service. Only the default
`snippet.title`, `snippet.description`, and `snippet.defaultLanguage` (when
available), together with the current target batch, are sent to Codex. Existing
translations are never sent. Only currently missing non-default catalog targets
are generated, in sequential batches of at most 10 languages. The CLI helper
uses one retry for a failed batch.

The CLI command is generation-only. It reads the YouTube state and live catalog
needed to construct missing targets, then writes local JSON; it does not
publish translations to YouTube. The generated file is a direct localization
JSON map for inspection and editing in the existing localization editor.

### Recommended first smoke test

After `codex login status` succeeds, start with a small real run:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID \
  --max-languages 2 \
  --output /tmp/smoke.json
```

Expected terminal output has this shape:

```text
Generated 2 localizations -> /tmp/smoke.json
```

Inspect the direct localization map:

```bash
python -m json.tool /tmp/smoke.json
```

The output must be one direct map, for example:

```json
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

Do not expect wrapper objects such as:

```json
{ "localizations": {} }
```

or:

```json
{ "languages": {} }
```

### Verify batching and merge

To force more than one batch while keeping the run small:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID \
  --batch-size 2 \
  --max-languages 3 \
  --output /tmp/batching.json
```

Expected terminal progress should resemble:

```text
Codex batch 1/2: ...
Codex batch 2/2: ...
Generated 3 localizations -> /tmp/batching.json
```

Then inspect the final object:

```bash
python -m json.tool /tmp/batching.json
```

The final file should contain all three language entries in one JSON object.
This verifies:

```text
batch → Codex → validate → next batch → validate → merge → one localization JSON
```

`--batch-size` must be between 1 and 10. Smaller batches create more Codex
calls; a failed batch is retried once by the current helper. `--max-languages`
limits the number of missing targets selected for that run.

### Generation versus publishing

The CLI command only generates a local file. It never publishes translations.
Use this safe application sequence when you are ready to review the result:

```text
Select video
    → LLM translate
    → Generate missing translations
    → inspect/edit generated JSON
    → Preview changes
    → Publish changes
```

**Generate missing translations** must not publish, and **Preview changes**
must not publish. Only the explicit **Publish changes** action writes
localization changes to YouTube. Test generation and Preview before testing
Publish.

## Safe publishing

After upload, inspect and edit the JSON in the form. Click **Preview changes**
before **Publish changes**; Preview never writes to YouTube. Publishing
revalidates the input, refetches the current video, merges submitted
localizations into existing localizations, preserves omitted languages, and
then refreshes the LLM progress from YouTube.

Start with one non-critical video and confirm the result in YouTube Studio.

➡️ [Troubleshooting](troubleshooting.md)
