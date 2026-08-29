# 🛡️ Security

This is a local tool with permission to modify YouTube metadata. Treat every
credential and token as a secret.

⬅️ [Back to documentation](README.md) · ➡️ [Configuration](configuration.md)

## 🔒 Never publish these files

- `config/account_client_secrets_main.json`;
- `token.json`;
- `token.pickle`;
- the `.venv/` directory.

The repository's `.gitignore` excludes these files. Never paste their contents
into GitHub issues, chats, screenshots, or bug reports.

## ✅ Before sharing the project

1. Run `git status --short`.
2. Confirm no credential or token file is tracked.
3. Remove secrets from logs and screenshots.
4. Check that OAuth credentials and tokens are not present in committed source
   or documentation.

## 🚨 If a secret was exposed

- Delete an exposed OAuth client and create a replacement.
- Remove the secret from local logs and shared screenshots.

Removing a file from the latest working tree is not enough if it was committed
before; rotate the credential first.

## 👤 Least privilege

Use a separate local Google Cloud project when possible. Keep the app private,
authorize only the account that needs access, and start with one non-critical
video before publishing larger changes.

The application does not connect to an LLM provider or store an LLM API key.
Uploaded localization JSON remains in the local Streamlit session until the
translation draft is published or the selected video changes.

➡️ [Return to the setup guide](getting-started.md)
