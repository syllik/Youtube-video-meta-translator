# ✨ LLM Translation prompt and Codex generation

**Translate** supports both local Codex generation and an external-LLM JSON
handoff. The supporting **LLM Translation prompt** page is for users who do not
use the local Codex CLI.

⬅️ [Back to documentation](README.md) · ➡️ [Translate workflow](translate-workflow.md)

## Source and target model

For the selected video:

- `snippet.defaultLanguage`, title, and description form the authoritative
  **primary source**;
- selected existing localizations contribute their real title and description
  as optional verified **reference sources**;
- references clarify intent, tone, and nuance but never compete with the
  primary source;
- target languages are currently missing metadata-catalog languages, excluding
  the default and every selected source language.

Source selection is shared between **Translate** and this supporting page while
the same video is selected. The primary source is displayed separately as
read-only information. Only existing localizations are optional reference
choices; clearing them still leaves the primary source selected. The selection
resets when the video changes and is not stored permanently.

The video metadata catalog comes from the checked-in
`data/youtube-metadata-languages.json` snapshot; codes retain its canonical
casing. The separate `i18nLanguages.list` helper is not used for metadata
localization validation. The public Data API documents no exhaustive
`metadataLanguages.list` endpoint, so this reviewable snapshot is intentional.

## Use an external LLM

On **Translate**, the complete external path is visible before preparation:

1. **Prepare prompt** on the supporting **LLM Translation prompt** page.
2. Generate JSON in an external LLM.
3. **Upload JSON** on **Translate**.

The upload control stays inactive until the prepared prompt matches the current
video and exact target-language tuple. Its binding includes the video ID,
target codes, and uploaded file SHA-256. A stale prompt or target set cannot
unlock the uploader.

On the prompt page, select a video and choose source languages on **Translate**
or this page. Choose up to ten missing target languages; the first ten are
selected by default. Copy the prepared prompt from the native read-only code
block, paste it into an external LLM, and ask for one downloadable UTF-8 JSON
file. Return to **Translate** and upload the file; it becomes the internal
translation draft after validation. Then click **Preview changes**, review the
diff, and explicitly **Publish changes**.

The app does not send data to linked websites or require an LLM provider API
key. Convenience links are available for [ChatGPT](https://chatgpt.com/),
[Google Gemini](https://gemini.google.com/), [Claude](https://claude.ai/),
[Microsoft Copilot](https://copilot.microsoft.com/),
[Perplexity](https://www.perplexity.ai/), and
[Mistral](https://chat.mistral.ai/).

### Source-language quality guide

Translation always uses the default source as the authoritative meaning. One
source can miss nuance, so use at least two source languages when possible. Two
or three strong translations are a good target; roughly two to five references
from different language families can give the LLM useful context. References
remain optional and never replace the default source.

The prompt includes only the source package and exact target metadata. Its
semantic contract is equivalent to:

```json
{
  "source": {
    "primary": {
      "languageCode": "en",
      "title": "Primary title",
      "description": "Primary description"
    },
    "references": [
      {
        "languageCode": "ru",
        "title": "Verified Russian title",
        "description": "Verified Russian description"
      }
    ]
  },
  "targetLanguages": [{"code": "ja", "name": "Japanese"}],
  "expectedLanguageCodes": ["ja"],
  "expectedCount": 1
}
```

The model must treat `source.primary` as authoritative, use references only to
clarify meaning and tone, translate every exact requested target, and preserve
names, URLs, hashtags, technical tokens, and meaningful line breaks.

## Output contract

Return only a direct JSON object keyed by exactly the requested language codes:

```json
{
  "ja": {
    "title": "Japanese title",
    "description": "Japanese description"
  }
}
```

Do not return Markdown, prose, or wrapper keys such as `catalog`, `languages`,
`outputContract`, `schemaVersion`, or `source`. Every value must contain only
`title` and `description`; titles are limited to 100 characters and
descriptions to 5,000 characters. **Translate** validates UTF-8, exact keys,
duplicate keys, fields, and length before the JSON reaches Preview.

## Automatic local Codex CLI generation

The optional CLI helper uses an installed, locally authenticated Codex CLI. It
does not add an in-app provider, require an API key, or publish to YouTube.

Install or update the CLI using the
[official Codex CLI instructions](https://developers.openai.com/codex/cli/),
then authenticate with the ChatGPT sign-in flow:

```bash
codex --version
codex login
codex login status
```

The app starts Codex child processes with an explicit runtime/auth environment
allowlist, uses ephemeral read-only execution, bounds login and batch execution
time, validates every batch, retries a failed batch once, merges the results,
and loads the direct document into the same Translate draft. Every batch
receives the same selected primary/reference source context.

Run a small generation-only smoke test:

```bash
npm run youtube:codex-localize -- \
  --video-id VIDEO_ID \
  --max-languages 2 \
  --output /tmp/smoke.json
python -m json.tool /tmp/smoke.json
```

The output is a local translation document only. Review it in **Translate**
before publishing. It merges into the current translation draft instead of
replacing unrelated language entries. An overlapping language code replaces
only that entry.

## Safety boundary

Generation and upload never publish automatically. Preview never writes to
YouTube. Publish revalidates the JSON, refetches current YouTube state, rejects
changes since the reviewed Preview, conditionally writes when an ETag is
available, merges submitted localizations with the current set, preserves
omitted languages, and requires a current valid Preview.

Use **Reset languages** only when you intentionally want to delete every
localization for one video. It is a separate destructive operation with native
browser confirmation in the selected-video **Danger zone**. It requires a fresh
ETag and conditional `If-Match` write; missing ETag, changed selection, or HTTP
412 means no accepted write and no automatic retry. Normal omitted-key Publish
behavior is unchanged.

➡️ [Troubleshooting](troubleshooting.md)
