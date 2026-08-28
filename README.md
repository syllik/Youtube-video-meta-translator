# 🎬 YouTube Video Metadata Translator

A local Streamlit app for managing YouTube video titles and descriptions.

You can choose between two workflows:

- 🧩 **Manual translate** — choose one video from the persistent sidebar, fetch YouTube's live language
  catalog through OAuth, edit localization JSON, validate it, preview the
  diff, and publish changes while preserving omitted languages.
- ✨ **LLM translate** — copy a prompt for an external LLM, download its JSON
  result, upload it, then validate and review it before publishing.

Both workflows use a `Select` button on each video card and the same explicit
preview-before-publish flow. The sidebar remains available on both workflows
and on the supporting LLM Translation prompt page, so the selected video is
shared everywhere.

## 🧭 Start here

👉 **[Open the documentation hub](docs/README.md)** to choose a path.

| | Open this guide | When to use it |
| --- | --- | --- |
| 🚀 | [Getting started](docs/getting-started.md) | Install the project and launch it for the first time. |
| 🔐 | [Configuration](docs/configuration.md) | Set up the YouTube OAuth client. |
| 🧩 | [Manual localizations](docs/manual-localizations.md) | Edit, validate, preview, and publish localization JSON. |
| ✨ | [LLM localizations](docs/llm-localizations.md) | Use an external LLM safely with a prompt and JSON upload. |
| 🆘 | [Troubleshooting](docs/troubleshooting.md) | Fix setup, OAuth, dependency, port, or API problems. |
| 🛡️ | [Security](docs/security.md) | Protect credentials and local token files. |
| 🛠️ | [Development](docs/development.md) | Run tests and work on the repository. |

The emoji markers are navigation hints: `🚀` means start, `🔐` means
credentials, `🧩` means manual editing, `✨` means LLM generation, and `🆘`
means help.

## ⚡ Quick start

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Streamlit opens the local app in your browser. If it does not, open
[http://127.0.0.1:8501](http://127.0.0.1:8501). Before the first launch, place the YouTube OAuth file at
`config/account_client_secrets_main.json`. The complete setup is in
[Getting started](docs/getting-started.md) and [Configuration](docs/configuration.md).

### 🪟 Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## ✅ Two-step translation flow

1. Start with one non-critical video.
2. Open the supporting **LLM Translation prompt** page from the app navigation,
   select up to ten missing live-catalog targets, and copy the native code block.
   The first ten missing targets are selected by default.
3. Paste the prompt into an external LLM and download its direct UTF-8 JSON
   result. The prompt contains only the selected video's default metadata.
4. Upload the file on **LLM translate**. The app validates exact requested
   language codes and the `title`/`description` shape before filling the
   editable JSON form.
5. Edit the JSON if needed, then click **Preview changes**. Preview never
   writes to YouTube.
6. Click **Publish changes** only when the JSON is valid. Publish refetches
   the current video, merges omitted localizations, and refreshes progress.
7. Confirm the result in YouTube Studio.

For fully manual work, use **Manual translate** and paste a direct JSON object
keyed by YouTube language codes into the same editor.

The persistent left sidebar shows channel details, channel and RSS links,
refresh, page-size controls, pagination, and the latest 10 uploads by default.
Use `10`, `20`, `50`, or `all` in the page-size control; the selected page and
limit are kept in the URL for refreshes and sharing. Click a video thumbnail to
open it on YouTube; the card's ID, default language, localization badges, and
`Select`/`Selected` control are shown below the thumbnail.

The Manual localizations editor is collapsed while idle and opens automatically
when JSON, validation feedback, or a preview result is present. Its example is
a direct JSON object containing ten codes validated against YouTube's current
live language catalog.

The manual editor re-fetches current YouTube state before publishing and keeps
existing localizations omitted from the submitted JSON.

The language catalog is never hardcoded. Both pages use the current OAuth
response of YouTube Data API v3 `i18nLanguages.list` at the time the video is
selected. No OpenAI or other LLM API key is required; YouTube still uses the
existing OAuth session, not `YOUTUBE_API_KEY`.

## 📚 Project documentation

- [Documentation hub](docs/README.md)
- [Development and tests](docs/development.md)
- [Security checklist](docs/security.md)

## 🔒 Credentials

Never commit OAuth JSON, `.env`, `token.json`, or `token.pickle`. See
[Security](docs/security.md) and [Configuration](docs/configuration.md).

## 📜 License

See [LICENSE](LICENSE).
