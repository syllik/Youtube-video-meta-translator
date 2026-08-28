# 🧩 Manual localizations

Use this workflow when translations are already prepared and you want to
review them before publishing to YouTube.

⬅️ [Back to documentation](README.md) · ➡️ [Troubleshooting](troubleshooting.md)

## 🎯 Workflow

```text
Click Select on one video card
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

Click **Select** on one video card in the list. The selected card changes to
**Selected** so the active video is clear. The app uses the YouTube video ID,
not the title, as the API identifier.

The selection stays active while you move through the paginated list. If the
selected video is not on the current page, the app says so explicitly; click
**Select** on a visible card to switch the active video.

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
status. The button is bound to the selected single video. Clicking **Select**
on another video automatically invalidates the previous result and revalidates
the same JSON for the new video. The publish request validates the JSON again
and fetches the latest YouTube video state before building one merged update.

Existing localizations omitted from the submitted JSON are preserved:

```text
current:   de, fr, ja, ru
submitted: de, es
result:    de updated, es added, fr/ja/ru preserved
```

An unchanged submission does not create an unnecessary YouTube write.

## ✅ Input rules

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

For externally prepared AI translations, use the
[LLM prompt workflow](llm-localizations.md), which keeps the provider outside
the application and validates the downloaded JSON locally.

## ➡️ Next step

- [Use the LLM prompt workflow](llm-localizations.md)
- [Handle errors](troubleshooting.md)
- [Read the complete product context](manual-localization-editor-context.md)
