# 🛠️ Development

Use this guide when changing the project or checking a local checkout without
calling the live YouTube API.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🧱 Project structure

```text
Youtube-video-meta-translator/
├── streamlit_app.py                 # Streamlit entry point and common bootstrap
├── pages/                           # Manual and LLM workflow pages
├── services/                        # YouTube and Manual boundaries
├── state/                           # Common, Manual, and LLM session state
├── ui/                              # Shared and workflow-specific widgets
│   ├── sidebar.py                   # Persistent channel and video navigation
│   └── badges.py                    # Shared localization badge renderer
├── models.py                        # Shared immutable data models
├── language_catalog.py              # Validated live YouTube language catalog
├── llm_localization_package.py     # LLM context, prompt, schema, and validation
├── youtube_account.py               # YouTube OAuth, listing, and publishing
├── localizations.py                 # JSON validation, diff, and merge logic
├── localization_service.py          # Manual/LLM preview and publish orchestration
├── requirements.txt                 # Python dependencies
├── tests/                           # Credential-free automated tests
├── docs/                            # User and project documentation
├── config/                          # Local OAuth credentials; never commit
└── token.json                       # Local OAuth session; generated locally
```

The Manual and LLM pages share the YouTube and localization boundaries and the
common selected video stored in session state. The persistent sidebar renders
channel details, links, pagination, and video cards on all workflow pages. The
LLM path creates a prompt for an external tool and validates the uploaded JSON
before it reaches the editor; it has no provider client. The prompt is shown in
Streamlit's native read-only code block, and the Manual editor is an expander.

## 🧪 Run automated tests

Activate `.venv`, then run:

```bash
python -m unittest discover -s tests -v
```

The suite uses mocks and does not require live YouTube or LLM credentials.
A real YouTube smoke test is intentionally separate because publishing changes
an external channel.

## 🧹 Run local checks

```bash
python -m compileall -q streamlit_app.py pages models.py language_catalog.py llm_localization_package.py services state ui youtube_account.py localizations.py localization_service.py tests
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
- Manual validation and the LLM prompt use the same fresh
  `i18nLanguages.list` catalog for the Streamlit session.
- LLM progress excludes the default language; prompt targets are a live-catalog
  subset of missing languages, with the first ten selected by default and a
  hard limit of ten.
- Prompt context is default-video metadata only. An uploaded file must be an
  exact direct language-keyed YouTube map; wrapper metadata is never accepted.
- Preview never writes. Publish revalidates, refetches current state, merges
  omitted localizations, and refreshes the displayed YouTube progress.

Read [Manual editor context](manual-localization-editor-context.md) and
[LLM localizations](llm-localizations.md) for the product constraints.

## 📝 Documentation changes

Keep `README.md` as the short entry point. Put long instructions in the
smallest relevant file under `docs/`, add a link from [the documentation
index](README.md), and use relative links so the guides work on GitHub and in a
local checkout.

## ➡️ Next step

- [Run the test suite](../tests/)
- [Handle a setup problem](troubleshooting.md)
- [Review security rules](security.md)
