# YouTube Video Metadata Translator

**भाषा नेविगेशन:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · **हिन्दी** · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## यह क्या करता है

यह स्थानीय Streamlit ऐप YouTube वीडियो के title और description localization को प्रबंधित करता है। वीडियो चुनें, JSON बनाएँ या अपलोड करें, Preview changes देखें और फिर Publish changes करें। Codex या बाहरी LLM का परिणाम अपने-आप प्रकाशित नहीं होता।

## आवश्यकताएँ

चैनल की अनुमति वाला Google खाता, Python 3.12, उसी कंप्यूटर का browser और Desktop app OAuth JSON चाहिए। Codex का वैकल्पिक तरीका Node.js और npm भी मांगता है। Translate और LLM Translation prompt के लिए OpenAI या किसी अन्य LLM API key की जरूरत नहीं है।

## इंस्टॉल करें

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

## Google OAuth सेटअप

Google Cloud Console में project बनाकर YouTube Data API v3 सक्षम करें। Google Auth Platform में **Desktop app** client बनाएँ और JSON डाउनलोड करें। इसे ठीक इस स्थान पर रखें:

~~~text
config/account_client_secrets_main.json
~~~

पहले authorization में channel वाले Google खाते का उपयोग करें और local callback 127.0.0.1:8080 की अनुमति दें। Web application client या साधारण API key न चुनें।

## ऐप चलाएँ

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows में `..venv\Scripts\Activate.ps1` के बाद यही Streamlit command चलाएँ। http://127.0.0.1:8501 खोलें।

## Translate workflow

1. Sidebar में एक वीडियो चुनें।
2. **Source languages** में default भाषा को primary source रखें और मौजूदा localizations को optional references के रूप में चुनें।
3. draft बनाने के लिए **Codex** या **External LLM** चुनें।
4. **Preview changes** में diff जाँचें।
5. current preview मान्य हो तभी **Publish changes** चुनें।
6. YouTube Studio में परिणाम जाँचें।

### Primary source और optional references

Default भाषा read-only **Primary source** है। केवल मौजूदा localizations **Optional reference translations** हो सकती हैं; references हटाने से primary source नहीं हटता। वीडियो बदलने पर draft और preview state साफ हो जाती है।

## Codex

स्थानीय Codex CLI install और login करें:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** में target languages चुनकर generation चलाएँ। Codex केवल review के लिए draft बनाता है, सीधे publish नहीं करता। failure पर उसी terminal में `codex --version` और `codex login status` चलाकर Streamlit restart करें।

## External LLM

1. **Prepare prompt** चुनें।
2. Prompt को बाहरी LLM में paste करके केवल माँगे गए language codes वाला UTF-8 JSON बनाएँ।
3. **Upload JSON** से file upload करें। Prompt के current video और target set से बंधे होने पर ही uploader सक्रिय होगा; JSON validation और Preview के बाद publish किया जा सकता है।

हर value में केवल title और description हों; title अधिकतम 100 और description 5,000 characters। wrapper metadata, Markdown, language names या duplicate keys न भेजें।

## Preview changes

Preview read-only है और videos.update नहीं बुलाता। Report added, changed, unchanged entries और draft में न दी गई लेकिन सुरक्षित रहने वाली YouTube localizations दिखाती है।

## Publish changes

Publish draft को फिर validate करके वीडियो दोबारा fetch करता है। वीडियो बदल गया हो तो write नहीं होता। सफल write पर sidebar cache साफ होकर count फिर fetch होता है; no-change या conflict को success refresh नहीं बताया जाता।

## Danger zone: Reset languages

**Reset languages** केवल selected video की collapsed **Danger zone** में है। पुष्टि के बाद fresh usable ETag अनिवार्य है और conditional If-Match write होती है; non-default localizations हटती हैं, default metadata बचता है। selection बदलना, ETag न मिलना या HTTP 412 no-write failure है और automatic retry नहीं होता। जरूरी translations पहले बचाएँ।

## समस्या और सुरक्षा

OAuth file missing या malformed हो तो नया Desktop app JSON डाउनलोड करें। callback के लिए terminal खुला रखें और 127.0.0.1:8080 अनुमति दें; authorization expire/revoke हो तो फिर authorize करें और केवल जरूरत पर token.json हटाएँ। quota, network, missing video और Codex login errors के लिए UI का action अपनाएँ। OAuth JSON, token.json, API tokens या पूरा environment output साझा न करें।

## लाइसेंस

[LICENSE](../../../LICENSE) देखें।
