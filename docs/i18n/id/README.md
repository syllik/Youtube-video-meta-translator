# YouTube Video Metadata Translator

**Navigasi bahasa:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · **Bahasa Indonesia** · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Fungsinya

Aplikasi Streamlit lokal ini mengelola localization title dan description video YouTube. Pilih video, buat atau upload JSON, periksa dengan Preview changes, lalu gunakan Publish changes. Hasil Codex atau LLM eksternal tidak pernah dipublikasikan otomatis.

## Persyaratan

Anda memerlukan Google account dengan akses channel, Python 3.12, browser di komputer yang sama, dan JSON OAuth dari client Desktop app. Jalur Codex opsional juga memerlukan Node.js dan npm. Translate dan LLM Translation prompt tidak memerlukan OpenAI atau LLM API key lain.

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

## Menyiapkan Google OAuth

Buat project di Google Cloud Console dan aktifkan YouTube Data API v3. Di Google Auth Platform, buat client **Desktop app**, unduh JSON, lalu simpan tepat di:

~~~text
config/account_client_secrets_main.json
~~~

Untuk authorization pertama, gunakan account yang mengelola channel dan izinkan local callback 127.0.0.1:8080. Jangan gunakan Web application client atau API key biasa.

## Menjalankan aplikasi

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Di Windows, jalankan `..venv\Scripts\Activate.ps1` lalu perintah Streamlit yang sama. Buka http://127.0.0.1:8501.

## Alur Translate

1. Pilih satu video di sidebar.
2. Di **Source languages**, pertahankan bahasa default sebagai primary source dan pilih localization yang ada sebagai optional reference.
3. Buat draft dengan **Codex** atau **External LLM**.
4. Periksa perbedaan dengan **Preview changes**.
5. Gunakan **Publish changes** hanya jika preview terbaru masih valid.
6. Konfirmasi hasil di YouTube Studio.

### Primary source dan referensi opsional

Bahasa default adalah **Primary source** read-only. Hanya localization yang sudah ada yang dapat menjadi **Optional reference translations**; menghapus referensi tidak menghapus primary source. Mengganti video akan menghapus draft dan state preview.

## Codex

Instal dan login ke Codex CLI lokal:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

Di **Translate**, pilih target languages dan jalankan generation. Codex hanya membuat draft untuk ditinjau dan tidak mempublikasikan langsung. Jika gagal, jalankan `codex --version` dan `codex login status` di terminal yang sama, lalu restart Streamlit.

## External LLM

1. Klik **Prepare prompt**.
2. Tempel prompt ke LLM eksternal dan buat UTF-8 JSON yang hanya berisi language codes yang diminta.
3. Gunakan **Upload JSON** untuk mengunggah file. Uploader aktif hanya setelah prompt terikat pada video dan target set saat ini; aplikasi memvalidasi JSON dan baru mengizinkan Preview lalu Publish.

Setiap value hanya boleh memiliki title dan description; title maksimal 100 dan description 5.000 karakter. Jangan upload wrapper metadata, Markdown, nama bahasa, atau duplicate keys.

## Preview changes

Preview bersifat read-only dan tidak memanggil videos.update. Report menampilkan added, changed, unchanged, serta localization YouTube yang tidak ada di draft tetapi akan dipertahankan.

## Publish changes

Publish memvalidasi draft lagi dan mengambil video ulang sebelum menulis. Jika video berubah, tidak ada write. Setelah write berhasil, sidebar cache dihapus dan count diambil ulang; no-change atau conflict tidak ditampilkan sebagai refresh berhasil.

## Danger zone: Reset languages

**Reset languages** hanya muncul di **Danger zone** yang diciutkan untuk video terpilih. Setelah konfirmasi, diperlukan ETag baru yang valid dan conditional If-Match write; semua localization non-default dihapus, sedangkan default metadata dipertahankan. Perubahan selection, ETag yang hilang, atau HTTP 412 adalah no-write failure tanpa retry otomatis. Simpan translation yang ingin dipertahankan terlebih dahulu.

## Pemecahan masalah dan keamanan

Jika OAuth file hilang atau malformed, download ulang JSON Desktop app. Jika callback gagal, biarkan terminal terbuka dan izinkan 127.0.0.1:8080; jika authorization kedaluwarsa atau dicabut, authorize lagi dan hapus token.json hanya jika perlu. Ikuti action UI untuk quota, network, missing video, atau error login Codex. Jangan bagikan OAuth JSON, token.json, API token, atau seluruh output environment.

## Lisensi

Lihat [LICENSE](../../../LICENSE).
