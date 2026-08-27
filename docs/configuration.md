# 🔐 Configuration / Настройка

This guide explains Google Cloud, YouTube OAuth, Google Cloud Translation,
DeepL, and the local files they use.

⬅️ [Back to documentation](README.md) · ⬅️ [Getting started](getting-started.md)

## 1️⃣ Create a Google Cloud project

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project or select an existing one, for example
   `youtube-video-translator`.
3. Enable [YouTube Data API v3](https://console.cloud.google.com/apis/library/youtube.googleapis.com).
4. If you want the legacy Google Translate fallback, enable
   [Cloud Translation API](https://console.cloud.google.com/apis/library/translate.googleapis.com).

Translation usage may require billing or consume free credits. Check the
quotas and billing pages in your Google Cloud project.

## 2️⃣ Configure the OAuth consent screen

The consent screen controls which Google account may authorize this local app.

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
step. The app uses Google's installed-application OAuth flow. See Google's
[installed-app OAuth guide](https://developers.google.com/youtube/v3/guides/auth/installed-apps).

## 4️⃣ Place the OAuth file

Create the folder if needed:

```bash
mkdir -p config
```

Rename the downloaded file exactly to:

```text
account_client_secrets_main.json
```

Place it here:

```text
Youtube-video-meta-translator/config/account_client_secrets_main.json
```

Watch for an accidental double extension:

```text
account_client_secrets_main.json.json
```

Check the real filename with:

```bash
find config -maxdepth 1 -type f -print
```

## 🌐 Optional: Google Cloud Translation

Use this only if you want the existing Google Translate workflow or its
fallback when DeepL is unavailable.

1. Open [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Select the same project and create a service account.
3. If a role is requested, choose **Cloud Translation API User**.
4. Open the account's **Keys** tab.
5. Choose **Add key → Create new key → JSON**.
6. Store the downloaded private key securely; it cannot be downloaded again.
7. Rename it to `translate_key.json` and place it in `config/`.

This is a different credential from `account_client_secrets_main.json`. See
Google's [service-account key instructions](https://docs.cloud.google.com/iam/docs/keys-create-delete).

## 🟦 Optional: DeepL

1. Create an account at [DeepL API](https://www.deepl.com/en/pro-api).
2. Copy your API key.
3. Create `.env` in the project root.
4. Add:

```text
DEEPL_API_KEY=replace-this-with-your-key
```

The application loads `.env` at startup. Keep the file local and restart the
app after changing it.

## 📁 Local files / Локальные файлы

| File | Required? | Purpose |
| --- | --- | --- |
| `config/account_client_secrets_main.json` | Yes | YouTube OAuth client configuration. |
| `config/translate_key.json` | Only for Google Translate/fallback | Google Cloud Translation service-account key. |
| `.env` | Only for DeepL | Stores `DEEPL_API_KEY`. |
| `token.json` | Created automatically | Local YouTube OAuth session. |
| `token.pickle` | Legacy only | Accepted once and migrated to `token.json`. |
| `.venv/` | Created automatically | Project-specific Python environment. |

All credentials, token files, `.env`, and `.venv` are excluded by
`.gitignore`. Read the [Security guide](security.md) before sharing the
project or opening an issue.

## ➡️ Next step

- [Start the app](getting-started.md)
- [Publish prepared JSON localizations](manual-localizations.md)
- [Troubleshoot OAuth and credentials](troubleshooting.md)
