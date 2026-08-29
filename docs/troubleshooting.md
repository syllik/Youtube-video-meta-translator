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

Automatic Codex generation requires the local Codex CLI. Install or update it
and verify that the command is available. Follow the
[official Codex CLI installation instructions](https://developers.openai.com/codex/cli/)
for the current installation method:

```bash
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

## 🧰 `Codex login status failed with exit code 1`

This message does not automatically mean that Codex is not logged in. It means
that the status command failed. Check the CLI and the environment before
authenticating again.

### 1. Check Codex in the current terminal

On macOS or Linux, run:

```bash
which -a codex
codex --version
node --version
uname -m
node -p "process.platform + ' ' + process.arch"
codex login status
```

`codex --version` must complete successfully. Compare the Node.js architecture
with the architecture you expect to use on the machine. Run `codex login
status` as a separate CLI check, not only through Streamlit.

### 2. Check the same Codex through the app's Python environment

Activate the app's `.venv`, then run:

```bash
python - <<'PY'
import shutil
import subprocess

print("Codex path:", shutil.which("codex"))

result = subprocess.run(
    ["codex", "--version"],
    text=True,
    capture_output=True,
)

print("Exit:", result.returncode)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
PY
```

If both the terminal and the Python `.venv` find and run the same Codex, but
the UI still shows an older Node.js/Codex error, Streamlit is probably using a
stale inherited environment.

### 3. Fully restart Streamlit

Stop the running app and start it from the same terminal session where the
Codex checks succeed:

```bash
Ctrl+C
source .venv/bin/activate
python -m streamlit run streamlit_app.py
```

Child processes inherit the environment of the Streamlit process. Updating
Node.js or Codex in another terminal does not change the `PATH` or runtime
environment of an already-running Streamlit process.

### 4. Reinstall only if `codex --version` itself fails

If `codex --version` reports `Missing optional dependency
@openai/codex-...`, or another launcher/runtime error, the Codex CLI
installation is broken. Reinstall or update it using the
[current official Codex CLI installation instructions](https://developers.openai.com/codex/cli/),
then repeat Step 1. Do not treat a launcher/runtime error as an authentication
problem.

## 🔐 `Codex CLI is not logged in`

Authenticate the local Codex CLI with ChatGPT sign-in, then verify it:

```bash
codex login
codex login status
```

This is separate from the YouTube OAuth file and `token.json`. No OpenAI API
key is required for the local Codex workflow.

The application reports the login guidance only when `codex login status`
explicitly reports `Not logged in`. Interpret the other outcomes as follows:

- `Not logged in` → run `codex login` and then `codex login status` again.
- `Missing optional dependency`, a Node.js stack trace, or another
  launcher/runtime error → this is an installation or environment problem,
  not an authentication problem; follow the diagnostic section above.
- If the CLI works in the terminal but fails only in the UI → restart
  Streamlit from that same working terminal environment.

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

The **FAQ** page is static and does not use this bootstrap path, so it remains
available for guidance even when OAuth or YouTube API loading fails.

## 📎 The LLM upload is rejected

The app does not need an LLM API key. Download the external LLM result as a
UTF-8 `.json` file, then check that it has exactly the requested target codes.
Each value must contain only a string `title` and `description`; wrapper keys,
Markdown fences, prose, duplicate keys, extra codes, and missing codes are
rejected. Correct the file in the external LLM and upload it again.

## 🧾 An upload reports unsupported language codes

Only the exact direct YouTube localization map belongs in an upload. Remove
wrapper keys such as `catalog`, `languages`, `outputContract`, `schemaVersion`,
or `source`. The valid code list comes from the fresh `i18nLanguages.list`
response shown by the selected workflow.

## 📊 YouTube quota errors

YouTube Data API requests consume project quota. Avoid repeatedly reloading
large channel lists, and start with one selected video.

## 🧨 Reset languages was selected

Reset is intentionally destructive. It removes all non-default localizations
after the native browser confirmation and preserves the current default
metadata. The app verifies the fresh YouTube resource after the update; a
verification failure is reported as an error rather than success. If you
clicked **Cancel**, no YouTube request is made and the current page URL is
unchanged. A confirmed reset calls the API without navigating away. If the
reset failed, review the error, refresh the list, and verify the video in
YouTube Studio before trying again.

## ➡️ Still blocked?

Run the checks in [Development](development.md), then review the credential
rules in [Security](security.md).
