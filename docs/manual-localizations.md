# 🧩 Manual localizations / Ручные локализации

Use this workflow when translations are already prepared and you want to
review them before publishing to YouTube.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🎯 Workflow / Сценарий

```text
Select one video
      ↓
Paste localization JSON
      ↓
Automatic validation on every change
      ↓
Review added / changed / unchanged entries
      ↓
Publish changes
```

The manual editor handles exactly one uploaded video per operation. It does not
generate translations, process subtitles, or publish audio localization.

## 1️⃣ Select a video

Choose one video in the **Manual** selector. The app uses the YouTube video ID,
not the title, as the API identifier.

## 2️⃣ Paste JSON

Use a non-empty JSON object keyed by YouTube language code:

```json
{
  "de": {
    "title": "German title",
    "description": "German description"
  },
  "fr": {
    "title": "French title",
    "description": "French description"
  }
}
```

Regional codes such as `pt-BR` and `zh-CN` remain regional codes. Do not put
`video_id`, channel data, or unrelated metadata inside this JSON.

## 3️⃣ Edit and validate locally

After every JSON change, the form validates the current text locally. Click
**Preview changes** to compare the valid document with the selected video's
current YouTube state. The report shows:

- `added` — the language does not exist yet;
- `changed` — title or description differs;
- `unchanged` — both fields are identical;
- invalid entries — the language or field needs correction.

Invalid JSON or an invalid entry keeps **Publish changes** disabled. The
validation request performs no `videos.update` request.

## 4️⃣ Publish changes

Click **Publish changes** only after checking the report and seeing the valid
status. The button is bound to the selected single video. Switching the Manual
radio to another video automatically invalidates the previous result and
revalidates the same JSON for the new video. The publish request validates the
JSON again and fetches the latest YouTube video state before building one
merged update.

Existing localizations omitted from the submitted JSON are preserved:

```text
current:   de, fr, ja, ru
submitted: de, es
result:    de updated, es added, fr/ja/ru preserved
```

An unchanged submission does not create an unnecessary YouTube write.

## ✅ Input rules / Правила ввода

- The root must be a non-empty JSON object.
- Every language key must be supported by the app.
- Every value must contain exactly `title` and `description` string fields.
- A title cannot be empty after trimming whitespace.
- A title may contain at most 100 characters.
- A description may contain at most 5,000 characters.
- Content is not silently truncated.

The editor reports the language and field path, for example `ja.title`.

## 🚫 Not supported in this workflow

- subtitles or SRT files;
- audio localization or dubbing;
- bulk manual editing of multiple videos;
- automatic AI, DeepL, or Google translation generation.

The machine translator remains available as a separate workflow. See
[Machine translation](legacy-translation.md).

## ➡️ Next step

- [Run the machine translation workflow](legacy-translation.md)
- [Handle errors](troubleshooting.md)
- [Read the complete product context](manual-localization-editor-context.md)
