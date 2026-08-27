# YouTube Video Metadata Translator

Translate YouTube video titles and descriptions into multiple languages with
DeepL or Google Cloud Translation, then publish the translations directly to
your channel.

This is a local desktop-style web application. It runs on your computer, opens
in your browser, and uses your own Google and translation-service accounts.

## What this project currently does

- signs in to one YouTube channel with Google OAuth;
- lists videos from that channel;
- shows existing localizations;
- translates selected videos into one or more languages;
- uses DeepL when enabled and available;
- falls back to Google Cloud Translation when DeepL is unavailable;
- updates YouTube localization fields without replacing the original video
  title or description;
- can skip or trim text that is longer than YouTube's limits.

The application currently implements the original translation workflow. The
manual JSON localization editor described in
`youtube-manual-localization-editor-context.md` is planning context for a
future workflow, not a separate interface in the current release.

## Before you begin

You need:

- a Google account with access to the YouTube channel you want to edit;
- a Google Cloud project;
- Python 3.12 (recommended and tested for this project);
- a browser on the same computer;
- a DeepL API key, if you want to use DeepL;
- a Google Cloud Translation credential, if you want Google Translate or the
  automatic fallback.

The application changes YouTube metadata on your behalf. Start with one video
and one language until you have checked the result in YouTube Studio.

## Quick start

The commands below must be run from the project folder. Copy only the commands
inside code blocks; do not copy the step numbers or the terminal prompt.

### macOS and Linux

Open Terminal and run:

```bash
cd /Users/your-name/path/to/Youtube-video-meta-translator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --only-binary=grpcio -r requirements.txt
```

If you cloned the repository using the command below, the project folder is
usually named `Youtube-video-meta-translator`:

```bash
git clone https://github.com/syllik/Youtube-video-meta-translator.git
cd Youtube-video-meta-translator
```

After the first setup, every new terminal session only needs:

```bash
cd /path/to/Youtube-video-meta-translator
source .venv/bin/activate
```

### Windows PowerShell

Open PowerShell and run:

```powershell
cd C:\path\to\Youtube-video-meta-translator
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install --only-binary=grpcio -r requirements.txt
```

If PowerShell refuses to activate the environment, run this once in the same
PowerShell window and then repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### What the virtual environment means

`.venv` is a private Python environment for this project. It prevents the
project's packages from interfering with other Python projects on your
computer. The `(.venv)` text at the beginning of the terminal line means it is
active.

Always use `python -m pip`, not a separate global `pip` command. This ensures
that packages are installed into the active `.venv` environment.

## Configure Google Cloud

