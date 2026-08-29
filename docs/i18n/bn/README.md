# YouTube Video Metadata Translator

**ভাষা নেভিগেশন:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · **বাংলা** · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## এটি কী করে

এটি একটি স্থানীয় Streamlit অ্যাপ, যা YouTube ভিডিওর title ও description localization পরিচালনা করে। ভিডিও বেছে নিয়ে JSON তৈরি বা আপলোড করুন, Preview changes দেখে তারপর Publish changes করুন। Codex বা বাইরের LLM-এর ফলাফল নিজে থেকে প্রকাশিত হয় না।

## প্রয়োজনীয়তা

চ্যানেলের অনুমতি-সহ Google account, Python 3.12, একই কম্পিউটারের browser এবং Desktop app OAuth JSON প্রয়োজন। Codex-এর ঐচ্ছিক পথে Node.js ও npm-ও লাগবে। Translate ও LLM Translation prompt-এর জন্য OpenAI বা অন্য LLM API key দরকার নেই।

## ইনস্টলেশন

### macOS / Linux

~~~bash
git clone https://github.com/syllik/Youtube-video-meta-translator.git
cd Youtube-video-meta-translator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

### Windows PowerShell

~~~powershell
cd C:\path\to\Youtube-video-meta-translator
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

## Google OAuth সেটআপ

Google Cloud Console-এ project তৈরি করে YouTube Data API v3 চালু করুন। Google Auth Platform-এ **Desktop app** client তৈরি করে JSON ডাউনলোড করুন। ফাইলটি ঠিক এই জায়গায় রাখুন:

~~~text
config/account_client_secrets_main.json
~~~

প্রথম authorization-এ channel পরিচালনাকারী account ব্যবহার করুন এবং local callback 127.0.0.1:8080 অনুমতি দিন। Web application client বা সাধারণ API key ব্যবহার করবেন না।

## অ্যাপ চালু করুন

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows-এ `..venv\Scripts\Activate.ps1` চালিয়ে একই Streamlit command ব্যবহার করুন। http://127.0.0.1:8501 খুলুন।

## Translate workflow

1. Sidebar-এ একটি ভিডিও বাছুন।
2. **Source languages**-এ default ভাষাকে primary source রাখুন এবং বিদ্যমান localizations-কে optional reference হিসেবে বাছুন।
3. draft তৈরির জন্য **Codex** বা **External LLM** ব্যবহার করুন।
4. **Preview changes**-এ diff পরীক্ষা করুন।
5. বর্তমান preview বৈধ থাকলেই **Publish changes** চাপুন।
6. YouTube Studio-তে ফলাফল নিশ্চিত করুন।

### Primary source ও optional references

Default ভাষা read-only **Primary source**। কেবল বিদ্যমান localizations **Optional reference translations** হতে পারে; reference মুছলে primary source মুছে যায় না। ভিডিও বদলালে draft ও preview state পরিষ্কার হয়।

## Codex

স্থানীয় Codex CLI ইনস্টল ও login করুন:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate**-এ target languages বেছে generation চালান। Codex শুধু review-এর draft তৈরি করে, সরাসরি publish করে না। ব্যর্থ হলে একই terminal-এ `codex --version` ও `codex login status` চালিয়ে Streamlit restart করুন।

## External LLM

1. **Prepare prompt** চাপুন।
2. Prompt বাইরের LLM-এ paste করে শুধু অনুরোধ করা language codes-সহ UTF-8 JSON তৈরি করুন।
3. **Upload JSON** দিয়ে file upload করুন। Prompt বর্তমান video ও target set-এর সঙ্গে bound হলে তবেই uploader সক্রিয় হয়; JSON validation ও Preview-এর পর publish করা যায়।

প্রতিটি value-তে শুধু title ও description থাকবে; title সর্বোচ্চ 100 এবং description 5,000 characters। wrapper metadata, Markdown, language names বা duplicate keys আপলোড করবেন না।

## Preview changes

Preview read-only এবং videos.update call করে না। Report-এ added, changed, unchanged এবং draft-এ বাদ পড়লেও YouTube-এ থাকা localizations-এর preservation দেখায়।

## Publish changes

Publish draft আবার validate করে এবং ভিডিও পুনরায় fetch করে। ভিডিও বদলে গেলে write হয় না। সফল write sidebar cache পরিষ্কার করে count আবার আনে; no-change বা conflict-কে সফল refresh বলা হয় না।

## Danger zone: Reset languages

**Reset languages** কেবল নির্বাচিত ভিডিওর collapsed **Danger zone**-এ আছে। Confirm করার পর fresh usable ETag আবশ্যক এবং conditional If-Match write হয়; non-default localizations সরিয়ে default metadata রাখা হয়। selection বদল, ETag না থাকা বা HTTP 412 no-write failure, automatic retry নেই। দরকারি translation আগে সংরক্ষণ করুন।

## সমস্যা সমাধান ও নিরাপত্তা

OAuth file missing বা malformed হলে নতুন Desktop app JSON ডাউনলোড করে UI-এর action অনুসরণ করুন। callback ব্যর্থ হলে terminal খোলা রেখে 127.0.0.1:8080 অনুমতি দিন; authorization expire/revoke হলে আবার authorize করুন এবং প্রয়োজন ছাড়া token.json মুছবেন না। quota, network, missing video ও Codex login error-এর জন্য UI-এর নির্দেশ অনুসরণ করুন। OAuth JSON, token.json, API token বা সম্পূর্ণ environment output শেয়ার করবেন না।

## লাইসেন্স

[LICENSE](../../../LICENSE) দেখুন।
