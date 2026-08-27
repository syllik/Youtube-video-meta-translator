# 🎬 YouTube Video Metadata Translator

A local Flask app for managing YouTube video titles and descriptions.

You can choose between two workflows:

- 🧩 **Manual JSON editor** — choose one video, paste prepared localizations,
  get automatic validation while editing, and publish changes while preserving
  omitted languages.
- 🔁 **Legacy translator** — keep using the existing DeepL/Google translation
  flow for automatic title and description translations.

The existing legacy workflow remains available. The manual editor does not
require translation-provider credentials.

## 🧭 Start here / Начните здесь

👉 **[Open the documentation hub](docs/README.md)** to choose a path.

| | Open this guide | When to use it |
| --- | --- | --- |
| 🚀 | [Getting started](docs/getting-started.md) | Install the project and launch it for the first time. |
| 🔐 | [Configuration](docs/configuration.md) | Set up Google Cloud, OAuth, DeepL, or Google Translate. |
| 🧩 | [Manual localizations](docs/manual-localizations.md) | Publish prepared JSON safely. |
| 🔁 | [Legacy translation](docs/legacy-translation.md) | Use the existing automatic translator. |
| 🆘 | [Troubleshooting](docs/troubleshooting.md) | Fix setup, OAuth, dependency, port, or API problems. |
| 🛡️ | [Security](docs/security.md) | Protect credentials and local token files. |
| 🛠️ | [Development](docs/development.md) | Run tests and work on the repository. |

The emoji markers are navigation hints: `🚀` means start, `🔐` means
credentials, `🧩` means manual editing, `🔁` means the existing workflow, and
`🆘` means help.

## ⚡ Quick start / Быстрый запуск

From the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --only-binary=grpcio -r requirements.txt
python app.py
```

Then open [http://127.0.0.1:5001](http://127.0.0.1:5001). Before the first
launch, place the YouTube OAuth file at
`config/account_client_secrets_main.json`. The complete setup is in
[Getting started](docs/getting-started.md) and [Configuration](docs/configuration.md).

### 🪟 Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --only-binary=grpcio -r requirements.txt
python app.py
```

## ✅ Before publishing / Перед публикацией

1. Start with one non-critical video.
2. For manual editing, choose the **Manual** radio button for one video.
3. Paste JSON and wait for automatic validation to finish.
4. Check that the report shows the expected `added`, `changed`, and
   `unchanged` entries.
5. Click **Publish changes** only when the JSON is valid.
6. Confirm the result in YouTube Studio.

The manual editor re-fetches current YouTube state before publishing and keeps
existing localizations omitted from the submitted JSON.

## 📚 Project documentation

- [Documentation hub](docs/README.md)
- [Manual editor context](docs/manual-localization-editor-context.md)
- [Development and tests](docs/development.md)
- [Security checklist](docs/security.md)

## 🔒 Credentials

Never commit OAuth JSON, service-account keys, `.env`, `token.json`, or
`token.pickle`. See [Security](docs/security.md) and [Configuration](docs/configuration.md).

## 📜 License

See [LICENSE](LICENSE).
