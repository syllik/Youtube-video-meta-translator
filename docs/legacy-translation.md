# 🔁 Legacy translation / Старый переводчик

The original DeepL/Google translation workflow remains available. Use this
guide when you want automatic translation instead of prepared JSON.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🧭 Safe first test / Первый безопасный тест

Before translating a whole channel:

1. Open [http://127.0.0.1:5001](http://127.0.0.1:5001).
2. Keep the page size small.
3. Select one video.
4. Select one target language.
5. Enable DeepL only when `.env` contains a valid `DEEPL_API_KEY`.
6. Leave overwrite disabled unless you intentionally want to replace an
   existing localization.
7. Start the translation.
8. Check the result in YouTube Studio.

The app translates video titles and descriptions, not subtitles or audio
tracks. YouTube character limits still apply.

## 🌐 Providers

- **DeepL** is used when enabled and configured.
- **Google Cloud Translation** is used when selected or as the fallback when
  DeepL is unavailable.
- Provider credentials are optional for the manual JSON editor.

See [Configuration](configuration.md) for provider setup.

## ✂️ Long text

If trimming is disabled, text that is too long can be skipped. If trimming is
enabled, the app shortens the title or description before publishing.

## ⚠️ Existing behavior

This is the maintained legacy path for automatic translations. It is separate
from the manual JSON editor, which is the preferred path when the final text
has already been prepared by a person.

➡️ [Use the manual JSON workflow instead](manual-localizations.md)
