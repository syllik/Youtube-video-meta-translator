# 🆘 Troubleshooting / Решение проблем

Start with the symptom that matches what you see. Most setup problems come
from an inactive virtual environment, an incorrect credential filename, or the
wrong local port.

⬅️ [Back to documentation](README.md) · ➡️ [Security](security.md)

## 🐍 `ModuleNotFoundError: No module named 'pkg_resources'`

Activate `.venv` and install the compatible Setuptools version:

```bash
python -m pip install "setuptools<81"
```

`pkg_resources is deprecated` is a warning from an older dependency. It is not
the same as the fatal missing-module error when startup stops.

## 📦 pip tries to build `grpcio`

The project uses a modern `grpcio` range for the tested Python 3.12 ARM64
setup. Make sure `.venv` is active and use the documented binary-wheel
installation command:

```bash
python -m pip install --only-binary=grpcio -r requirements.txt
which python
python --version
```

On Windows, use `where.exe python` instead of `which python`.

## 🔑 `FileNotFoundError` for `config/account_client_secrets_main.json`

Check that:

1. The command is running from the project root.
2. The file is inside `config/`.
3. The filename is not `account_client_secrets_main.json.json`.

```bash
find config -maxdepth 1 -type f -print
```

See [Configuration](configuration.md) for the complete OAuth setup.

## 🚫 Google says access is restricted

For an External test app, add the Google account you are using to **Google
Auth Platform → Audience → Test users**. Authorize with that same account.

## 🌐 The browser shows `403` at `127.0.0.1:5000`

That is the wrong port. Open:

```text
http://127.0.0.1:5001
```

Port `5000` may belong to another macOS service; this app uses `5001`.

## 🔄 The browser does not open after Google login

Complete the Google authorization page opened by the app and wait for the
terminal to finish the callback on port `8080`. Keep the terminal running and
open port `5001` only after Flask has started.

## 🔗 `redirect_uri_mismatch`

The OAuth client was probably created as a Web application. Create a new
**Desktop app** client, download its JSON, and replace the file in `config/`.

## 🚪 `Address already in use`

Another program is using port `5001`. Change the final line of `app.py`:

```python
app.run(debug=False, host='127.0.0.1', port=5001)
```

For example, use `5002`, restart the app, and open
`http://127.0.0.1:5002`.

## 🎬 Videos do not appear

Check that:

- the authorized Google account owns or manages the channel;
- YouTube Data API v3 is enabled;
- OAuth completed successfully;
- `token.json` exists in the project root, or an old `token.pickle` is
  available for migration;
- the terminal is still running and has internet access.

## 🌍 Google Translate is unavailable

Check that Cloud Translation API is enabled, `config/translate_key.json` is
valid, the service account belongs to the same project, and billing/quota
requirements are satisfied.

## 🟦 DeepL is not used

Check that `.env` is in the project root, not in `config/`, and contains:

```text
DEEPL_API_KEY=your-real-key
```

Restart `python app.py` after changing `.env`.

## ✂️ Translations are skipped or trimmed

The title or description is longer than YouTube's limit. Enable trimming if
you want the app to shorten it, or leave trimming disabled and shorten the
content yourself.

## 📊 YouTube quota errors

YouTube Data API requests consume project quota. Reduce batch size, avoid
repeatedly loading large channel lists, and check the quota page in Google
Cloud Console. Translation providers have separate quotas.

## ➡️ Still blocked?

Run the checks in [Development](development.md), then review the credential
rules in [Security](security.md).
