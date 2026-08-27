# 🎬 YouTube Video Metadata Translator

A local Streamlit app for managing YouTube video titles and descriptions.

You can choose between two workflows:

- 🧩 **Manual translate** — choose one video, paste prepared localizations,
  validate the JSON, preview the diff, and publish changes while preserving
  omitted languages.
- 🔁 **Machine translate** — translate several videos and languages with DeepL
  and Google Translation fallback.

The two workflows are deliberately separate. Machine translation uses
checkboxes for batch work; manual translation uses a `Select` button on each
video card and an explicit preview-before-publish flow.

## 🧭 Start here

👉 **[Open the documentation hub](docs/README.md)** to choose a path.

| | Open this guide | When to use it |
| --- | --- | --- |
| 🚀 | [Getting started](docs/getting-started.md) | Install the project and launch it for the first time. |
| 🔐 | [Configuration](docs/configuration.md) | Set up Google Cloud, OAuth, DeepL, or Google Translate. |
| 🧩 | [Manual localizations](docs/manual-localizations.md) | Publish prepared JSON safely. |
| 🔁 | [Machine translation](docs/legacy-translation.md) | Translate titles and descriptions automatically. |
| 🆘 | [Troubleshooting](docs/troubleshooting.md) | Fix setup, OAuth, dependency, port, or API problems. |
| 🛡️ | [Security](docs/security.md) | Protect credentials and local token files. |
| 🛠️ | [Development](docs/development.md) | Run tests and work on the repository. |

The emoji markers are navigation hints: `🚀` means start, `🔐` means
credentials, `🧩` means manual editing, `🔁` means machine translation, and
`🆘` means help.

## ⚡ Quick start

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --only-binary=grpcio -r requirements.txt
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
python -m pip install --only-binary=grpcio -r requirements.txt
streamlit run streamlit_app.py
```

## ✅ Before publishing

1. Start with one non-critical video.
2. Open **Manual translate** from the navigation and click **Select** on one video.
3. Paste JSON, validate it, and click **Preview changes**.
4. Check that the report shows the expected `added`, `changed`, and
   `unchanged` entries.
5. Click **Publish changes** only when the JSON is valid.
6. Confirm the result in YouTube Studio.

The video list defaults to the latest 10 uploads. Use `10`, `20`, `50`, or
`all` in the page-size control; the selected page and limit are kept in the
URL for refreshes and sharing.

The manual editor re-fetches current YouTube state before publishing and keeps
existing localizations omitted from the submitted JSON.

## 📚 Project documentation

- [Documentation hub](docs/README.md)
- [Streamlit migration design](docs/superpowers/specs/2026-08-27-streamlit-migration-design.md)
- [Development and tests](docs/development.md)
- [Security checklist](docs/security.md)

## 🔒 Credentials

Never commit OAuth JSON, service-account keys, `.env`, `token.json`, or
`token.pickle`. See [Security](docs/security.md) and [Configuration](docs/configuration.md).

## 📜 License

See [LICENSE](LICENSE).
