# 🔐 Configuration

This guide explains the YouTube OAuth setup used by both workflows.

⬅️ [Back to documentation](README.md) · ⬅️ [Getting started](getting-started.md)

## 1️⃣ Create a Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project or select an existing one, for example
   `youtube-video-translator`.
3. Enable [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com).

The app uses one authenticated YouTube OAuth session for listing videos,
fetching the live `i18nLanguages.list` catalog, reading localizations, and
publishing updates. It does not need a separate YouTube API key for the
integrated app flow.

## 2️⃣ Configure the OAuth consent screen

1. Open [Google Auth Platform → Branding](https://console.cloud.google.com/auth/branding).
2. Select the same project if prompted.
3. Enter an application name such as `Local YouTube Translator` and a support
   email.
4. Open [Google Auth Platform → Audience](https://console.cloud.google.com/auth/audience).
5. If the app is **External**, add the Google account that owns or manages the
   channel under **Test users**.

Use that same account in the browser during the first launch. A test
application is normal for a private local tool.

## 3️⃣ Create the YouTube OAuth client

1. Open [Google Auth Platform → Clients](https://console.cloud.google.com/auth/clients).
2. Select the project.
3. Click **Create client**.
4. Choose **Desktop app** as the application type.
5. Download the JSON file.

Do not choose **Web application** and do not create a plain API key for this
step. The app uses Google's installed-application OAuth flow for video access,
the live catalog, and publishing. See Google's
[installed-app OAuth guide](https://developers.google.com/youtube/v3/guides/auth/installed-apps).

## 4️⃣ Place the OAuth file

Create the folder if needed and place the downloaded file here:

```text
Youtube-video-meta-translator/config/account_client_secrets_main.json
```

The filename must be exactly `account_client_secrets_main.json`, not
`account_client_secrets_main.json.json`.

```bash
mkdir -p config
find config -maxdepth 1 -type f -print
```

## 5️⃣ Use an external LLM without an API key

No OpenAI or other LLM API key, `.env` file, or provider configuration is
required. The supporting **LLM Translation prompt** page creates a copyable
prompt from the selected video's default metadata and live YouTube language
catalog. Paste it into an external LLM, download its JSON file, and upload the
file to **LLM translate** for local validation, Preview, and Publish.

## 📁 Local files

| File | Required? | Purpose |
| --- | --- | --- |
| `config/account_client_secrets_main.json` | Yes | YouTube OAuth client configuration. |
| `token.json` | Created automatically | Local YouTube OAuth session. |
| `token.pickle` | Legacy only | Accepted once and migrated to `token.json`. |
| `.venv/` | Created automatically | Project-specific Python environment. |

The language catalog is fetched at runtime from YouTube Data API v3
`i18nLanguages.list`. There is no checked-in language list and no
`YOUTUBE_API_KEY` setting in this application flow.

The optional `youtube_languages/` export utility is separate from the
Streamlit app and is not needed for translation or publishing.

All credentials, token files, `.env`, and `.venv` are excluded by
`.gitignore`. Read the [Security guide](security.md) before sharing the
project or opening an issue.

## ➡️ Next step

- [Start the app](getting-started.md)
- [Use the Manual workflow](manual-localizations.md)
- [Use the LLM workflow](llm-localizations.md)
- [Troubleshoot OAuth and JSON uploads](troubleshooting.md)
