# 🚀 Getting started / Быстрый старт

Use this guide to install the local app, start it, and complete the first
Google authorization.

⬅️ [Back to documentation](README.md) · ➡️ [Configure credentials](configuration.md)

## ✅ What you need / Что понадобится

- A Google account with access to the YouTube channel.
- Python 3.12 (recommended and tested for this project).
- A browser on the same computer.
- An OAuth client JSON file for YouTube; see [Configuration](configuration.md).
- Optional: a DeepL API key or Google Cloud Translation credentials.

The application changes YouTube metadata on your behalf. Start with one video
and one language until you have checked the result in YouTube Studio.

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
python -m pip install --only-binary=grpcio -r requirements.txt
```

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
python -m pip install --only-binary=grpcio -r requirements.txt
```

If PowerShell refuses to activate the environment, run this once in the same
PowerShell window and repeat the activation command:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 3️⃣ Configure Google / Настройте Google

Follow [Configuration](configuration.md) and place the OAuth file at:

```text
config/account_client_secrets_main.json
```

Do not use a plain API key for YouTube. This app needs OAuth permission to read
and update channel data.

## 4️⃣ Check the environment / Проверьте окружение

With `.venv` active:

```bash
python -m pip check
python -c "import streamlit, grpc, deepl, dotenv, googleapiclient, google_auth_oauthlib; print('Dependencies: OK')"
```

`pip check` should not report broken requirements. Do not install a package
named `pkg_resources`; the project pins a compatible Setuptools version for
older Google Translation code.

## 5️⃣ Start the application / Запустите приложение

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

The application uses two local ports:

- `8080` — temporary Google OAuth callback;
- `8501` — the Streamlit web application.

Open [http://127.0.0.1:8501](http://127.0.0.1:8501) after Streamlit starts.

## 6️⃣ First authorization / Первая авторизация

1. Run `streamlit run streamlit_app.py` from the project root.
2. Sign in with the Google account added as an OAuth test user.
3. Review and approve the requested YouTube permissions.
4. Let Google redirect to the local callback on port `8080`.
5. Wait for the terminal to finish its initial YouTube requests.
6. Open `http://127.0.0.1:8501`.

Keep the terminal open while the app is running. Press `Control+C` there to
stop it. After authorization, `token.json` is created in the project root and
future launches normally reuse it. An older `token.pickle` is accepted once
and migrated to the safer JSON format.

## ➡️ Next step

- [Configure Google Cloud and optional providers](configuration.md)
- [Use the manual JSON editor](manual-localizations.md)
- [Use the machine translation workflow](legacy-translation.md)
