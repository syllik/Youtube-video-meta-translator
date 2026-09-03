# YouTube Video Metadata Translator

**மொழி வழிசெலுத்தல்:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · **தமிழ்** · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## இது என்ன செய்கிறது

YouTube வீடியோ title மற்றும் description localization-ஐ நிர்வகிக்கும் உள்ளூர் Streamlit பயன்பாடு இது. வீடியோவைத் தேர்ந்தெடுத்து JSON உருவாக்கவும் அல்லது upload செய்யவும், Preview changes மூலம் சரிபார்த்து Publish changes செய்யவும். Codex அல்லது வெளிப்புற LLM முடிவு தானாக வெளியிடப்படாது.

## தேவைகள்

Channel access உள்ள Google account, Python 3.12, அதே கணினியில் browser மற்றும் Desktop app OAuth JSON தேவை. விருப்பமான Codex வழிக்கு Node.js மற்றும் npm தேவை. Translate மற்றும் LLM Translation prompt-க்கு OpenAI அல்லது வேறு LLM API key தேவையில்லை.

## நிறுவல்

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

## Google OAuth அமைப்பு

Google Cloud Console-ல் project உருவாக்கி YouTube Data API v3-ஐ enable செய்யவும். Google Auth Platform-ல் **Desktop app** client உருவாக்கி JSON-ஐ இதே இடத்தில் சேமிக்கவும்:

~~~text
config/account_client_secrets_main.json
~~~

முதல் authorization-க்கு channel நிர்வகிக்கும் account-ஐப் பயன்படுத்தி local callback 127.0.0.1:8080-ஐ அனுமதிக்கவும். Web application client அல்லது சாதாரண API key பயன்படுத்த வேண்டாம்.

## பயன்பாட்டைத் தொடங்குதல்

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows-ல் `..venv\Scripts\Activate.ps1` இயக்கி அதே Streamlit command-ஐப் பயன்படுத்தவும். http://127.0.0.1:8501-ஐத் திறக்கவும்.

## Translate workflow

1. Sidebar-ல் ஒரு வீடியோவைத் தேர்ந்தெடுக்கவும்.
2. **Source languages**-ல் default மொழியை primary source ஆக வைத்துக் கொண்டு, உள்ள localizations-ஐ optional references ஆகத் தேர்ந்தெடுக்கவும்.
3. **Codex** அல்லது **External LLM** மூலம் draft உருவாக்கவும்.
4. **Preview changes**-ல் diff-ஐப் பரிசோதிக்கவும்.
5. தற்போதைய preview valid ஆக இருந்தால் மட்டுமே **Publish changes** செய்யவும்.
6. YouTube Studio-ல் முடிவைச் சரிபார்க்கவும்.

### Primary source மற்றும் optional references

Default மொழி read-only **Primary source**. உள்ள localizations மட்டும் **Optional reference translations** ஆகும்; references-ஐ அழித்தாலும் primary source அழியாது. வீடியோ மாற்றும்போது draft மற்றும் preview state அழிக்கப்படும்.

## Codex

உள்ளூர் Codex CLI-ஐ install செய்து login செய்யவும்:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate**-ல் target languages தேர்ந்தெடுத்து generation இயக்கவும். Codex review-க்கான draft மட்டும் உருவாக்கும், நேரடியாக publish செய்யாது. தோல்வியுற்றால் அதே terminal-ல் `codex --version` மற்றும் `codex login status` இயக்கி Streamlit-ஐ restart செய்யவும்.

## External LLM

1. **Prepare prompt** அழுத்தவும்.
2. Prompt-ஐ வெளிப்புற LLM-ல் பயன்படுத்தி கேட்கப்பட்ட language codes மட்டும் உள்ள UTF-8 JSON உருவாக்கவும்.
3. **Upload JSON** மூலம் file upload செய்யவும். Prompt தற்போதைய video மற்றும் target set உடன் bind ஆன பிறகே uploader enable ஆகும்; JSON validation மற்றும் Preview முடிந்த பிறகு publish செய்யலாம்.

ஒவ்வொரு value-லும் title மற்றும் description மட்டும் இருக்க வேண்டும்; title 100, description 5,000 characters வரை. wrapper metadata, Markdown, language names அல்லது duplicate keys upload செய்ய வேண்டாம்.

## Preview changes

Preview read-only ஆகும்; videos.update call செய்யாது. Report added, changed, unchanged மற்றும் draft-ல் இல்லாவிட்டாலும் YouTube-ல் பாதுகாக்கப்படும் localizations-ஐ காட்டும்.

## Publish changes

Publish draft-ஐ மீண்டும் validate செய்து write-க்கு முன் video-ஐ மீண்டும் fetch செய்யும். Video மாறியிருந்தால் write நடக்காது. வெற்றிகரமான write-க்கு பிறகு sidebar cache clear செய்து count மீண்டும் பெறப்படும்; no-change அல்லது conflict வெற்றிகரமான refresh என்று காட்டப்படாது.

## Danger zone: Reset languages

**Reset languages** தேர்ந்தெடுத்த video-ன் collapsed **Danger zone**-ல் மட்டும் இருக்கும். உறுதிப்படுத்திய பிறகு fresh usable ETag தேவை; conditional If-Match write மூலம் non-default localizations நீக்கப்பட்டு default metadata காக்கப்படும். selection மாற்றம், ETag இல்லாமை அல்லது HTTP 412 no-write failure; automatic retry இல்லை. தேவைப்படும் translations-ஐ முதலில் சேமிக்கவும்.

## சிக்கல் தீர்வு மற்றும் பாதுகாப்பு

OAuth file இல்லை அல்லது malformed என்றால் புதிய Desktop app JSON download செய்யவும். callback தோல்வியுற்றால் terminal திறந்திருக்க வைத்து 127.0.0.1:8080 அனுமதிக்கவும்; authorization expire/revoke ஆனால் மீண்டும் authorize செய்து token.json-ஐ தேவையானபோது மட்டும் நீக்கவும். quota, network, missing video அல்லது Codex login errors-க்கு UI action-ஐப் பின்பற்றவும். OAuth JSON, token.json, API token அல்லது முழு environment output-ஐ பகிர வேண்டாம்.

## உரிமம்

[LICENSE](../../../LICENSE)-ஐப் பார்க்கவும்.
