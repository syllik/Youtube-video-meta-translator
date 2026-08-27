# 📚 Documentation

This folder contains the project guides. Start with the guide that matches
what you want to do, then follow the numbered steps inside it.

⬅️ [Back to the project README](../README.md)

## 🧭 Choose a path

| | Guide | Use it when… |
| --- | --- | --- |
| 🚀 | [Getting started](getting-started.md) | You are installing the project or launching it for the first time. |
| 🔐 | [Configuration](configuration.md) | You need Google Cloud, OAuth, DeepL, or Google Translate credentials. |
| 🧩 | [Manual localizations](manual-localizations.md) | You already have translated JSON and want local validation, preview, and publishing. |
| 🔁 | [Machine translation](legacy-translation.md) | You want batch DeepL/Google translation with video checkboxes. |
| 🆘 | [Troubleshooting](troubleshooting.md) | Setup, OAuth, ports, dependencies, or API calls are failing. |
| 🛡️ | [Security](security.md) | You are handling credentials, tokens, or a leaked secret. |
| 🛠️ | [Development](development.md) | You are running tests or changing the project. |
| 📝 | [Manual editor context](manual-localization-editor-context.md) | You need the full product scope and implementation constraints. |

## ✅ Recommended order

```text
🚀 Getting started
        ↓
🔐 Configuration
        ↓
▶️ Start the app
        ↓
🔁 Machine translation  or  🧩 Manual localizations
        ↓
🆘 Troubleshooting if something goes wrong
```

The emojis are navigation markers, not required language knowledge: find the
icon that matches your task and open the linked guide.

## 📖 Documentation rules

- Keep setup commands copy-pasteable.
- Link to an existing guide instead of duplicating long instructions.
- Keep product context and implementation plans separate from user setup help.
- Update links when a guide is renamed.
- Write baseline documentation in English only until a localization policy is
  introduced.
- Update the relevant documentation in the same change as code, UI, UX, or
  workflow changes.

➡️ [Start with the installation guide](getting-started.md)
