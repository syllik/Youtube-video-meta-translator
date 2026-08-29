# ▶️ Translate workflow

Use **Translate** for the complete YouTube localization workflow: choose
sources, generate or provide JSON, edit it, validate it, preview the diff, and
publish one selected video's changes safely.

⬅️ [Back to documentation](README.md) · ➡️ [LLM Translation prompt](llm-localizations.md)

## 🎯 Workflow

```text
Select video
      ↓
Choose default primary source and optional existing references
      ↓
Localization JSON Example → Manual edit
      ↓
Choose source languages → Generate translations
      ↓
Validate → Preview changes → Publish changes
```

## 1️⃣ Select a video

The persistent sidebar is available on both **Translate** and **LLM Translation
prompt**. Click **Select** below a video card; the selected card changes to
**Selected**. The app uses the YouTube video ID, not the title, as the API
identifier.

Changing the selected video clears source selection, prompt and target state,
uploaded-file context, and the old editor state, then loads current live
localizations into **Manual edit**. Normal Streamlit reruns preserve a hand-edited
draft. Explicit Refresh, successful Publish, and successful Reset reload it.
Source selection is not saved permanently.

## 2️⃣ Choose source languages

The video's `snippet.defaultLanguage` is always the primary source and uses the
real `snippet.title` and `snippet.description`. If the video has existing
localizations, **Source languages** shows a native multiselect containing the
default plus every existing localization. The default is required and is
restored if removed.

When only the default source exists, the app selects it automatically and does
not show a one-option multiselect. Selected existing localizations provide
their real title and description as optional verified reference translations.
They help preserve intent, tone, and nuance, but the default source remains
authoritative when references conflict with it.

The same source selection is used on **Translate** and **LLM Translation
prompt** while the same video remains selected. Source language codes are
canonicalized using YouTube's live `i18nLanguages.list` catalog.

## 3️⃣ Edit, generate, or provide localization JSON

In **Generate translations**, choose one of these paths:

- **Generate missing translations** runs the locally authenticated Codex CLI
  in sequential batches of at most ten. Every batch receives the same primary
  and selected reference sources.
- Open **LLM Translation prompt** to prepare the same source-aware prompt for
  ChatGPT, Gemini, Claude, or another external LLM. Return to **Translate** and
  upload its direct UTF-8 JSON file.
- **Localization JSON Example** is read-only guidance; it is not the editor.
- Paste or edit JSON directly in **Manual edit**.

All three paths populate the same **Manual edit** draft. Codex results and valid
external-LLM uploads merge into the current draft: new languages are added and
an overlapping code replaces only that entry. No generation or upload publishes
automatically.

The target list contains only currently missing languages from the live
YouTube catalog. The default and every selected source language are excluded
from targets.

## 4️⃣ Edit and validate locally

The editor accepts a non-empty direct JSON object keyed by YouTube language
code:

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

Every value must contain exactly `title` and `description` string fields. A
title cannot be empty and is limited to 100 characters; a description is
limited to 5,000 characters. Invalid JSON or fields keep publishing disabled.
Language keys are matched case-insensitively against the live YouTube catalog,
then emitted using the catalog's exact spelling, including regional and script
codes such as `pt-BR`, `zh-Hans`, and `sr-Latn`.

Existing localizations omitted from submitted JSON are preserved. Removing a
key from the draft therefore does not delete that YouTube localization during
normal Publish. Do not put video, channel, prompt, or wrapper metadata inside
the localization object.

## 5️⃣ Preview and publish safely

Click **Preview changes** to compare valid JSON with the current YouTube state.
Preview never writes to YouTube. The report shows added, changed, unchanged,
and preserved languages.

Click **Publish changes** only after reviewing a valid current preview. If JSON
changes after Preview, publishing is blocked until Preview runs again. Publish
revalidates, fetches the latest YouTube state, merges submitted entries into
existing localizations, preserves omitted entries, and performs at most one
update for the selected video.

An unchanged submission does not create an unnecessary YouTube write.

## 6️⃣ Use the sidebar safely

Video cards show `Localizations: done / undone` using the live YouTube language
catalog, excluding the default language from both values. **Load more** appends
the next cursor-backed batch for numeric page sizes; changing the URL page
starts a new visible batch. It is not shown for **all**.

**Reset languages** is the separate full-deletion operation. It uses the native
browser confirmation and removes every localization for that video while
preserving default title, description, default language, and required snippet
metadata. Save translations you need before selecting **OK**. Cancel does not
make an API request.

## 🚫 Not supported

- subtitles or SRT files;
- audio localization or dubbing;
- bulk editing of multiple videos;
- automatic publishing after generation or upload;
- provider API-key integration.

## ➡️ Next step

- [Prepare an external-LLM prompt or configure local Codex](llm-localizations.md)
- [Handle errors](troubleshooting.md)
- [Read historical product context](manual-localization-editor-context.md)
