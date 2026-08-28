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
- Keep user-facing UI copy and documentation terminology consistent, especially
  for the Manual translate and LLM translate workflows.

## Active workflow rules

- The application has exactly two workflows: Manual translate and LLM
  translate. Do not reintroduce a Machine translate page, provider, state
  namespace, control, dependency, or documentation flow.
- The live YouTube Data API v3 `i18nLanguages.list` OAuth response is the only
  source of valid localization language codes. Never restore a hardcoded
  language map or infer a code from a translated language name.
- The LLM workflow has no provider integration, API key, environment setting,
  or dependency. It copies a prompt for an external LLM; the user downloads
  that LLM's JSON result and uploads it back to the app.
- Progress is `current / total` from live YouTube state, excluding the selected
  video's default language. The supporting LLM Translation prompt page offers
  only currently missing live-catalog languages, selects the first ten by
  default, and rejects more than ten targets.
- LLM prompt context includes only the selected video's default
  `snippet.title`, `snippet.description`, and `snippet.defaultLanguage` when
  available. Existing localizations are used only to calculate progress.
- The external LLM must return one downloadable UTF-8 JSON file: a direct map
  keyed by exactly the requested language codes, with only `title` and
  `description` for every key. Never accept wrapper metadata such as `catalog`,
  `languages`, `outputContract`, `schemaVersion`, or `source`.
- Treat uploads as untrusted: validate them before populating the editable
  form. The shared editor validates before Preview, Preview never writes, and
  Publish revalidates, merges omitted existing localizations, and refreshes the
  selected video from YouTube before showing the next progress value.
