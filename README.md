# 🎬 YouTube Video Metadata Translator

A local Streamlit app for managing YouTube video titles and descriptions.

The app has one primary workflow, **Translate**. Select a video, choose its
source and target languages, generate translations with the local Codex CLI or
upload a UTF-8 JSON result from an external LLM, then preview and publish the
validated draft safely. The supporting **LLM Translation prompt** page prepares
a prompt for users who do not use local Codex.

Both pages use the same selected video and source-language state. The default
YouTube language is always the authoritative primary source. Existing
localizations may be selected as optional verified reference translations; the
selection resets when the video changes.

The optional Codex CLI helper can automate missing-language generation outside
Streamlit. It produces a direct localization document for review in Translate,
never publishes by itself, and uses local ChatGPT/Codex authentication without
an API key; see [LLM localizations](docs/llm-localizations.md).

**Language navigation:** **English** · [简体中文](docs/i18n/zh-Hans/README.md) · [繁體中文](docs/i18n/zh-Hant/README.md) · [Español](docs/i18n/es/README.md) · [हिन्दी](docs/i18n/hi/README.md) · [Português (Brasil)](docs/i18n/pt-BR/README.md) · [বাংলা](docs/i18n/bn/README.md) · [Русский](docs/i18n/ru/README.md) · [日本語](docs/i18n/ja/README.md) · [پنجابی](docs/i18n/pa-Arab/README.md) · [Türkçe](docs/i18n/tr/README.md) · [Tiếng Việt](docs/i18n/vi/README.md) · [العربية](docs/i18n/ar/README.md) · [मराठी](docs/i18n/mr/README.md) · [తెలుగు](docs/i18n/te/README.md) · [한국어](docs/i18n/ko/README.md) · [தமிழ்](docs/i18n/ta/README.md) · [اردو](docs/i18n/ur/README.md) · [Bahasa Indonesia](docs/i18n/id/README.md) · [Deutsch](docs/i18n/de/README.md) · [Français](docs/i18n/fr/README.md) · [Basa Jawa](docs/i18n/jv/README.md) · [فارسی](docs/i18n/fa/README.md) · [Italiano](docs/i18n/it/README.md) · [Hausa](docs/i18n/ha/README.md) · [ગુજરાતી](docs/i18n/gu/README.md) · [भोजपुरी](docs/i18n/bho/README.md)

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

```text
Select video
→ Primary source + optional reference translations
→ Target languages
→ Codex or External LLM
→ Preview
→ Publish
→ refreshed current state
```

1. Select one video in the persistent sidebar.
2. In **Source languages**, keep the default source selected and optionally
   select existing localizations as verified references. A video with only its
   default source uses it automatically without a multiselect.
3. In **Target languages**, all currently missing metadata languages are
   selected by default. Remove any languages you do not want to generate; the
   primary Translate selector is not limited to ten languages.
4. In **Generate translations**, choose **Codex** or the visible **External
   LLM** three-step path: **Prepare prompt**, generate JSON externally, then
   upload the downloaded UTF-8 JSON file. Codex processes the complete
   remaining selection in sequential batches of up to ten targets from one
   **Generate missing translations** click. Each successful batch is checkpointed
   into the internal draft; if a later batch fails, retry continues with only
   the remaining targets. **Download JSON** always contains the current draft.
5. Click **Preview changes**. Preview never writes to YouTube.
6. Click **Publish changes** only after reviewing a valid current preview.
   Publish refetches the current video, preserves omitted existing
   localizations, and updates one selected video.
7. Confirm the result in YouTube Studio. A successful Publish clears the cached
   video pages so the sidebar count is refreshed automatically.

The prompt page uses the same source selection as Translate. It offers only
currently missing languages from the checked-in
`data/youtube-metadata-languages.json` metadata catalog, selects the first ten
by default, allows at most ten targets, and never includes selected source
languages as targets. **Download JSON** always contains the current internal
draft as a direct localization map; a later failed Codex batch does not remove
earlier checkpoints. One **Generate missing translations** click processes the
full current remaining queue in sequential batches. While it is active,
**Generate** is disabled and **STOP** can terminate the current Codex job;
completed checkpoints remain in the draft and a later click resumes only the
remaining targets.

After the selected video resource is initially loaded, source and target widget
reruns use its video-scoped session cache and do not issue another selected-video
YouTube read. Use **Refresh video list**, **Preview changes**, **Publish changes**,
or **Reset languages** when a fresh YouTube state is required.

The persistent sidebar shows compact channel details, YouTube/RSS links,
refresh, page-size controls, pagination, and compact video cards. Cards show
metadata-catalog localization counts as `current / total` and full-width
Select/Selected controls. Use **Load more** to append the next cursor-backed
batch; changing the page starts a new visible batch. Click a thumbnail to open
the video on YouTube. Destructive **Reset languages** appears only in the
selected-video **Danger zone**.

**Reset languages** is destructive: after the native browser confirmation, the
app fetches the selected video again, requires a usable fresh ETag, and sends a
conditional `If-Match` update. All non-default localizations are removed while
the default title, description, language, and required metadata remain. A
changed selection, missing ETag, or HTTP 412 is a no-write failure; refresh and
confirm again. Save translations you need before confirming. The control does
not navigate or change URL parameters. The FAQ page is static and opens even
when YouTube OAuth or the API is unavailable.

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

## Support

I spent part of my life building this tool and gave it freely to anyone who
may need it.

Perhaps you found it exactly when you needed it.

[Support my work →](https://github.com/syllik/syllik/blob/master/SUPPORT.md)
