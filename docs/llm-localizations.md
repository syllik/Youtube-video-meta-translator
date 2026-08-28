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
Open the supporting LLM Translation prompt page and copy the prompt
      ↓
Paste it into an external LLM and download its JSON result
      ↓
Upload the JSON result and validate it locally
      ↓
Automatic validation → Preview changes → Publish changes
```

The app does not call an LLM provider or require an API key. A downloaded file
is untrusted until the local upload validation accepts it; accepted JSON then
remains editable in the shared localization form.

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

## Optional local Codex CLI automation

The existing Streamlit prompt/upload workflow remains unchanged. For repeated
local generation, the optional helper uses an installed Codex CLI with saved
local authentication and hands its direct JSON output to **Manual translate**.
It does not create a third application workflow, integrate a provider into the
app, or publish to YouTube.

Authenticate with ChatGPT sign-in before running it:

```bash
codex login
codex login status
```

No OpenAI API key is required. The helper removes `OPENAI_API_KEY` and
`CODEX_API_KEY` from the child process environment, while retaining the local
Codex authentication context. Usage is subject to the signed-in Codex/ChatGPT
plan limits; this workflow is not free or unlimited.

For every run, the helper fetches the current video and a fresh live YouTube
language catalog through the existing YouTube OAuth service. Only the default
`snippet.title`, `snippet.description`, and `snippet.defaultLanguage` (when
available), together with the current target batch, are sent to Codex. Existing
translations are never sent. Only currently missing non-default catalog targets
are generated, in sequential batches of at most 10 languages, with one retry
for a failed batch.

The generated file is a direct localization JSON map intended for review and
publishing through **Manual translate**, not the exact-selected-batch LLM
uploader. Preview and Publish remain explicit actions in Streamlit; the helper
never auto-publishes.

Cheap first smoke run:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID \
  --max-languages 2 \
  --output localizations-smoke.json
```

Full run:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID
```

Controlled run:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID \
  --batch-size 5 \
  --max-languages 10 \
  --output localizations.json
```

Smaller batches create more Codex calls. The default batch size of 10
minimizes call count while matching the current LLM batch bounds.

## Safe publishing

After upload, inspect and edit the JSON in the form. Click **Preview changes**
before **Publish changes**; Preview never writes to YouTube. Publishing
revalidates the input, refetches the current video, merges submitted
localizations into existing localizations, preserves omitted languages, and
then refreshes the LLM progress from YouTube.

Start with one non-critical video and confirm the result in YouTube Studio.

➡️ [Troubleshooting](troubleshooting.md)
