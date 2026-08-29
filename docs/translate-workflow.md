# Translate workflow

The Translate page uses one safe flow for a selected video:

```text
Select video
    ↓
Source languages
    ↓
Generate missing translations with Codex
or upload JSON from an external LLM
    ↓
Preview changes
    ↓
Publish changes
```

## 1. Select a video and source languages

Select one video in the sidebar. Keep the video's default language selected as
the authoritative source. Existing YouTube localizations may be selected as
optional verified references. Source selection is scoped to the selected video.

The target list and sidebar counts use the live YouTube Data API v3
`i18nLanguages.list` catalog. The default language is not a target localization.

## 2. Generate or upload a translation draft

Choose one of these paths on **Translate**:

- **Generate missing translations with Codex** uses the locally authenticated
  Codex CLI and validates the generated document before it becomes the internal
  translation draft.
- **Upload JSON from an external LLM** uses the prompt from **LLM Translation
  prompt**. Upload one UTF-8 JSON file containing exactly the requested language
  codes. The file is validated before it becomes the internal translation draft.

The draft is read-only in the application. A valid generated or uploaded entry
replaces the matching draft language; other draft entries remain available for
review. An invalid upload shows validation errors and leaves the current valid
draft unchanged.

Each localization value must contain only `title` and `description`. Titles may
contain at most 100 characters and descriptions at most 5,000 characters. Do
not upload wrapper metadata, Markdown, prose, language names, unsupported codes,
or duplicate keys.

## 3. Preview changes

Click **Preview changes** to compare the current valid draft with the selected
video's live YouTube localizations. Preview is read-only and never calls
`videos.update`.

The report identifies added, changed, and unchanged draft entries. It also
reports existing YouTube languages that will be preserved because they are not
in the draft.

## 4. Publish changes

Click **Publish changes** only after a current valid Preview. Publish validates
the draft again and fetches the selected video immediately before writing.

The update uses safe merge semantics:

- a generated or uploaded language replaces the matching existing language;
- existing languages absent from the draft remain in YouTube;
- the default language is kept as the video's primary metadata, not treated as
  a target localization.

After publishing, confirm the result in YouTube Studio. If the selected video
changes, its draft and Preview state are cleared.

## Reset languages

**Reset languages** is a separate destructive sidebar action. After the native
browser confirmation, the app:

1. fetches the latest video resource;
2. preserves the canonical `snippet.defaultLanguage`, current default title and
   description, and writable snippet metadata;
3. sends the default language entry as the YouTube API reset workaround;
4. fetches the video again and verifies that every non-default localization is
   gone and the default metadata is unchanged.

If the default language cannot be determined safely, no destructive update is
sent. If post-write verification finds a remaining non-default localization or
changed default metadata, the operation is reported as failed and no success is
shown. A confirmed successful reset clears the selected video's draft, Preview,
source selection, prompt/upload state, and sidebar cache before refetching live
data.
