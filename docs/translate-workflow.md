# Translate workflow

The Translate page uses one safe flow for a selected video:

```text
Select video
→ Primary source + optional reference translations
→ Target languages
→ Codex or External LLM
→ Preview changes
→ Publish changes
→ refreshed current state
```

## 1. Select a video and source languages

Select one video in the sidebar. Keep the video's default language selected as
the authoritative source. Existing YouTube localizations may be selected as
optional verified references. Source selection is scoped to the selected video.
The primary source is shown as read-only information. Only existing
localizations can be selected as optional reference translations; clearing all
references still leaves the primary source selected.

The target list and sidebar counts use the checked-in
`data/youtube-metadata-languages.json` metadata catalog. The default language is
not a target localization. Its snapshot records the scope, provenance, review
date, count, canonical BCP-47 codes, and deterministic English display names
used by the app. Selectors show each code first, for example `ru — Russian`;
the exact code remains the state and JSON key.

Immediately after **Source languages**, **Target languages** contains only
currently missing catalog languages and excludes every selected source code.
The primary Translate page selects all of those targets by default and allows
any subset, including more than ten languages. Target selection is scoped to
the selected video and is recalculated when the video or source selection
changes. The supporting **LLM Translation prompt** page remains capped at ten
targets.

## 2. Generate or upload a translation draft

Choose one of these paths on **Translate**:

- **Generate missing translations with Codex** uses the locally authenticated
  Codex CLI, validates each batch, and merges each successful batch into the
  internal translation draft before starting the next one. Each interaction
  runs one batch of up to ten targets so the page returns to the user between
  batches.
- **Upload JSON from an external LLM** uses the prompt from **LLM Translation
  prompt**. Upload one UTF-8 JSON file containing exactly the requested language
  codes. The file is validated before it becomes the internal translation draft.

The draft is read-only in the application. A valid generated or uploaded entry
replaces the matching draft language; other draft entries remain available for
review. An invalid upload shows validation errors and leaves the current valid
draft unchanged.

The **Download JSON** control is beside generation on **Translate**. It is
disabled for an empty draft and downloads the whole current internal draft as
`<video-id>-localizations.json`, not a raw Codex response or YouTube resource.
After a successful Codex batch, the download is available immediately, before
the remaining batches run. Click **Generate missing translations** again to
continue. Retry work subtracts every valid selected target already present in
the draft, whether it came from an earlier Codex checkpoint or an external
upload. If a later batch fails, that failed batch is not merged and earlier
checkpoints remain available for Preview and Download.

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
in the draft. Language labels use the same code-first format, such as
`ru — Russian`.

## 4. Publish changes

Click **Publish changes** only after a current valid Preview. Publish validates
the draft again and fetches the selected video immediately before writing. It
compares a semantic publish-relevant snapshot with the resource reviewed in
Preview: the video ID, `WRITABLE_SNIPPET_FIELDS`, and `localizations`. ETag
changes and read-only response fields alone do not create a false conflict.
If publish-relevant YouTube state changed in the meantime, no update is sent
and the app asks you to Preview again. When YouTube provides an ETag, the
freshly fetched value is still used as the conditional `If-Match` write guard;
a race that returns HTTP 412 remains a no-write conflict. After a successful
write, the sidebar video-page cache is cleared before rerun, so the
localization count is fetched again automatically.

The update uses safe merge semantics:

- a generated or uploaded language replaces the matching existing language;
- existing languages absent from the draft remain in YouTube;
- the default language is kept as the video's primary metadata, not treated as
  a target localization.

After publishing, confirm the result in YouTube Studio. A successful Publish
clears the video-page cache before rerun, so the sidebar count reflects the
fresh YouTube state without a manual Refresh. If the selected video changes,
its draft and Preview state are cleared.

Publish has mutually exclusive visible outcomes: a successful write clears the
cache and refreshes the page; a valid no-change result reports that there is
nothing to publish; a conflict or service error reports failure and does not
claim that the cache was refreshed.

Any draft mutation, including a newly checkpointed batch or a valid upload,
invalidates the previous Preview. Preview the complete current draft again
before publishing.

## Reset languages

**Reset languages** is a separate destructive sidebar action in the collapsed
**Danger zone** for the current selected video. It is not rendered on every
video card and appears directly below **Refresh video list**. After the native
browser confirmation, the app:

1. fetches the latest video resource for the exact selected video;
2. requires a usable fresh ETag and sends a conditional `If-Match` update;
3. preserves the canonical `snippet.defaultLanguage`, current default title,
   description, and writable snippet metadata;
4. sends the default language entry as the YouTube API reset workaround;
5. fetches the video again and verifies that every non-default localization is
   gone and the default metadata is unchanged.

Reset never falls back to an unconditional destructive update. A changed
selection or HTTP 412 is a no-write conflict with no automatic retry and
requires a new explicit confirmation. The reset also refuses to write when the
default language or a usable ETag is unavailable. If post-write verification
finds a remaining non-default localization or changed default metadata, the
operation is reported as failed and no success is shown. A confirmed
successful reset clears the selected video's draft, Preview, source selection,
prompt/upload state, and sidebar cache before refetching live data.
