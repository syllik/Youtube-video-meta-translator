# YouTube Video Metadata Translator

**راهبری زبان‌ها:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · **فارسی** · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## این برنامه چه می‌کند؟

این برنامه یک Streamlit محلی برای مدیریت بومی‌سازی title و description ویدیوهای YouTube است. ویدیو را انتخاب کنید، JSON بسازید یا بارگذاری کنید، با Preview changes بررسی کنید و سپس Publish changes را اجرا کنید. نتیجه Codex یا LLM خارجی خودکار منتشر نمی‌شود.

## نیازمندی‌ها

به Google account دارای دسترسی به کانال، Python 3.12، مرورگر همان رایانه و JSON مربوط به client از نوع Desktop app نیاز دارید. مسیر اختیاری Codex به Node.js و npm هم نیاز دارد. برای Translate و LLM Translation prompt به API key از OpenAI یا LLM دیگری نیاز نیست.

## نصب

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

## تنظیم Google OAuth

در Google Cloud Console یک project بسازید و YouTube Data API v3 را فعال کنید. در Google Auth Platform یک client از نوع **Desktop app** بسازید، JSON را دانلود کنید و دقیقاً در این مسیر قرار دهید:

~~~text
config/account_client_secrets_main.json
~~~

برای authorization اول از account مدیریت‌کننده channel استفاده کنید و local callback در 127.0.0.1:8080 را مجاز کنید. از Web application client یا API key معمولی استفاده نکنید.

## اجرای برنامه

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

در Windows ابتدا `..venv\Scripts\Activate.ps1` را اجرا کنید و سپس همان فرمان Streamlit را بزنید. http://127.0.0.1:8501 را باز کنید.

## روند Translate

1. یک ویدیو را در sidebar انتخاب کنید.
2. در **Source languages** زبان پیش‌فرض را primary source نگه دارید و localizations موجود را به‌عنوان optional references انتخاب کنید.
3. با **Codex** یا **External LLM** یک draft بسازید.
4. تفاوت‌ها را در **Preview changes** بررسی کنید.
5. فقط پس از یک preview معتبر و جدید **Publish changes** را اجرا کنید.
6. نتیجه را در YouTube Studio تأیید کنید.

### Primary source و مراجع اختیاری

زبان پیش‌فرض **Primary source** فقط‌خواندنی است. فقط localizations موجود می‌توانند **Optional reference translations** باشند؛ پاک‌کردن مراجع primary source را حذف نمی‌کند. با تغییر ویدیو draft و preview state پاک می‌شوند.

## Codex

Codex CLI محلی را نصب و login کنید:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

در **Translate** زبان‌های مقصد را انتخاب و generation را اجرا کنید. Codex فقط draft قابل بررسی می‌سازد و مستقیم publish نمی‌کند. در صورت خطا در همان terminal فرمان‌های `codex --version` و `codex login status` را اجرا کرده و Streamlit را restart کنید.

## External LLM

1. **Prepare prompt** را انتخاب کنید.
2. prompt را در LLM خارجی قرار دهید و UTF-8 JSON شامل دقیقاً language codes درخواست‌شده بسازید.
3. با **Upload JSON** فایل را بارگذاری کنید. uploader فقط وقتی فعال می‌شود که prompt به ویدیوی فعلی و target set متصل باشد؛ برنامه JSON را اعتبارسنجی می‌کند و بعد Preview را ممکن می‌سازد.

هر value فقط باید title و description داشته باشد؛ title حداکثر 100 و description حداکثر 5,000 کاراکتر. wrapper metadata، Markdown، نام زبان‌ها یا duplicate keys را بارگذاری نکنید.

## Preview changes

Preview فقط خواندنی است و videos.update را صدا نمی‌زند. گزارش added، changed، unchanged و localizations موجود YouTube را که در draft نیستند اما حفظ می‌شوند نشان می‌دهد.

## Publish changes

Publish draft را دوباره validate می‌کند و درست پیش از write ویدیو را دوباره می‌گیرد. اگر ویدیو تغییر کرده باشد write انجام نمی‌شود. پس از write موفق، sidebar cache پاک و count دوباره دریافت می‌شود؛ no-change یا conflict به‌عنوان refresh موفق نشان داده نمی‌شود.

## Danger zone: Reset languages

**Reset languages** فقط در **Danger zone** بازشونده ویدیوی انتخاب‌شده دیده می‌شود. پس از تأیید، ETag تازه و معتبر لازم است و write مشروط If-Match انجام می‌شود؛ localizations غیرپیش‌فرض حذف و default metadata حفظ می‌شود. تغییر selection، نبودن ETag یا HTTP 412 خطای no-write بدون automatic retry است. ترجمه‌های مهم را اول ذخیره کنید.

## رفع مشکل و امنیت

اگر OAuth file گم شده یا malformed است، JSON جدید Desktop app را دانلود کنید. اگر callback شکست خورد terminal را باز نگه دارید و 127.0.0.1:8080 را مجاز کنید؛ اگر authorization منقضی یا لغو شد دوباره authorize کنید و token.json را فقط در صورت نیاز حذف کنید. برای quota، network، missing video و خطای login Codex، action نمایش‌داده‌شده در UI را انجام دهید. OAuth JSON، token.json، API token یا خروجی کامل environment را به اشتراک نگذارید.

## مجوز

[LICENSE](../../../LICENSE) را ببینید.
