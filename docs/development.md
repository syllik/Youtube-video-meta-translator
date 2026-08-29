# 🛠️ Development

Use this guide when changing the project or checking a local checkout without
calling the live YouTube API.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🧱 Project structure

```text
Youtube-video-meta-translator/
├── streamlit_app.py                 # Streamlit entry point and common bootstrap
├── pages/                           # Translate, prompt, and static FAQ pages
├── services/                        # YouTube and localization boundaries
├── state/                           # Common, universal editor, and prompt state
├── ui/                              # Shared and workflow-specific widgets
│   ├── sidebar.py                   # Persistent channel and video navigation
│   ├── faq.py                       # Static FAQ content with no API bootstrap
│   └── badges.py                    # Shared localization badge renderer
├── models.py                        # Shared immutable data models
├── language_catalog.py              # Validated live YouTube language catalog
├── llm_localization_package.py      # Source context, prompt, schema, validation
├── codex_localization_runner.py      # Isolated non-interactive Codex batch call
├── codex_localization_generator.py   # Missing-target batching/retry/merge
├── generate_codex_localizations.py   # Optional local CLI entry point
├── youtube_account.py               # YouTube OAuth, listing, and publishing
├── localizations.py                 # JSON validation, diff, and merge logic
├── localization_service.py          # Preview and publish orchestration
├── requirements.txt                 # Python dependencies
├── tests/                           # Credential-free automated tests
├── docs/                            # User and project documentation
├── config/                          # Local OAuth credentials; never commit
└── token.json                       # Local OAuth session; generated locally
```

The Translate page and supporting prompt page share the YouTube boundary,
selected video, source selection, and live catalog stored in session state.
Translate owns one universal Manual edit/preview/publish state. The prompt page
owns only target and prompt/upload state. The default source is authoritative;
selected existing localizations are optional verified references with real
title/description metadata. Source selection resets when the selected video
changes. Manual edit drafts survive normal reruns and reload only on explicit
lifecycle events. The persistent sidebar renders compact cards, live-catalog
counts, cursor-backed Load more, and destructive Reset languages on both pages.
FAQ is static and intentionally bypasses YouTube bootstrap and OAuth.

## 🧪 Run automated tests

Activate `.venv`, then run:

```bash
python -m unittest discover -s tests -v
```

The suite mocks both Codex and YouTube, consumes no Codex quota, and does not
require live YouTube or LLM credentials. A real YouTube smoke test is
intentionally separate because publishing changes an external channel.

The optional local Codex CLI is not installed by `requirements.txt`. Its real
generation smoke tests and batching checks are documented in
[LLM localizations](llm-localizations.md#recommended-first-smoke-test); do not
run them as part of the credential-free suite.

## 🧹 Run local checks

```bash
python -m compileall -q streamlit_app.py pages models.py language_catalog.py llm_localization_package.py codex_localization_runner.py codex_localization_generator.py generate_codex_localizations.py services state ui youtube_account.py localizations.py localization_service.py tests
git diff --check
git diff --cached --check
python -m pip check
```

The dependency check may print a pip cache-permission warning; the relevant
success result is `No broken requirements found.`

## 🧩 Workflow boundaries

- Local JSON validation runs before preview; preview never writes.
- Publish validates again, refetches current state, and performs at most one
  update for one video.
- Existing localizations omitted from submitted JSON are preserved.
- Manual edit starts from current live localizations, while deleting a key in the
  draft does not delete it from YouTube during normal Publish.
- Codex and external-LLM JSON merge into the current draft; they do not replace
  unrelated language entries.
- Reset languages is the only full-localization deletion path and preserves
  default metadata through a separate reset payload.
- Numeric Load more appends cached cursor pages; changing URL page resets the
  accumulated visible list. It is hidden for `all`.
- Translate and the supporting prompt use the same fresh `i18nLanguages.list`
  catalog and source selection for the Streamlit session.
- Progress excludes the default language and all selected source languages;
  prompt targets are a live-catalog subset of missing languages, with the first
  ten selected by default and a hard limit of ten.
- Codex and external prompts receive the same primary/reference source model.
  An uploaded file must be an exact direct language-keyed YouTube map; wrapper
  metadata is never accepted.
- Preview never writes. Publish revalidates, refetches current state, merges
  omitted localizations, and refreshes the displayed YouTube progress.
- `FAQ` can render without YouTube service construction, OAuth, or API access.

Read [Translate workflow](manual-localizations.md) and
[LLM Translation prompt](llm-localizations.md) for the product constraints.

## 📝 Documentation changes

Keep `README.md` as the short entry point. Put long instructions in the
smallest relevant file under `docs/`, add a link from [the documentation
index](README.md), and use relative links so the guides work on GitHub and in a
local checkout.

## ➡️ Next step

- [Run the test suite](../tests/)
- [Handle a setup problem](troubleshooting.md)
- [Review security rules](security.md)
