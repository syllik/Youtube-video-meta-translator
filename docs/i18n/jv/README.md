# YouTube Video Metadata Translator

**Navigasi basa:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · **Basa Jawa** · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Gunane

Aplikasi Streamlit lokal iki kanggo ngatur title lan description video YouTube ing macem-macem basa. Pilih video, gawe utawa upload JSON, priksa nganggo Preview changes, banjur gunakake Publish changes. Hasil saka Codex utawa LLM njaba ora tau dipublikasi kanthi otomatis.

## Syarat

Butuh Google account sing nduweni akses channel, Python 3.12, browser ing komputer sing padha, lan JSON OAuth saka client Desktop app. Jalur Codex opsional uga butuh Node.js lan npm. Translate lan LLM Translation prompt ora butuh API key saka OpenAI utawa LLM liyane.

## Instalasi

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

## Nyetel Google OAuth

Gawe project ing Google Cloud Console lan aktifake YouTube Data API v3. Ing Google Auth Platform, gawe client **Desktop app**, download JSON, lan simpen persis ing:

~~~text
config/account_client_secrets_main.json
~~~

Nalika authorization pisanan, gunakake account sing ngatur channel lan ijinana local callback 127.0.0.1:8080. Aja nggunakake Web application client utawa API key biasa.

## Miwiti aplikasi

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Ing Windows, jalanake `..venv\Scripts\Activate.ps1` banjur prentah Streamlit sing padha. Bukak http://127.0.0.1:8501.

## Alur Translate

1. Pilih siji video ing sidebar.
2. Ing **Source languages**, tetepake basa default minangka primary source lan pilih localizations sing wis ana minangka optional references.
3. Gawe draft nganggo **Codex** utawa **External LLM**.
4. Priksa bedane nganggo **Preview changes**.
5. Gunakake **Publish changes** mung yen preview saiki isih valid.
6. Priksa asil ing YouTube Studio.

### Primary source lan referensi pilihan

Basa default iku **Primary source** sing mung bisa diwaca. Mung localizations sing wis ana sing bisa dadi **Optional reference translations**; mbusak referensi ora mbusak primary source. Yen video diganti, draft lan preview state dibusak.

## Codex

Instal lan login menyang Codex CLI lokal:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

Ing **Translate**, pilih target languages lan jalanke generation. Codex mung nggawe draft kanggo review lan ora langsung publish. Yen gagal, jalanake `codex --version` lan `codex login status` ing terminal sing padha, banjur restart Streamlit.

## External LLM

1. Klik **Prepare prompt**.
2. Tempel prompt menyang LLM njaba lan gawe UTF-8 JSON sing mung ngemot language codes sing dijaluk.
3. Ing **Upload JSON**, upload file. Uploader mung aktif yen prompt wis kaiket karo video lan target set saiki; aplikasi validasi JSON lan menehi Preview sadurunge publish.

Saben value mung oleh title lan description; title maksimal 100 lan description 5.000 karakter. Aja upload wrapper metadata, Markdown, jeneng basa, utawa duplicate keys.

## Preview changes

Preview mung maca lan ora ngundang videos.update. Laporan nuduhake added, changed, unchanged, uga localizations YouTube sing ora ana ing draft nanging bakal tetep disimpen.

## Publish changes

Publish validasi draft maneh lan njupuk video maneh sakdurunge nulis. Yen video wis owah, ora ana write. Sawise write sukses, sidebar cache dibusak lan count dijupuk maneh; no-change utawa conflict ora dituduhake minangka refresh sukses.

## Danger zone: Reset languages

**Reset languages** mung katon ing **Danger zone** sing dilipat kanggo video sing dipilih. Sawise konfirmasi, perlu ETag anyar sing valid lan digunakake conditional If-Match; localizations non-default dibusak, default metadata tetep ana. Ganti selection, ETag ilang, utawa HTTP 412 iku no-write failure tanpa automatic retry. Simpen translation sing arep dijaga dhisik.

## Ngatasi masalah lan keamanan

Yen OAuth file ora ana utawa malformed, download maneh JSON Desktop app. Yen callback gagal, terminal kudu tetep mbukak lan 127.0.0.1:8080 diijini; yen authorization kadaluwarsa, authorize maneh lan busak token.json mung yen perlu. Tindakake action ing UI kanggo quota, network, missing video, utawa error login Codex. Aja nuduhake OAuth JSON, token.json, API token, utawa output environment lengkap.

## Lisensi

Delengen [LICENSE](../../../LICENSE).
