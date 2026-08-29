# 🎬 YouTube Video Metadata Translator

A local Streamlit app for managing YouTube video titles and descriptions.

The app has one primary workflow, **Translate**. Select a video, choose its
source languages, generate translations with the local Codex CLI or provide
JSON manually/from an external LLM, then edit, validate, preview, and publish
the result safely. The supporting **LLM Translation prompt** page prepares a
prompt for users who do not use local Codex.

Both pages use the same selected video and source-language state. The default
YouTube language is always the authoritative primary source. Existing
localizations may be selected as optional verified reference translations; the
selection resets when the video changes.

The optional Codex CLI helper can automate missing-language generation outside
Streamlit. It produces direct localization JSON for review in the Translate
editor, never publishes by itself, and uses local ChatGPT/Codex authentication
without an API key; see [LLM localizations](docs/llm-localizations.md).

## 🧭 Start here

👉 **[Open the documentation hub](docs/README.md)** to choose a path.

| | Open this guide | When to use it |
| --- | --- | --- |
| 🚀 | [Getting started](docs/getting-started.md) | Install the project and launch it for the first time. |
| 🔐 | [Configuration](docs/configuration.md) | Set up the YouTube OAuth client. |
| ▶️ | [Translate workflow](docs/manual-localizations.md) | Generate or provide JSON, edit, validate, preview, and publish. |
| ✨ | [LLM Translation prompt](docs/llm-localizations.md) | Prepare an external-LLM prompt or use local Codex generation. |
| 🆘 | [Troubleshooting](docs/troubleshooting.md) | Fix setup, OAuth, dependency, port, or API problems. |
| 🛡️ | [Security](docs/security.md) | Protect credentials and local token files. |
| 🛠️ | [Development](docs/development.md) | Run tests and work on the repository. |

## ⚡ Quick start

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The Python requirements do not install the optional Codex CLI. Install and
authenticate it separately using the
[LLM localization guide](docs/llm-localizations.md#automatic-local-codex-cli-generation).

Before the first launch, place the YouTube OAuth file at
`config/account_client_secrets_main.json`. See [Getting started](docs/getting-started.md)
and [Configuration](docs/configuration.md) for complete setup.

Streamlit normally opens the local app in your browser. If it does not, open
[http://127.0.0.1:8501](http://127.0.0.1:8501).

### 🪟 Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## ✅ Translate workflow

1. Select one video in the persistent sidebar.
2. In **Source languages**, keep the default source selected and optionally
   select existing localizations as verified references. A video with only its
   default source uses it automatically without a multiselect.
3. In **Generate translations**, click **Generate missing translations** for
   local Codex generation, or open **LLM Translation prompt** for an external
   LLM. You can also paste or edit localization JSON directly.
4. Upload an external-LLM JSON file when returning from the prompt page. All
   generated, uploaded, and manually entered JSON uses the same editor.
5. Click **Preview changes**. Preview never writes to YouTube.
6. Click **Publish changes** only after reviewing a valid current preview.
   Publish refetches the current video, preserves omitted existing
   localizations, and updates one selected video.
7. Confirm the result in YouTube Studio.

The prompt page uses the same source selection as Translate. It offers only
currently missing languages from YouTube's live `i18nLanguages.list` catalog,
allows at most ten targets, and never includes selected source languages as
targets.

The persistent sidebar shows channel details, channel and RSS links, refresh,
page-size controls, pagination, and video cards. Select is below each card's
details and fills the available card width. Click a thumbnail to open the video
on YouTube.

The language catalog is never hardcoded. No OpenAI or other LLM API key is
required; YouTube uses the existing OAuth session.

## 📚 Project documentation

- [Documentation hub](docs/README.md)
- [Development and tests](docs/development.md)
- [Security checklist](docs/security.md)

## 🔒 Credentials

Never commit OAuth JSON, `.env`, `token.json`, or `token.pickle`. See
[Security](docs/security.md) and [Configuration](docs/configuration.md).

## 📜 License

See [LICENSE](LICENSE).
