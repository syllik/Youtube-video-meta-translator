# YouTube Video Metadata Translator

**भाषा नेविगेशन:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · **भोजपुरी**

## ई का करेला?

ई लोकल Streamlit ऐप YouTube वीडियो के title आ description के localization संभालेला। वीडियो चुन के JSON बनाईं या upload करीं, Preview changes में जाँच करीं आ फेर Publish changes करीं। Codex भा बाहरी LLM के नतीजा अपने-आप publish ना होला।

## जरूरत

Channel access वाला Google account, Python 3.12, ओही computer के browser आ Desktop app client के OAuth JSON चाहीं। Codex वाला वैकल्पिक तरीका खातिर Node.js आ npm भी चाहीं। Translate आ LLM Translation prompt खातिर OpenAI भा कवनो LLM API key ना चाहीं।

## इंस्टॉल करीं

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

## Google OAuth सेट करीं

Google Cloud Console में project बना के YouTube Data API v3 चालू करीं। Google Auth Platform में **Desktop app** client बना के JSON download करीं आ ठीक इहाँ रखीं:

~~~text
config/account_client_secrets_main.json
~~~

पहिला authorization channel चलावे वाला account से करीं आ local callback 127.0.0.1:8080 के अनुमति दीं। Web application client भा साधारण API key मत इस्तेमाल करीं।

## ऐप चलाईं

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows में `..venv\Scripts\Activate.ps1` चला के ई Streamlit command चलाईं। http://127.0.0.1:8501 खोलीं।

## Translate workflow

1. Sidebar में एगो वीडियो चुनीं।
2. **Source languages** में default भाषा के primary source रखीं आ मौजूद localizations के optional references के रूप में चुनीं।
3. **Codex** भा **External LLM** से draft बनाईं।
4. **Preview changes** में diff देखीं।
5. वर्तमान preview valid होखे तबे **Publish changes** करीं।
6. YouTube Studio में परिणाम जाँचीं।

### Primary source आ optional references

Default भाषा read-only **Primary source** ह। खाली मौजूद localizations **Optional reference translations** बन सकेलीं; references साफ कइला से primary source ना मिटी। वीडियो बदले पर draft आ preview state साफ हो जाला।

## Codex

लोकल Codex CLI install क के login करीं:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** में target languages चुन के generation चलाईं। Codex खाली review खातिर draft बनावेला, सीधा publish ना करेला। दिक्कत होखे त ओही terminal में `codex --version` आ `codex login status` चला के Streamlit restart करीं।

## External LLM

1. **Prepare prompt** दबाईं।
2. Prompt बाहरी LLM में paste क के खाली माँगल language codes वाला UTF-8 JSON बनाईं।
3. **Upload JSON** से file upload करीं। Prompt वर्तमान वीडियो आ target set से bound होखला के बादे uploader चालू होला; app JSON validate क के Preview के बाद publish करे देला।

हर value में title आ description भर होखे; title 100 आ description 5,000 characters से बेसी ना होखे। wrapper metadata, Markdown, भाषा के नाम भा duplicate keys upload मत करीं।

## Preview changes

Preview read-only ह आ videos.update call ना करेला। Report में added, changed, unchanged आ draft में ना रहे वाला बाकिर YouTube में बाँचल localizations देखाला।

## Publish changes

Publish draft के फेर validate करेला आ write से पहिले video फेर fetch करेला। वीडियो बदल गइल होखे त write ना होला। सफल write के बाद sidebar cache साफ होके count फेर fetch होला; no-change भा conflict के सफल refresh ना बतावल जाला।

## Danger zone: Reset languages

**Reset languages** खाली चुनल वीडियो के collapsed **Danger zone** में देखाई देला। Confirm के बाद fresh usable ETag जरूरी बा आ conditional If-Match write होला; non-default localizations हट जालीं, default metadata बचल रहे ला। selection बदले, ETag ना मिले भा HTTP 412 no-write failure ह, automatic retry ना होला। बचावे वाला translation पहिले save करीं।

## दिक्कत आ सुरक्षा

OAuth file ना मिले भा malformed होखे त नया Desktop app JSON download करीं। callback fail होखे त terminal खुलल रखीं आ 127.0.0.1:8080 के अनुमति दीं; authorization expire/revoke होखे त फेर authorize करीं आ token.json खाली जरूरत पर हटाईं। quota, network, missing video भा Codex login error खातिर UI के action करीं। OAuth JSON, token.json, API token भा पूरा environment output share मत करीं।

## लाइसेंस

[LICENSE](../../../LICENSE) देखीं।
