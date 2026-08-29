# YouTube language catalog

This folder contains a small helper tool that fetches the current list of
languages exposed by YouTube. The list is not hard-coded: every run calls the
official YouTube Data API v3 `i18nLanguages.list` endpoint.

The tool supports the translation workflow:

1. fetch fresh YouTube BCP-47 language codes;
2. pass the codes and the source `title` and `description` to a translation
   generation system;
3. upload the resulting UTF-8 JSON file on the Translate page;
4. review the Preview changes report and publish the video localizations to YouTube.

The script does not translate text or publish videos. It only refreshes the
language catalog so a generation system can use the current list.

## Generated file

After a successful run, the tool creates:

```text
data/youtube-languages.json
```

The file contains:

- `code` — the value of `item.snippet.hl`;
- `name` — the value of `item.snippet.name`;
- `id` — the value of `item.id`;
- `count` — the actual number of returned items;
- `fetchedAt` — the UTC time when the catalog was fetched.

Example record:

```json
{
  "code": "en",
  "name": "English",
  "id": "en"
}
```

## Setup

The project already uses `python-dotenv`, so the key can be stored in the
project root `.env` file:

```dotenv
YOUTUBE_API_KEY=your_api_key
```

`.env` is excluded from Git. The key is not written to the JSON file or
printed to the terminal.

## Run the catalog tool

From the project root:

```bash
source .venv/bin/activate
YOUTUBE_API_KEY=xxx npm run youtube:languages
```

If the key is already in `.env`, run:

```bash
npm run youtube:languages
```

On success, the script prints the actual number of languages:

```text
Fetched 85 YouTube languages -> data/youtube-languages.json
```

The number is read from the latest API response and is not fixed. If the key
is missing, the file is not created and an existing file is not overwritten.

## Localization workflow

### 1. Refresh the catalog

Run the script immediately before preparing a new translation set. Do not use
an old list from memory or a separate static file as the source of truth.

### 2. Prepare the source text

Select a video in the web application and prepare its `title` and
`description`. A second source-language version can be supplied to a reviewer
or generation system when it helps verify meaning, names, terminology, and
context.

### 3. Provide the catalog to the generation system

Provide the system with:

- the source `title` and `description`;
- `data/youtube-languages.json` or its `languages` array;
- the prompt below.

The prompt must request meaning-based translation instead of word-for-word
replacement. The result keys must be the BCP-47 codes from `code`, not the
translated language names.

Prompt template:

```text
You are a YouTube localization specialist.

Source video title:
<SOURCE_TITLE>

Source video description:
<SOURCE_DESCRIPTION>

Optional second source-language version for verification:
<SECOND_SOURCE_LANGUAGE_AND_TEXT>

The current data/youtube-languages.json file is attached below. Translate the
title and description by meaning for every language in the languages array.

Rules:
1. Preserve the source meaning, facts, tone, calls to action, names, brand
   names, URLs, hashtags, and technical notation.
2. Do not translate mechanically word for word. Use natural wording for a
   native speaker of the target language.
3. Use the exact languages[].code value as the result key for every item. Do
   not invent codes and do not use languages[].name as a key.
4. Return one JSON object without Markdown, comments, or explanations:
   {
     "<language-code>": {
       "title": "...",
       "description": "..."
     }
   }
5. Do not add fields other than title and description.
6. Do not omit languages from the languages array.
7. Preserve line breaks correctly inside valid JSON.
8. Keep title at or below 100 characters and description at or below 5,000
   characters.

Return only the JSON object.
```

Before sending the result to the application, verify that it is a localization
object and not a wrapper such as `{"languages": [...]}`.

### 4. Upload JSON to the web application

1. Open the web application and choose **Translate**.
2. Click **Select** on the required video card.
3. Open **LLM Translation prompt** if you need to prepare an external-LLM result,
   then return to **Translate** and upload the UTF-8 JSON file.
4. Click **Preview changes**.
5. Review added, changed, unchanged, and invalid languages.
6. Click **Publish changes** only after reviewing the preview.

The web application validates the uploaded document, fetches the current video
state again before publishing, and merges submitted localizations with existing
ones. Languages omitted from the submitted JSON are therefore preserved. Only
localizations included in the JSON and accepted by YouTube/API validation are
updated.

Minimal application format:

```json
{
  "de": {
    "title": "Translated title",
    "description": "Translated description"
  },
  "fr": {
    "title": "Titre traduit",
    "description": "Description traduite"
  }
}
```

## Security and errors

- The API key is read only from `YOUTUBE_API_KEY` or `.env`.
- Google API errors may show an HTTP status and a safe Google message, but
  never the key.
- A malformed response without `items` does not overwrite the JSON file.
- The script uses the fresh `i18nLanguages.list` response and does not embed a
  static language array.
- YouTube limits localized `title` and `description` length; review the web
  application preview before publishing.
