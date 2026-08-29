# Project instructions

## Documentation language and maintenance

- Keep baseline project documentation in English only. Do not add Russian or
  other-language prose to `README.md`, `docs/`, or tool-specific guides until
  an explicit localization policy is introduced.
- Update the relevant documentation in the same change as any code, UI, UX, or
  workflow change. Do not defer documentation updates to a separate task.
- Keep documentation aligned with the current implementation. Remove or revise
  stale control names, flows, routes, and acceptance criteria when behavior
  changes.
- Keep user-facing UI copy and documentation terminology consistent with the
  unified Translate workflow and its supporting LLM Translation prompt page.

## Active workflow rules

- The application has one primary Translate workflow and one supporting LLM
  Translation prompt page. Do not reintroduce separate legacy translate
  workflows, a Machine translate page, provider, state namespace, control,
  dependency, or documentation flow.
- The checked-in `data/youtube-metadata-languages.json` snapshot is the only
  source of valid video metadata localization language codes. The YouTube Data
  API v3 `i18nLanguages.list` response is an application/UI catalog only. Never
  restore live metadata discovery, infer a code from a translated language
  name, substitute captions/audio/ISO lists, or replace the snapshot with a
  fallback. Do not add a runtime dependency on undocumented YouTube Studio
  internals.
- The supporting LLM Translation prompt page has no provider integration, API
  key, environment setting, or dependency. It copies a prompt for an external
  LLM; the user downloads that LLM's JSON result and uploads it back to
  Translate.
- The optional `generate_codex_localizations.py` helper is local CLI automation,
  not a third application workflow or an in-app LLM provider integration. It may
  invoke an installed Codex CLI using saved local authentication, but it must
  never require provider API-key environment variables or publish to YouTube.
  Its generated direct localization JSON becomes the internal Translate draft.
- Progress is `current / total` from live YouTube state and the checked-in
  metadata catalog, excluding the selected video's default language. The
  supporting LLM Translation prompt page offers only currently missing
  metadata-catalog languages, selects the first ten by default, and rejects
  more than ten targets.
- Translation source context always treats the selected video's default
  language and `snippet.title`/`snippet.description` as the authoritative
  primary source. Selected existing localizations contribute their real title
  and description only as optional verified reference translations. Source
  selection is scoped to the selected video and resets when the video changes;
  the same selection is used by Translate and the supporting prompt page.
- The external LLM must return one downloadable UTF-8 JSON file: a direct map
  keyed by exactly the requested language codes, with only `title` and
  `description` for every key. Never accept wrapper metadata such as `catalog`,
  `languages`, `outputContract`, `schemaVersion`, or `source`.
- Treat uploads as untrusted: validate them before they become the internal
  translation draft. Preview never writes, and Publish revalidates, merges
  omitted existing localizations, and refreshes the selected video from YouTube
  before showing the next progress value.
- Codex and valid external-LLM uploads merge into the current translation draft.
  Overlapping language codes replace only that entry; existing YouTube
  localizations omitted from the draft remain preserved during normal Publish.
  Changing the selected video clears its draft and Preview state.
- Reset languages is a separate destructive service operation. Its local
  component requires native browser confirmation, sends only the canonical
  default-language localization with current default title/description as the
  YouTube API workaround, verifies the fresh post-write resource, invalidates
  related state without changing URL parameters, and never uses normal Publish
  merge semantics.
- Sidebar video cards are compact and use metadata-catalog counts: `done` is
  existing known non-default localizations and `undone` is missing non-default
  codes from the checked-in catalog. Numeric Load more appends cursor-backed
  batches; URL page changes reset only the accumulated visible list.
- `FAQ` is a static navigation page. It must not construct a YouTube service, start OAuth, fetch API data, or render the persistent video sidebar, so it remains available when YouTube access fails.
