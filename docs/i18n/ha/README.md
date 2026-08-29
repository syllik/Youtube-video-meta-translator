# YouTube Video Metadata Translator

**Kewayen harsuna:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · **Hausa** · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Me yake yi?

Wannan manhajar Streamlit ta gida tana kula da title da description na bidiyon YouTube a harsuna daban-daban. Zaɓi bidiyo, ƙirƙiri ko upload JSON, duba shi da Preview changes sannan ka yi Publish changes. Ba a taɓa publish sakamakon Codex ko LLM na waje kai tsaye ba.

## Abubuwan da ake buƙata

Ana buƙatar Google account mai damar channel, Python 3.12, browser a kwamfutar ɗaya, da OAuth JSON na client na nau’in Desktop app. Hanyar Codex ta zaɓi tana buƙatar Node.js da npm. Translate da LLM Translation prompt ba sa buƙatar OpenAI ko wani LLM API key.

## Sanya manhajar

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

## Saita Google OAuth

A Google Cloud Console ƙirƙiri project kuma kunna YouTube Data API v3. A Google Auth Platform ƙirƙiri client **Desktop app**, sauke JSON, sannan ajiye shi daidai a:

~~~text
config/account_client_secrets_main.json
~~~

A authorization ta farko yi amfani da account da ke kula da channel, kuma ka ba local callback 127.0.0.1:8080 izini. Kada ka yi amfani da Web application client ko API key na yau da kullum.

## Fara manhajar

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

A Windows fara da `..venv\Scripts\Activate.ps1`, sannan yi wannan umarnin Streamlit. Buɗe http://127.0.0.1:8501.

## Tsarin Translate

1. Zaɓi bidiyo ɗaya a sidebar.
2. A **Source languages**, bar harshen default a matsayin primary source, sannan zaɓi localizations da suke akwai a matsayin optional references.
3. Yi draft da **Codex** ko **External LLM**.
4. Duba bambanci da **Preview changes**.
5. Yi **Publish changes** ne kawai idan preview na yanzu yana valid.
6. Tabbatar da sakamakon a YouTube Studio.

### Primary source da optional references

Harshen default shi ne **Primary source** mai karatu-kawai. Localizations da suke akwai kaɗai za su iya zama **Optional reference translations**; share references ba ya share primary source. Canza bidiyo yana share draft da preview state.

## Codex

Sanya kuma yi login zuwa Codex CLI na gida:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

A **Translate** zaɓi target languages ka fara generation. Codex yana ƙirƙirar draft don review kawai, ba ya publish kai tsaye. Idan ya gaza, yi `codex --version` da `codex login status` a terminal ɗin nan sannan ka restart Streamlit.

## External LLM

1. Danna **Prepare prompt**.
2. Liƙa prompt a LLM na waje ka ƙirƙiri UTF-8 JSON mai ɗauke da language codes da aka nema kawai.
3. Yi **Upload JSON** don ɗora file. Uploader yana aiki ne bayan prompt ya kasance an haɗa shi da bidiyo da target set na yanzu; app ɗin zai validate JSON sannan ya ba da Preview kafin publish.

Kowane value ya ƙunshi title da description kawai; title bai wuce 100 ba, description bai wuce characters 5,000 ba. Kada ka upload wrapper metadata, Markdown, sunayen harsuna, ko duplicate keys.

## Preview changes

Preview na karatu-kawai ne kuma ba ya kiran videos.update. Report yana nuna added, changed, unchanged, da localizations na YouTube da ba sa cikin draft amma za a riƙe su.

## Publish changes

Publish yana sake validate draft kuma ya sake fetch bidiyon kafin write. Idan bidiyon ya canza, ba a yin write. Bayan write mai nasara, sidebar cache yana sharewa kuma count yana sake fetch; no-change ko conflict ba a nuna su a matsayin refresh mai nasara.

## Danger zone: Reset languages

**Reset languages** yana bayyana ne kawai a cikin folded **Danger zone** na bidiyon da aka zaɓa. Bayan confirm, ana buƙatar fresh usable ETag kuma a yi conditional If-Match write; a cire localizations marasa default, a bar default metadata. Canjin selection, rashin ETag ko HTTP 412 no-write failure ne ba tare da automatic retry ba. Ajiye translations da kake son riƙewa tun da wuri.

## Magance matsala da tsaro

Idan OAuth file ya ɓace ko malformed ne, sauke sabon JSON na Desktop app. Idan callback ya gaza, bar terminal a buɗe ka ba 127.0.0.1:8080 izini; idan authorization ya ƙare ko an revoke shi, yi authorize kuma ka share token.json ne kawai idan ya zama dole. Bi action na UI don quota, network, missing video ko kuskuren Codex login. Kada ka raba OAuth JSON, token.json, API token ko cikakken environment output.

## Lasisi

Duba [LICENSE](../../../LICENSE).
