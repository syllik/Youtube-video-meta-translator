# 🛠️ Development

Use this guide when changing the project or checking a local checkout without
calling the live YouTube API.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🧱 Project structure

```text
Youtube-video-meta-translator/
├── streamlit_app.py                 # Streamlit entry point and common bootstrap
├── pages/                           # Machine and manual workflow pages
├── services/                        # YouTube, machine, and manual boundaries
├── state/                           # Common, machine, and manual session state
├── ui/                              # Shared and mode-specific widgets
├── models.py                        # Shared immutable data models
├── youtube_account.py               # YouTube OAuth, listing, publishing
├── localizations.py                 # JSON validation, diff, and merge logic
├── localization_service.py          # Pure manual validation/publish orchestration
├── google_translate.py              # Google Cloud Translation wrapper
├── requirements.txt                 # Python dependencies
├── tests/                           # Credential-free automated tests
├── docs/                            # User and project documentation
├── config/                          # Local credentials; never commit
├── .env                             # Optional local DeepL key; never commit
└── token.json                       # Local OAuth session; generated locally
```

The provider module remains because machine translation is still supported.
The manual editor is implemented separately so its validation and merge logic
can be tested without credentials.

## 🧪 Run automated tests

Activate `.venv`, then run:

```bash
python -m unittest discover -s tests -v
```

The suite uses mocks and does not require live YouTube credentials. A real
YouTube smoke test is intentionally separate because publishing changes an
external channel.

## 🧹 Run local checks

```bash
python -m compileall -q streamlit_app.py pages models.py services state ui google_translate.py youtube_account.py localizations.py localization_service.py youtube_languages tests
git diff --check
git diff --cached --check
python -m pip check
```

The dependency check may print a pip cache-permission warning; the relevant
success result is `No broken requirements found.`

## 🧩 Manual editor boundaries

- Local JSON validation runs before preview; preview never writes.
- Publish validates again, refetches current state, and performs at most one
  update for one video.
- Existing localizations omitted from the submitted JSON are preserved.
- Machine translation and manual localization code are kept separate.

Read the [manual editor context](manual-localization-editor-context.md) for the
full product constraints and review checklist.

## 📝 Documentation changes

Keep `README.md` as the short entry point. Put long instructions in the
smallest relevant file under `docs/`, add a link from [the documentation
index](README.md), and use relative links so the guides work on GitHub and in a
local checkout.

## ➡️ Next step

- [Run the test suite](../tests/)
- [Handle a setup problem](troubleshooting.md)
- [Review security rules](security.md)
