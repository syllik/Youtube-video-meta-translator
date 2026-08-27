# 🔁 Machine translation

Use this guide when you want automatic title and description translation
instead of prepared JSON.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🧭 Safe first test

Before translating a whole channel:

1. Run `streamlit run streamlit_app.py` and open the **Machine translate** page.
2. Keep the page size at 10 or 20 for the first test.
3. Select one video with its checkbox.
4. Select one target language.
5. Enable DeepL only when `.env` contains a valid `DEEPL_API_KEY`.
6. Leave overwrite disabled unless you intentionally want to replace an
   existing localization.
7. Click **Translate selected videos**.
8. Check the result in YouTube Studio.

For batch selection, **Select all visible** and **Clear all visible** affect
only the current page. **Select all channel videos** is available with the
`all` page size. Once a row is changed or the visible selection is cleared,
the channel-wide selection mode turns off so it cannot reapply the old state.

The video list defaults to the latest 10 uploads. Use `10`, `20`, `50`, or
`all`; the current page and limit are kept in the URL.

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

This is the machine translation page. It is separate from the manual JSON
editor, which is the preferred path when the final text has already been
prepared by a person.

➡️ [Use the manual JSON workflow instead](manual-localizations.md)
