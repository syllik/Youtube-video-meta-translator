# YouTube Video Metadata Translator

**भाषा नेव्हिगेशन:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · **मराठी** · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## हे काय करते

हे स्थानिक Streamlit अॅप YouTube व्हिडिओंची title आणि description localization व्यवस्थापित करते. व्हिडिओ निवडा, JSON तयार किंवा upload करा, Preview changes तपासा आणि मग Publish changes करा. Codex किंवा बाहेरील LLM चे परिणाम आपोआप publish होत नाहीत.

## आवश्यक गोष्टी

Channel access असलेले Google account, Python 3.12, त्याच संगणकावरील browser आणि Desktop app OAuth JSON आवश्यक आहे. Codex च्या पर्यायी मार्गासाठी Node.js आणि npm देखील आवश्यक आहेत. Translate आणि LLM Translation prompt साठी OpenAI किंवा इतर LLM API key लागत नाही.

## स्थापना

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

## Google OAuth सेटअप

Google Cloud Console मध्ये project तयार करून YouTube Data API v3 सुरू करा. Google Auth Platform मध्ये **Desktop app** client तयार करा आणि JSON येथे ठेवा:

~~~text
config/account_client_secrets_main.json
~~~

पहिल्या authorization साठी channel manage करणारे खाते वापरा आणि local callback 127.0.0.1:8080 ला परवानगी द्या. Web application client किंवा साधी API key वापरू नका.

## अॅप सुरू करा

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows मध्ये `..venv\Scripts\Activate.ps1` चालवून हीच Streamlit command वापरा. http://127.0.0.1:8501 उघडा.

## Translate workflow

1. Sidebar मध्ये एक व्हिडिओ निवडा.
2. **Source languages** मध्ये default भाषा primary source म्हणून ठेवा आणि उपलब्ध localizations optional references म्हणून निवडा.
3. **Codex** किंवा **External LLM** वापरून draft तयार करा.
4. **Preview changes** मध्ये diff तपासा.
5. चालू preview valid असेल तेव्हाच **Publish changes** करा.
6. YouTube Studio मध्ये निकाल तपासा.

### Primary source आणि optional references

Default भाषा read-only **Primary source** आहे. फक्त उपलब्ध localizations **Optional reference translations** होऊ शकतात; references clear केल्याने primary source हटत नाही. व्हिडिओ बदलल्यावर draft आणि preview state clear होते.

## Codex

स्थानिक Codex CLI install करून login करा:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** मध्ये target languages निवडून generation चालवा. Codex फक्त review साठी draft तयार करतो, थेट publish करत नाही. अपयश आल्यास त्याच terminal मध्ये `codex --version` आणि `codex login status` चालवून Streamlit restart करा.

## External LLM

1. **Prepare prompt** क्लिक करा.
2. Prompt बाहेरील LLM मध्ये देऊन फक्त मागितलेले language codes असलेला UTF-8 JSON तयार करा.
3. **Upload JSON** मधून file upload करा. Prompt सध्याच्या video आणि target set शी bound झाल्यावरच uploader सुरू होतो; JSON validation आणि Preview नंतर publish करता येते.

प्रत्येक value मध्ये फक्त title आणि description असावे; title 100 आणि description 5,000 characters पर्यंत. wrapper metadata, Markdown, language names किंवा duplicate keys upload करू नका.

## Preview changes

Preview read-only आहे आणि videos.update call करत नाही. Report मध्ये added, changed, unchanged तसेच draft मध्ये नसले तरी YouTube मध्ये राखली जाणारी localizations दिसतात.

## Publish changes

Publish draft पुन्हा validate करून write करण्याआधी video पुन्हा fetch करतो. Video बदलले असल्यास write होत नाही. यशस्वी write नंतर sidebar cache clear होऊन count पुन्हा fetch होतो; no-change किंवा conflict ला successful refresh म्हटले जात नाही.

## Danger zone: Reset languages

**Reset languages** फक्त निवडलेल्या video च्या collapsed **Danger zone** मध्ये दिसते. Confirm केल्यावर fresh usable ETag आवश्यक असून conditional If-Match write होते; non-default localizations हटतात आणि default metadata ठेवले जाते. selection बदल, ETag नसणे किंवा HTTP 412 म्हणजे no-write failure; automatic retry होत नाही. हवे असलेले translations आधी save करा.

## अडचण आणि सुरक्षा

OAuth file missing किंवा malformed असल्यास Desktop app JSON पुन्हा download करा. callback अयशस्वी झाल्यास terminal उघडे ठेवा आणि 127.0.0.1:8080 परवानगी द्या; authorization expire/revoke झाल्यास पुन्हा authorize करा आणि गरज असेल तेव्हाच token.json हटवा. quota, network, missing video किंवा Codex login errors साठी UI मधील action करा. OAuth JSON, token.json, API token किंवा पूर्ण environment output share करू नका.

## परवाना

[LICENSE](../../../LICENSE) पहा.
