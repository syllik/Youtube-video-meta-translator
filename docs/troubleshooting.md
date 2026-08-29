# 🆘 Troubleshooting

Start with the symptom that matches what you see. Most setup problems come
from an inactive virtual environment, an incorrect OAuth filename, or an
incomplete Google configuration.

⬅️ [Back to documentation](README.md) · ➡️ [Security](security.md)

## 🐍 `ModuleNotFoundError`

Activate `.venv` and install the project requirements:

```bash
python -m pip install -r requirements.txt
```

The project pins a compatible Setuptools version for older Google API
dependencies. A `pkg_resources is deprecated` warning is not fatal.

## 🧰 `Codex CLI was not found`

Automatic Codex generation requires the local Codex CLI. Install it with npm
and verify that the command is available:

```bash
npm install -g @openai/codex
codex --version
```

If installation succeeds but the command is still missing, check the runtime
and npm's global binary location:

```bash
node --version
npm --version
npm prefix -g
which codex
```

The npm global binary directory may not be present in `PATH`. Do not assume a
single macOS global npm path; installation methods can use different locations.

## 🔐 `Codex CLI is not logged in`

Authenticate the local Codex CLI with ChatGPT sign-in, then verify it:

```bash
codex login
codex login status
```

This is separate from the YouTube OAuth file and `token.json`. No OpenAI API
key is required for the local Codex workflow.

The application reports the login guidance only when `codex login status`
explicitly reports `Not logged in`. If it instead shows `Codex login status
failed with exit code ...`, the failure is not necessarily an authentication
failure; use the included safe CLI diagnostic to investigate executable
availability, permissions, or the local runtime environment.

## 🔑 `FileNotFoundError` for the OAuth file

Check that:

1. the command runs from the project root;
2. the file is inside `config/`;
3. the filename is exactly `account_client_secrets_main.json`.

```bash
find config -maxdepth 1 -type f -print
```

See [Configuration](configuration.md) for the complete OAuth setup.

## 🚫 Google says access is restricted

For an External test app, add the Google account you are using to **Google Auth
Platform → Audience → Test users**. Authorize with that same account.

## 🌐 The browser does not show Streamlit

Start the app from the project root:

```text
streamlit run streamlit_app.py
```

The default local address is:

```text
http://127.0.0.1:8501
```

## 🔄 The browser does not open after Google login

Complete the Google authorization page opened by the app and wait for the
terminal to finish the callback on port `8080`. Keep Streamlit running.

## 🔗 `redirect_uri_mismatch`

The OAuth client was probably created as a Web application. Create a new
**Desktop app** client, download its JSON, and replace the file in `config/`.

## 🚪 `Address already in use`

Another program is using port `8501`. Start Streamlit on another port:

```bash
streamlit run streamlit_app.py --server.port 8502
```

Then open `http://127.0.0.1:8502`.

## 🎬 Videos do not appear

Check that:

- the authorized Google account owns or manages the channel;
- YouTube Data API v3 is enabled;
- OAuth completed successfully;
- `token.json` exists in the project root, or an old `token.pickle` is
  available for migration;
- the terminal is still running and has internet access.

## 📎 The LLM upload is rejected

The app does not need an LLM API key. Download the external LLM result as a
UTF-8 `.json` file, then check that it has exactly the requested target codes.
Each value must contain only a string `title` and `description`; wrapper keys,
Markdown fences, prose, duplicate keys, extra codes, and missing codes are
rejected. Correct the file in the external LLM and upload it again.

## 🧾 The form reports unsupported language codes

Only the exact direct YouTube localization map belongs in the form. Remove
wrapper keys such as `catalog`, `languages`, `outputContract`, `schemaVersion`,
or `source`. The valid code list comes from the fresh `i18nLanguages.list`
response shown by the selected workflow.

## 📊 YouTube quota errors

YouTube Data API requests consume project quota. Avoid repeatedly reloading
large channel lists, and start with one selected video.

## ➡️ Still blocked?

Run the checks in [Development](development.md), then review the credential
rules in [Security](security.md).
