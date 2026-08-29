# YouTube Video Metadata Translator

**زبان نیویگیشن:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · **پنجابی** · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## ایہ کی کردا اے

ایہ مقامی Streamlit ایپ YouTube ویڈیو دے title تے description دی localization سنبھالدی اے۔ ویڈیو چنو، JSON بناؤ یا upload کرو، Preview changes وچ جانچ کرو تے فیر Publish changes کرو۔ Codex یا بیرونی LLM دا نتیجہ آپے publish نہیں ہوندا۔

## لوڑاں

چینل تک رسائی والا Google اکاؤنٹ، Python 3.12، اوہو کمپیوٹر دا browser تے Desktop app OAuth JSON لوڑ اے۔ Codex والے اختیاری طریقے لئی Node.js تے npm وی چاہیدے نیں۔ Translate تے LLM Translation prompt لئی OpenAI یا ہور LLM API key نہیں چاہیدی۔

## انسٹالیشن

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

## Google OAuth دی ترتیب

Google Cloud Console وچ project بنا کے YouTube Data API v3 چالو کرو۔ Google Auth Platform وچ **Desktop app** client بنا کے JSON download کرو تے اینج رکھو:

~~~text
config/account_client_secrets_main.json
~~~

پہلی authorization لئی channel والا account استعمال کرو تے local callback 127.0.0.1:8080 دی اجازت دو۔ Web application client یا عام API key نہ ورتو۔

## ایپ چلاؤ

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows وچ `..venv\Scripts\Activate.ps1` چلا کے ایہ Streamlit command ورتو۔ http://127.0.0.1:8501 کھولو۔

## Translate دا کم

1. Sidebar وچ اک ویڈیو چنو۔
2. **Source languages** وچ default زبان primary source رہن دو تے موجودہ localizations نوں optional references چنو۔
3. **Codex** یا **External LLM** نال draft بناؤ۔
4. **Preview changes** وچ diff ویکھو۔
5. صرف موجودہ valid preview دے بعد **Publish changes** کرو۔
6. YouTube Studio وچ نتیجہ پکا کرو۔

### Primary source تے optional references

Default زبان read-only **Primary source** اے۔ صرف موجودہ localizations **Optional reference translations** بن سکدیاں نیں؛ references صاف کرن نال primary source نہیں مٹدا۔ ویڈیو بدلنے نال draft تے preview state صاف ہو جاندی اے۔

## Codex

مقامی Codex CLI install تے login کرو:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** وچ target languages چن کے generation چلاو۔ Codex صرف review لئی draft بناندا اے، سیدھا publish نہیں کردا۔ ناکامی تے اوہنے terminal وچ `codex --version` تے `codex login status` چلا کے Streamlit restart کرو۔

## External LLM

1. **Prepare prompt** دباؤ۔
2. Prompt بیرونی LLM وچ paste کر کے صرف منگے گئے language codes والا UTF-8 JSON بناؤ۔
3. **Upload JSON** نال file upload کرو۔ Uploader اوہدوں ای فعال ہوندا اے جدوں prompt موجودہ ویڈیو تے target set نال bound ہووے؛ JSON validation تے Preview توں بعد publish کرو۔

ہر value وچ صرف title تے description ہوون؛ title 100 تے description 5,000 characters تک۔ wrapper metadata، Markdown، زبان دے ناں یا duplicate keys upload نہ کرو۔

## Preview changes

Preview read-only اے تے videos.update نہیں کردا۔ Report added، changed، unchanged تے draft توں باہر مگر محفوظ رہن والی YouTube localizations وکھاندا اے۔

## Publish changes

Publish draft نوں فیر validate تے ویڈیو نوں فیر fetch کردا اے۔ ویڈیو بدل گئی ہووے تے write نہیں ہوندا۔ کامیاب write تے sidebar cache صاف تے count دوبارہ آ جاندا اے؛ no-change یا conflict نوں کامیاب refresh نہیں آکھیا جاندا۔

## Danger zone: Reset languages

**Reset languages** صرف selected ویڈیو دی collapsed **Danger zone** وچ اے۔ Confirm توں بعد fresh usable ETag ضروری اے تے conditional If-Match write ہوندی اے؛ non-default localizations ہٹ کے default metadata بچدا اے۔ selection بدلنا، ETag نہ ہونا یا HTTP 412 no-write failure اے، automatic retry نہیں۔ ضروری translations پہلے save کرو۔

## مسئلہ تے حفاظت

OAuth file نہ ہووے یا خراب ہووے تے نواں Desktop app JSON download کرو۔ callback فیل ہووے تے terminal کھلا رکھو تے 127.0.0.1:8080 allow کرو؛ authorization expire یا revoke ہووے تے فیر authorize کرو، token.json صرف ضرورت تے مٹاؤ۔ quota، network، missing video تے Codex login errors لئی UI دا action کرو۔ OAuth JSON، token.json، API tokens یا پورا environment output share نہ کرو۔

## لائسنس

[LICENSE](../../../LICENSE) ویکھو۔