The project needs an OAuth client file for YouTube. It does not use a simple
Google API key for YouTube because it must read and update private channel
data. Google distinguishes OAuth credentials for private data from API keys
for general project identification and quota tracking. See Google's
[YouTube authorization guide](https://developers.google.com/youtube/registering_an_application).

You may also create a separate Service Account JSON file for Google Cloud
Translation. These are two different credentials and must not be mixed up.

### Part A: Enable the APIs

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. At the top of the page, create a new project or select your existing
   project. For example, name it `youtube-video-translator`.
3. Open the [YouTube Data API v3 page](https://console.cloud.google.com/apis/library/youtube.googleapis.com)
   and click **Enable**.
4. If you want Google Translate, also open the
   [Cloud Translation API page](https://console.cloud.google.com/apis/library/translate.googleapis.com)
   and click **Enable**.
5. If Google asks for a billing account while enabling or using Cloud
   Translation, follow the billing setup shown by Google. Translation usage
   may incur charges or consume free credits; check the quotas and billing
   pages in your project.

### Part B: Configure the OAuth consent screen

The consent screen is the page Google shows before allowing this local app to
access your YouTube account.

1. Open [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding).
2. Select the same Google Cloud project if prompted.
3. Enter an application name, for example `Local YouTube Translator`.
4. Enter your support email and save the form.
5. Open [Google Auth Platform → Audience](https://console.cloud.google.com/auth/audience).
6. If the application is **External**, add the Google account that owns or
   manages the YouTube channel under **Test users**.

The account added as a test user must be the same account you choose in the
browser during the first application launch. A test application is normal for
a private local tool. It does not mean that the application is broken or
published for the whole internet.

If the console uses the older layout, the same settings may appear under
**APIs & Services → OAuth consent screen**.

### Part C: Create the YouTube OAuth client

1. Open [Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients).
2. Select your project if prompted.
3. Click **Create client**.
4. For **Application type**, choose **Desktop app**.
5. Enter a name such as `Local YouTube Translator`.
6. Click **Create**.
7. Click **Download JSON** in the confirmation window.

Do not choose **Web application** and do not create a plain **API key** for
this step. The Python code uses Google's installed-application OAuth flow.
Google's current OAuth documentation also specifies the Desktop app type for
installed applications. ([OAuth guide](https://developers.google.com/youtube/v3/guides/auth/installed-apps))

### Part D: Put the OAuth JSON in the project

Create the configuration folder if it does not exist:

```bash
mkdir -p config
```

Rename the downloaded file exactly to:

```text
account_client_secrets_main.json
```

Move it into the project's `config` folder:

```text
Youtube-video-meta-translator/config/account_client_secrets_main.json
```

The full path on macOS in the example setup is:

```text
/Users/mihaildovgun/Desktop/Youtube-video-meta-translator/config/account_client_secrets_main.json
```

#### Important: avoid `.json.json`

Some file managers hide known file extensions. If the downloaded file already
ends in `.json` and you type `.json` again, the real filename can become:

```text
account_client_secrets_main.json.json
```

The application will not find that file. Check the real filename with:

```bash
find config -maxdepth 1 -type f -print
```

There must be exactly one `.json` at the end of the OAuth filename.

## Optional: enable Google Cloud Translation

DeepL is enough if you always use DeepL and have a working DeepL key. Create
the Google credential as well if you want Google Translate or an automatic
fallback when DeepL reaches its quota.

1. Open [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Select the same Google Cloud project.
3. Click **Create service account**.
4. Give it a name such as `youtube-translator`.
5. If Google asks for a role, choose **Cloud Translation API User**.
6. Finish creating the service account.
7. Click the new service account.
8. Open the **Keys** tab.
9. Click **Add key → Create new key**.
10. Select **JSON** and click **Create**.

Google downloads the private key immediately. It cannot be downloaded again
later, so store it securely. ([Service account key instructions](https://docs.cloud.google.com/iam/docs/keys-create-delete))

Rename the downloaded file exactly to:

```text
translate_key.json
```

Place it here:

```text
Youtube-video-meta-translator/config/translate_key.json
```

This is not the same file as
`account_client_secrets_main.json`.

## Optional: enable DeepL

1. Create an account at [DeepL API](https://www.deepl.com/en/pro-api).
2. Create or copy your DeepL API key.
3. In the project root, create a file named `.env`.
4. Put one line in it:

```text
DEEPL_API_KEY=replace-this-with-your-key
```

Do not add quotes unless the key itself requires them, and do not publish the
file. The application loads `.env` automatically when it starts.

If no DeepL key is present, the DeepL option will not be available as a
working provider. Configure Google Cloud Translation if you want a fallback.

## Files and what they mean

After setup, the important local files are:

| File | Required? | Purpose |
| --- | --- | --- |
| `config/account_client_secrets_main.json` | Yes | Identifies the local app to Google OAuth for YouTube access. |
| `config/translate_key.json` | Only for Google Translate/fallback | Service Account credential for Google Cloud Translation. |
| `.env` | Only for DeepL | Stores `DEEPL_API_KEY`. |
| `token.pickle` | Created automatically | Stores your local YouTube OAuth session after the first authorization. It is in the project root, not in `config`. |
| `.venv/` | Created automatically | Project-specific Python environment. |

The credential files, `.env`, `token.pickle`, and `.venv` are excluded by the
repository's `.gitignore`. Never commit them or send their contents to anyone.

## Start the application

### macOS and Linux

```bash
cd /path/to/Youtube-video-meta-translator
source .venv/bin/activate
python app.py
```

### Windows PowerShell

```powershell
cd C:\path\to\Youtube-video-meta-translator
.\.venv\Scripts\Activate.ps1
python app.py
```

The application uses two local ports for two different purposes:

- `8080` is a temporary callback port used by Google OAuth;
- `5001` is the web application itself.

After the terminal shows that Flask is running, open:

```text
http://127.0.0.1:5001
```

Do not open port `5000`. On some macOS installations another system service
already uses it, which can produce a confusing `403` page that is not coming
from this application.

### First launch

1. Run `python app.py` from the project root.
2. A Google authorization page opens in your browser.
3. Sign in with the account you added as a test user.
4. Review the requested YouTube permissions and approve them.
5. Let Google redirect back to the local OAuth callback on port `8080`.
6. Wait for the terminal to finish its initial YouTube API requests.
7. Open `http://127.0.0.1:5001`.

The terminal may not show a normal prompt while the application is running.
That is expected. Keep that terminal open. Press `Control+C` there when you
want to stop the application.

After successful authorization, `token.pickle` is created automatically. Future
launches normally reuse it and do not ask you to authorize again.

## Verify the installation before launching

These checks are optional but useful when setting up the project for the first
time:

```bash
cd /path/to/Youtube-video-meta-translator
source .venv/bin/activate
python -m pip check
python -c "import flask, grpc, deepl, dotenv, googleapiclient, google_auth_oauthlib; print('Dependencies: OK')"
```

`pip check` should not report broken requirements. If an existing environment
still contains the old `packaging` version, update it with:

```bash
python -m pip install -r requirements.txt
```

Do not install a package named `pkg_resources`. The project pins a compatible
Setuptools version because older Google Translation code imports
`pkg_resources` during startup.

## First safe test

Before translating a whole channel:

1. Open the application at `http://127.0.0.1:5001`.
2. Leave the page size small.
3. Select one video.
4. Select one target language.
5. Enable DeepL only if `.env` contains a valid `DEEPL_API_KEY`.
6. Leave overwrite disabled unless you intentionally want to replace an
   existing localization.
7. Start the translation.
8. Open YouTube Studio and check the video's subtitle/localization language
   settings.

The application works with video titles and descriptions, not subtitles or
audio tracks. YouTube character limits still apply. If trimming is disabled,
text that is too long can be skipped; if trimming is enabled, the application
shortens it before publishing.

## Common problems and what they mean

### `ModuleNotFoundError: No module named 'pkg_resources'`

The environment is using a newer Setuptools with an older Google Translation
library. Make sure the virtual environment is active and run:

```bash
python -m pip install "setuptools<81"
```

Then retry the application. This warning is different from the old fatal
error: `pkg_resources is deprecated` is only a warning as long as startup
continues.

### pip tries to build `grpcio` or fails while building it

The old `grpcio==1.39.0` pin is not suitable for the tested Python 3.12 ARM64
setup. The current requirements use `grpcio>=1.60.0,<2` and the installation
command asks pip to use a binary wheel. Confirm that the active Python belongs
to `.venv`:

```bash
which python
python --version
```

On Windows use:

```powershell
where.exe python
python --version
```

### `FileNotFoundError` for `config/account_client_secrets_main.json`

Check all three things:

1. You are running the command from the project root.
2. The file is inside the project's `config` folder.
3. The filename is not `account_client_secrets_main.json.json`.

Check it with:

```bash
find config -maxdepth 1 -type f -print
```

### Google says the app is in testing or access is restricted

This is expected for a private OAuth application. Add the Google account you
are using to **Google Auth Platform → Audience → Test users**, then authorize
again with that same account.

### The browser shows `403` at `127.0.0.1:5000`

That is the wrong port. Open:

```text
http://127.0.0.1:5001
```

Port `5000` can belong to another macOS service. The application uses `5001`
to avoid that conflict.

### The browser does not open after Google login

Do not manually open the application URL until the terminal has finished the
OAuth callback and started Flask. The Google callback uses port `8080`; the
application uses port `5001`. Keep the terminal running and complete the
authorization page that the application opened.

### `redirect_uri_mismatch`

The OAuth client was probably created as a Web application instead of a Desktop
app. Create a new client with **Application type → Desktop app**, download its
JSON, and replace the file in `config`.

### `Address already in use`

Another program is using port `5001`. Open `app.py` and change the final line:

```python
app.run(debug=True, host='127.0.0.1', port=5001)
```

For example, use `5002`, save the file, restart the app, and open the matching
URL `http://127.0.0.1:5002`.

### Videos do not appear

Check that:

- you authorized the Google account that owns or manages the channel;
- **YouTube Data API v3** is enabled in the selected Cloud project;
- the OAuth flow completed successfully;
- `token.pickle` was created in the project root;
- the terminal is still running and has internet access.

### Google Translate is unavailable

Check that:

- **Cloud Translation API** is enabled;
- `config/translate_key.json` exists and is valid JSON;
- the Service Account belongs to the same project;
- billing or quota requirements have been handled.

DeepL can still work without this file if `.env` contains a valid DeepL key.

### DeepL is not used

Check that `.env` is in the project root, not inside `config`, and contains:

```text
DEEPL_API_KEY=your-real-key
```

Restart `python app.py` after changing `.env`. The application reads the key
when it starts.

### Translations are skipped or trimmed

The title or description is longer than YouTube's allowed length. Start with
trimming enabled if you want the application to shorten the content; leave it
disabled if you prefer to review and shorten the text yourself.

### YouTube quota errors

YouTube Data API requests consume project quota. Reduce the batch size, avoid
repeatedly reloading large channel lists, and check the quota page in Google
Cloud Console. Translation providers have separate quotas and billing rules.

## Security checklist

- Never publish `config/account_client_secrets_main.json`.
- Never publish `config/translate_key.json`.
- Never publish `.env` or its `DEEPL_API_KEY`.
- Never publish `token.pickle`.
- Do not paste credential contents into GitHub issues, chats, or screenshots.
- If a Service Account key is exposed, revoke/delete it in Google Cloud and
  create a new one.
- If an OAuth client is exposed in a public place, delete that client and
  create a replacement.

## Project structure

```text
Youtube-video-meta-translator/
├── app.py                           # Flask application and web routes
├── youtube_account.py               # YouTube OAuth, video loading, publishing
├── google_translate.py              # Google Cloud Translation wrapper
├── requirements.txt                 # Python dependencies
├── templates/
│   ├── home.html                    # Main interface
│   └── quota-error.html             # Quota/error page
├── static/css/                      # Application styles
├── config/                          # Local credentials; never commit
├── .env                             # Optional local DeepL key; never commit
└── token.pickle                     # Local OAuth session; generated automatically
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
