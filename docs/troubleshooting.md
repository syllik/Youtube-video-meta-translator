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

## 🔑 OAuth client file is missing

The app expects this exact path:

```text
config/account_client_secrets_main.json
```

Download a Google OAuth client JSON for a **Desktop app**, save it at this exact
path, then restart the app. Check that:

1. the command runs from the project root;
2. the file is inside `config/`;
3. the filename is exactly `account_client_secrets_main.json`.

```bash
find config -maxdepth 1 -type f -print
```

See [Configuration](configuration.md) for the complete OAuth setup.

## 🔧 OAuth client JSON is malformed or the wrong type

The file was found, but Google cannot use it. Create a Google OAuth client of
type **Desktop app**, download a replacement, and save it as
`config/account_client_secrets_main.json`. Do not use a Web application client
for this local flow. The app does not display the credential contents.

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
terminal to finish the callback on `localhost:8080`. Keep Streamlit running.

## 🚪 OAuth callback on `localhost:8080` failed

Close the process using port `8080` or restart the app and complete Google
authorization again. Do not delete the token automatically; if authorization
is no longer valid, follow the recovery below.

## 🔐 Authorization expired or was revoked

The app refreshes authorization when possible. If YouTube reports that
authorization is no longer valid, restart authorization; if necessary remove
the local `token.json` and restart Streamlit. Never share the token contents.

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

## 🎯 No target languages are available or selected

**Translate** shows only missing languages from the checked-in
`data/youtube-metadata-languages.json` catalog. The default source, selected
source references, and existing YouTube localizations are excluded. A new
video selects all remaining targets by default; if you clear the selection,
choose at least one target before clicking **Generate missing translations**.
The primary Translate selector can contain more than ten languages. The
supporting **LLM Translation prompt** page intentionally remains limited to
ten.

## ⏸️ Codex generation stopped after a batch

Codex generation on **Translate** processes all remaining selected targets from
one click in sequential batches of up to ten. Each validated batch is merged
into the internal draft immediately. If a later batch fails, that failed batch
is not merged but earlier checkpoints remain in the draft and Download after
the page rerenders. Retry skips valid selected target entries already present
in the draft. During an active job, **STOP** terminates the current Codex
process; it does not wait for the normal batch timeout. The current incomplete
batch is not merged, while earlier checkpoints remain. After the job reaches
**stopped** or **failed**, click **Generate missing translations** again to
process only the remaining selected targets. The download contains the direct
localization map from the current committed draft and is disabled only while
that draft is empty.

Changing source or target widgets after the initial selected-video load does not
fetch that video again; those reruns use the video-scoped session cache. Use
**Refresh video list**, **Preview changes**, **Publish changes**, or **Reset
languages** when a fresh YouTube read is required.

## ⚠️ Preview asks you to Preview again

Any new draft entry, including a Codex checkpoint or valid external upload,
invalidates the old Preview. Preview the complete current draft again before
publishing. Publish compares the video ID, writable snippet fields, and
localizations; an ETag-only or read-only response-field change does not cause a
false conflict. A real publish-relevant change blocks the write. The final
fresh fetch still uses `If-Match`, so HTTP 412 is also a no-write conflict.

## 🧾 An upload reports an unknown or malformed language code

Only the exact direct YouTube localization map belongs in an upload. Remove
wrapper keys such as `catalog`, `languages`, `outputContract`, `schemaVersion`,
or `source`. The valid code list comes from the checked-in
`data/youtube-metadata-languages.json` metadata snapshot. A message about an
invalid BCP-47 code means the key has malformed syntax such as `en_US` or
`en--GB`; an unknown metadata localization language is syntactically plausible
but absent from the snapshot.

## 📊 YouTube quota is exhausted

YouTube API quota is exhausted. Wait for the quota reset before trying again.
Do not use an automatic retry loop. Avoid repeatedly reloading large channel
lists, and start with one selected video after the reset.

## 🎬 The selected video was not found

The selected video may have been deleted or become unavailable. Refresh the list
and select it again. Preview and Publish use the same recovery message and do
not write when the exact selected video cannot be fetched.

## 🌐 YouTube/Google cannot be reached

Could not reach YouTube/Google. Check the connection and retry. The app shows a
safe summary instead of a stack trace or raw API diagnostics.

## 🧨 Reset languages conflict or failure

Reset is intentionally destructive and exists only in the selected-video
**Danger zone**. It fetches a fresh resource and requires a usable ETag before
using conditional `If-Match`. A changed selection, missing ETag, or HTTP 412 is
a no-write conflict with no automatic retry; refresh the list and confirm
again. The app verifies the fresh YouTube resource after an accepted update; a
verification failure is reported as an error rather than success. If you
clicked **Cancel**, no YouTube request is made and the current page URL is
unchanged. A confirmed reset calls the API without navigating away.

## ➡️ Still blocked?

Run the checks in [Development](development.md), then review the credential
rules in [Security](security.md).
