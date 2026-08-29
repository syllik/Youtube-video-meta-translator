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
  Translation prompt page. Do not reintroduce separate Manual translate or LLM
  translate workflows, a Machine translate page, provider, state namespace,
  control, dependency, or documentation flow.
- The live YouTube Data API v3 `i18nLanguages.list` OAuth response is the only
  source of valid localization language codes. Never restore a hardcoded
  language map or infer a code from a translated language name.
- The supporting LLM Translation prompt page has no provider integration, API
  key, environment setting, or dependency. It copies a prompt for an external
  LLM; the user downloads that LLM's JSON result and uploads it back to
  Translate.
- The optional `generate_codex_localizations.py` helper is local CLI automation,
  not a third application workflow or an in-app LLM provider integration. It may
  invoke an installed Codex CLI using saved local authentication, but it must
  never require provider API-key environment variables or publish to YouTube.
  Its generated direct localization JSON is reviewed in the Translate editor.
- Progress is `current / total` from live YouTube state, excluding the selected
  video's default language. The supporting LLM Translation prompt page offers
  only currently missing live-catalog languages, selects the first ten by
  default, and rejects more than ten targets.
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
- Treat uploads as untrusted: validate them before populating the editable
  form. The shared editor validates before Preview, Preview never writes, and
  Publish revalidates, merges omitted existing localizations, and refreshes the
  selected video from YouTube before showing the next progress value.
