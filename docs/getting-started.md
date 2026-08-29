# 🚀 Getting started

Use this guide to install the local app, start it, and complete the first
Google authorization.

⬅️ [Back to documentation](README.md) · ➡️ [Configure credentials](configuration.md)

## ✅ What you need

- A Google account with access to the YouTube channel.
- Python 3.12 (recommended and tested for this project).
- A browser on the same computer.
- A YouTube OAuth client JSON file; see [Configuration](configuration.md).
- Node.js and npm if you want automatic Codex CLI generation.
- No OpenAI or other LLM API key is required for **Translate** or the
  supporting **LLM Translation prompt** page.
- **FAQ** is static and does not require YouTube OAuth or API access.

The application changes YouTube metadata on your behalf. Start with one video
and check the result in YouTube Studio before larger work.

## 1️⃣ Install on macOS or Linux

If you still need to clone the repository:

```bash
git clone https://github.com/syllik/Youtube-video-meta-translator.git
cd Youtube-video-meta-translator
```

Then run these commands from the project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

These Python requirements do not install the optional Codex CLI. To use
automatic generation, follow [Automatic local Codex CLI generation](llm-localizations.md#automatic-local-codex-cli-generation)
after the Python setup; that path requires Node.js/npm and a locally
authenticated Codex session.

For a later terminal session, activate the existing environment:

```bash
cd /path/to/Youtube-video-meta-translator
source .venv/bin/activate
```

## 2️⃣ Install on Windows PowerShell

```powershell
cd C:\path\to\Youtube-video-meta-translator
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell refuses to activate the environment, run this once in the same
PowerShell window and repeat activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3️⃣ Configure Google

Follow [Configuration](configuration.md) and place the OAuth file at:

```text
config/account_client_secrets_main.json
```

The **Translate** workflow and supporting prompt page use the same YouTube
OAuth session and current selected video. Their source selection is shared:
the default language is the primary source and selected existing localizations
are optional verified references. Changing video resets that selection and any
draft workflow state. On **Translate**, **Target languages** defaults to every
currently missing metadata language and can be narrowed to a subset. The
external-LLM path creates a source-aware prompt and validates the downloaded
JSON file when you upload it; the automatic Codex path additionally uses the
local Codex login and checkpoints successful batches into the draft. Neither
path requires a provider API key.

## 4️⃣ Check the environment

With `.venv` active:

```bash
python -m pip check
python -c "import streamlit, googleapiclient, google_auth_oauthlib; print('Dependencies: OK')"
```

`pip check` should not report broken requirements. A `pkg_resources is
deprecated` warning from an older Google dependency is not a fatal error.

## 5️⃣ Start the application

### macOS or Linux

```bash
cd /path/to/Youtube-video-meta-translator
source .venv/bin/activate
streamlit run streamlit_app.py
```

### Windows PowerShell

```powershell
cd C:\path\to\Youtube-video-meta-translator
.\.venv\Scripts\Activate.ps1
streamlit run streamlit_app.py
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501) after Streamlit starts.

## 6️⃣ First authorization

1. Run `streamlit run streamlit_app.py` from the project root.
2. Sign in with the Google account added as an OAuth test user.
3. Review and approve the requested YouTube permissions.
4. Let Google redirect to the local callback on port `8080`.
5. Wait for the terminal to finish its initial YouTube requests.
6. Open the local Streamlit page.

Keep the terminal open while the app is running. Press `Control+C` there to
stop it. After authorization, `token.json` is created in the project root and
future launches normally reuse it. An older `token.pickle` is accepted once
and migrated to the safer JSON format.

If first authorization fails, follow the action shown in the app: restore the
Desktop OAuth file at `config/account_client_secrets_main.json`, replace a
malformed client JSON, allow the local callback on `127.0.0.1:8080`, or restart
authorization if the account's consent has expired or been revoked. Delete
`token.json` only for a deliberate re-authorization, and never share its
contents.

## ➡️ Next step

- [Use Translate](translate-workflow.md)
- [Use LLM Translation prompt](llm-localizations.md)
- [Read the FAQ](../pages/3_FAQ.py)
- [Troubleshoot setup](troubleshooting.md)
