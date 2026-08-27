# 🛡️ Security / Безопасность

This is a local tool with permission to modify YouTube metadata. Treat every
credential and token as a secret.

⬅️ [Back to documentation](README.md) · ➡️ [Configuration](configuration.md)

## 🔒 Never publish these files

- `config/account_client_secrets_main.json`
- `config/translate_key.json`
- `.env` and its `DEEPL_API_KEY`
- `token.json`
- `token.pickle`
- the `.venv/` directory

The repository's `.gitignore` excludes these files. Never paste their contents
into GitHub issues, chats, screenshots, or bug reports.

## ✅ Before sharing the project

1. Run `git status --short`.
2. Confirm no credential or token file is tracked.
3. Remove secrets from logs and screenshots.
4. Check that API keys are not present in committed source or documentation.

## 🚨 If a secret was exposed

- Revoke or delete an exposed Service Account key in Google Cloud and create a
  new one.
- Delete an exposed OAuth client and create a replacement.
- Rotate a DeepL API key if it appeared in a public place.
- Remove the secret from local logs and shared screenshots.

Removing a file from the latest working tree is not enough if it was committed
before; rotate the credential first.

## 👤 Least privilege

Use a separate local Google Cloud project when possible. Keep the app private,
authorize only the account that needs access, and start with one non-critical
video before publishing larger changes.

➡️ [Return to the setup guide](getting-started.md)
