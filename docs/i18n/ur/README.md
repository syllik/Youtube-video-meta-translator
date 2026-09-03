# YouTube Video Metadata Translator

**زبان نیویگیشن:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · **اردو** · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## یہ کیا کرتا ہے

یہ مقامی Streamlit ایپ YouTube ویڈیوز کے title اور description کی localization کو منظم کرتی ہے۔ ویڈیو منتخب کریں، JSON بنائیں یا upload کریں، Preview changes میں جانچیں اور پھر Publish changes کریں۔ Codex یا بیرونی LLM کا نتیجہ خودکار طور پر publish نہیں ہوتا۔

## ضروریات

چینل تک رسائی والا Google account، Python 3.12، اسی کمپیوٹر کا browser اور Desktop app OAuth JSON درکار ہے۔ اختیاری Codex طریقے کے لیے Node.js اور npm بھی درکار ہیں۔ Translate اور LLM Translation prompt کے لیے OpenAI یا کسی LLM API key کی ضرورت نہیں۔

## انسٹالیشن

### macOS / Linux

~~~bash
git clone https://github.com/syllik/youtube-metadata-translator.git
cd youtube-metadata-translator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

### Windows PowerShell

~~~powershell
cd C:\path\to\youtube-metadata-translator
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

## Google OAuth ترتیب

Google Cloud Console میں project بنا کر YouTube Data API v3 فعال کریں۔ Google Auth Platform میں **Desktop app** client بنائیں، JSON download کریں، اور اسے یہاں رکھیں:

~~~text
config/account_client_secrets_main.json
~~~

پہلی authorization میں channel manage کرنے والا account استعمال کریں اور local callback 127.0.0.1:8080 کی اجازت دیں۔ Web application client یا عام API key استعمال نہ کریں۔

## ایپ شروع کریں

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows میں `..venv\Scripts\Activate.ps1` چلا کر یہی Streamlit command استعمال کریں۔ http://127.0.0.1:8501 کھولیں۔

## Translate workflow

1. Sidebar میں ایک ویڈیو منتخب کریں۔
2. **Source languages** میں default زبان کو primary source رہنے دیں اور موجودہ localizations کو optional references کے طور پر منتخب کریں۔
3. draft کے لیے **Codex** یا **External LLM** استعمال کریں۔
4. **Preview changes** میں diff چیک کریں۔
5. صرف موجودہ valid preview کے بعد **Publish changes** کریں۔
6. YouTube Studio میں نتیجہ confirm کریں۔

### Primary source اور optional references

Default زبان read-only **Primary source** ہے۔ صرف موجودہ localizations **Optional reference translations** ہو سکتی ہیں؛ references صاف کرنے سے primary source ختم نہیں ہوتا۔ ویڈیو بدلنے پر draft اور preview state صاف ہو جاتی ہے۔

## Codex

مقامی Codex CLI install اور login کریں:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** میں target languages منتخب کر کے generation چلائیں۔ Codex صرف review کے لیے draft بناتا ہے اور براہ راست publish نہیں کرتا۔ ناکامی پر اسی terminal میں `codex --version` اور `codex login status` چلا کر Streamlit restart کریں۔

## External LLM

1. **Prepare prompt** دبائیں۔
2. Prompt بیرونی LLM میں دے کر صرف مطلوبہ language codes والا UTF-8 JSON بنائیں۔
3. **Upload JSON** سے file upload کریں۔ Uploader تبھی فعال ہوتا ہے جب prompt موجودہ video اور target set سے bound ہو؛ JSON validation اور Preview کے بعد publish کیا جا سکتا ہے۔

ہر value میں صرف title اور description ہوں؛ title زیادہ سے زیادہ 100 اور description 5,000 characters۔ wrapper metadata، Markdown، زبانوں کے نام یا duplicate keys upload نہ کریں۔

## Preview changes

Preview read-only ہے اور videos.update call نہیں کرتا۔ Report added، changed، unchanged اور draft میں نہ ہونے کے باوجود YouTube میں محفوظ رہنے والی localizations دکھاتا ہے۔

## Publish changes

Publish draft کو دوبارہ validate کر کے write سے پہلے video دوبارہ fetch کرتا ہے۔ Video بدل جائے تو write نہیں ہوتا۔ کامیاب write کے بعد sidebar cache clear اور count دوبارہ fetch ہوتا ہے؛ no-change یا conflict کو کامیاب refresh نہیں دکھایا جاتا۔

## Danger zone: Reset languages

**Reset languages** صرف منتخب video کی collapsed **Danger zone** میں دکھائی دیتا ہے۔ تصدیق کے بعد fresh usable ETag ضروری ہے اور conditional If-Match write ہوتی ہے؛ non-default localizations ہٹا کر default metadata محفوظ رہتا ہے۔ selection بدلنا، ETag نہ ہونا یا HTTP 412 no-write failure ہے، automatic retry نہیں۔ ضروری translations پہلے save کریں۔

## خرابی اور سکیورٹی

OAuth file missing یا malformed ہو تو نیا Desktop app JSON download کریں۔ callback ناکام ہو تو terminal کھلا رکھیں اور 127.0.0.1:8080 allow کریں؛ authorization expire/revoke ہو تو دوبارہ authorize کریں اور token.json صرف ضرورت پر حذف کریں۔ quota، network، missing video اور Codex login errors میں UI کا action کریں۔ OAuth JSON، token.json، API token یا مکمل environment output شیئر نہ کریں۔

## لائسنس

[LICENSE](../../../LICENSE) دیکھیں۔
