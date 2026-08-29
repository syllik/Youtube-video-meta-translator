# YouTube Video Metadata Translator

**التنقل بين اللغات:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · **العربية** · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## ماذا يفعل؟

هذا تطبيق Streamlit محلي لإدارة تعريب عناوين فيديوهات YouTube ووصفها. اختر فيديو، وأنشئ JSON أو ارفعه، وافحصه عبر Preview changes ثم نفّذ Publish changes. لا ينشر التطبيق نتائج Codex أو أي LLM خارجي تلقائياً.

## المتطلبات

تحتاج إلى حساب Google لديه صلاحية على القناة، وPython 3.12، ومتصفح على الكمبيوتر نفسه، وملف OAuth بصيغة عميل Desktop app. يتطلب مسار Codex الاختياري أيضاً Node.js وnpm. لا تحتاج Translate وLLM Translation prompt إلى API key لـ OpenAI أو لأي LLM آخر.

## التثبيت

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

## إعداد Google OAuth

أنشئ مشروعاً في Google Cloud Console وفعّل YouTube Data API v3. في Google Auth Platform أنشئ عميلاً من نوع **Desktop app** ونزّل JSON، ثم احفظه بالضبط في:

~~~text
config/account_client_secrets_main.json
~~~

استخدم في التفويض الأول الحساب الذي يدير القناة واسمح بـ local callback على 127.0.0.1:8080. لا تستخدم Web application client أو API key عادية.

## تشغيل التطبيق

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

في Windows شغّل `..venv\Scripts\Activate.ps1` ثم نفّذ أمر Streamlit نفسه. افتح http://127.0.0.1:8501.

## سير عمل Translate

1. اختر فيديو واحداً من الشريط الجانبي.
2. في **Source languages** أبقِ اللغة الافتراضية primary source، ويمكنك اختيار localizations موجودة كمراجع اختيارية.
3. أنشئ مسودة باستخدام **Codex** أو **External LLM**.
4. افحص الفرق عبر **Preview changes**.
5. استخدم **Publish changes** فقط إذا بقيت المعاينة الحالية صالحة.
6. تحقق من النتيجة في YouTube Studio.

### Primary source والمراجع الاختيارية

اللغة الافتراضية هي **Primary source** للقراءة فقط. لا يمكن أن تكون **Optional reference translations** إلا localizations الموجودة؛ مسح المراجع لا يمسح primary source. يؤدي تغيير الفيديو إلى مسح المسودة وحالة المعاينة.

## Codex

ثبّت وسجّل الدخول إلى Codex CLI المحلي:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

في **Translate** اختر اللغات المستهدفة وشغّل التوليد. ينشئ Codex مسودة للمراجعة فقط ولا ينشر مباشرة. عند الفشل شغّل `codex --version` و`codex login status` في الطرفية نفسها ثم أعد تشغيل Streamlit.

## External LLM

1. اضغط **Prepare prompt**.
2. الصق prompt في LLM خارجي وأنشئ UTF-8 JSON يحتوي فقط على language codes المطلوبة.
3. استخدم **Upload JSON** لرفع الملف. لا يتفعّل uploader إلا بعد ربط prompt بالفيديو الحالي ومجموعة target languages؛ يتحقق التطبيق من JSON ويسمح بـ Preview قبل النشر.

يجب أن تحتوي كل قيمة على title وdescription فقط؛ الحد الأقصى لـ title هو 100 حرف ولـ description هو 5,000 حرف. لا ترفع wrapper metadata أو Markdown أو أسماء اللغات أو duplicate keys.

## Preview changes

Preview للقراءة فقط ولا يستدعي videos.update. يعرض التقرير entries من نوع added وchanged وunchanged، إضافة إلى localizations الموجودة في YouTube التي لم تدخل المسودة ولذلك ستبقى محفوظة.

## Publish changes

يعيد Publish التحقق من المسودة ويجلب الفيديو قبل الكتابة مباشرة. إذا تغيّر الفيديو فلن تحدث كتابة. بعد الكتابة الناجحة يُمسح sidebar cache ويُعاد جلب count؛ لا يُعرض no-change أو conflict كتحديث ناجح.

## Danger zone: Reset languages

يظهر **Reset languages** فقط داخل **Danger zone** المطوي للفيديو المحدد. بعد التأكيد يتطلب ETag جديداً صالحاً ويرسل كتابة مشروطة بـ If-Match؛ يزيل كل localizations غير الافتراضية ويحافظ على metadata الافتراضية. تغيير التحديد أو غياب ETag أو HTTP 412 يعني no-write بلا إعادة محاولة تلقائية. احفظ الترجمات التي تريد الاحتفاظ بها أولاً.

## استكشاف الأخطاء والأمان

إذا كان ملف OAuth مفقوداً أو غير صالح فنزّل JSON جديداً من نوع Desktop app. عند فشل callback اترك الطرفية مفتوحة واسمح بـ 127.0.0.1:8080؛ وعند انتهاء التفويض أعد التفويض واحذف token.json فقط عند الحاجة. اتبع الإجراء الظاهر في التطبيق لأخطاء quota أو network أو missing video أو تسجيل دخول Codex. لا تشارك OAuth JSON أو token.json أو API tokens أو مخرجات البيئة الكاملة.

## الترخيص

راجع [LICENSE](../../../LICENSE).
