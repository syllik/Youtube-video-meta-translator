# 🎬 YouTube Video Metadata Translator

A local Streamlit app for managing YouTube video titles and descriptions.

The app has one primary workflow, **Translate**. Select a video, choose its
source languages, generate translations with the local Codex CLI or upload a
UTF-8 JSON result from an external LLM, then preview and publish the validated
draft safely. The supporting **LLM Translation prompt** page prepares a prompt
for users who do not use local Codex.

Both pages use the same selected video and source-language state. The default
YouTube language is always the authoritative primary source. Existing
localizations may be selected as optional verified reference translations; the
selection resets when the video changes.

The optional Codex CLI helper can automate missing-language generation outside
Streamlit. It produces a direct localization document for review in Translate,
never publishes by itself, and uses local ChatGPT/Codex authentication without
an API key; see [LLM localizations](docs/llm-localizations.md).

## 🧭 Start here

👉 **[Open the documentation hub](docs/README.md)** to choose a path.

| | Open this guide | When to use it |
| --- | --- | --- |
| 🚀 | [Getting started](docs/getting-started.md) | Install the project and launch it for the first time. |
| 🔐 | [Configuration](docs/configuration.md) | Set up the YouTube OAuth client. |
| ▶️ | [Translate workflow](docs/translate-workflow.md) | Generate or upload translations, preview, and publish. |
| ✨ | [LLM Translation prompt](docs/llm-localizations.md) | Prepare an external-LLM prompt or use local Codex generation. |
| ❓ | [FAQ](pages/3_FAQ.py) | Get short answers about the workflow and safe publishing. |
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
   local Codex generation, or open **LLM Translation prompt** and upload the
   downloaded UTF-8 JSON file. Each valid result becomes the internal
   translation draft; an overlapping language replaces only that entry.
4. Click **Preview changes**. Preview never writes to YouTube.
5. Click **Publish changes** only after reviewing a valid current preview.
   Publish refetches the current video, preserves omitted existing
   localizations, and updates one selected video.
6. Confirm the result in YouTube Studio.

The prompt page uses the same source selection as Translate. It offers only
currently missing languages from the checked-in
`data/youtube-metadata-languages.json` metadata catalog, allows at most ten
targets, and never includes selected source languages as targets.

The persistent sidebar shows compact channel details, YouTube/RSS links,
refresh, page-size controls, pagination, and compact video cards. Cards show
metadata-catalog localization counts as `done / undone`,
full-width Select/Selected, and Reset languages. Use **Load more** to append the
next cursor-backed batch; changing the page starts a new visible batch. Click a
thumbnail to open the video on YouTube.

**Reset languages** is destructive: after the native browser confirmation, all
non-default localizations for that video are removed while its default title,
description, language, and required metadata remain. Save translations you need
before confirming. The control calls the server-side reset operation without
navigating away or changing URL parameters. The FAQ page is static and opens
even when YouTube OAuth or the API is unavailable.

The metadata language catalog is a checked-in snapshot with explicit scope,
provenance, review date, count, and canonical BCP-47 entries. The application
does not call `i18nLanguages.list` to discover video metadata languages. No
OpenAI or other LLM API key is required; YouTube uses the existing OAuth
session for video data and publishing.

## 📚 Project documentation

- [Documentation hub](docs/README.md)
- [Development and tests](docs/development.md)
- [Security checklist](docs/security.md)

## 🔒 Credentials

Never commit OAuth JSON, `.env`, `token.json`, or `token.pickle`. See
[Security](docs/security.md) and [Configuration](docs/configuration.md).

## 📜 License

See [LICENSE](LICENSE).
