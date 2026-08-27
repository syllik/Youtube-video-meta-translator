# 📚 Documentation / Документация

This folder contains the project guides. Start with the guide that matches
what you want to do, then follow the numbered steps inside it.

⬅️ [Back to the project README](../README.md)

## 🧭 Choose a path / Выберите раздел

| | Guide | Use it when… |
| --- | --- | --- |
| 🚀 | [Getting started / Быстрый старт](getting-started.md) | You are installing the project or launching it for the first time. |
| 🔐 | [Configuration / Настройка](configuration.md) | You need Google Cloud, OAuth, DeepL, or Google Translate credentials. |
| 🧩 | [Manual localizations / Ручные локализации](manual-localizations.md) | You already have translated JSON and want automatic validation and publishing. |
| 🔁 | [Legacy translation / Старый переводчик](legacy-translation.md) | You want to keep using the existing DeepL/Google translation workflow. |
| 🆘 | [Troubleshooting / Решение проблем](troubleshooting.md) | Setup, OAuth, ports, dependencies, or API calls are failing. |
| 🛡️ | [Security / Безопасность](security.md) | You are handling credentials, tokens, or a leaked secret. |
| 🛠️ | [Development / Разработка](development.md) | You are running tests or changing the project. |
| 📝 | [Manual editor context](manual-localization-editor-context.md) | You need the full product scope and implementation constraints. |

## ✅ Recommended order / Рекомендуемый порядок

```text
🚀 Getting started
        ↓
🔐 Configuration
        ↓
▶️ Start the app
        ↓
🧩 Manual localizations  or  🔁 Legacy translation
        ↓
🆘 Troubleshooting if something goes wrong
```

The emojis are navigation markers, not required language knowledge: find the
icon that matches your task and open the linked guide.

## 📖 Documentation rules / Правила документации

- Keep setup commands copy-pasteable.
- Link to an existing guide instead of duplicating long instructions.
- Keep product context and implementation plans separate from user setup help.
- Update links when a guide is renamed.

➡️ [Start with the installation guide](getting-started.md)
