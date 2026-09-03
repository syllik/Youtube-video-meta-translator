# YouTube Video Metadata Translator

**భాషా నావిగేషన్:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · **తెలుగు** · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## ఇది ఏమి చేస్తుంది

ఇది YouTube వీడియోల title మరియు description localization ను నిర్వహించే స్థానిక Streamlit యాప్. వీడియోను ఎంచుకుని JSON తయారు చేయండి లేదా upload చేయండి, Preview changes లో పరిశీలించి తర్వాత Publish changes చేయండి. Codex లేదా బాహ్య LLM ఫలితాలు స్వయంగా publish కావు.

## అవసరాలు

చానల్ యాక్సెస్ ఉన్న Google account, Python 3.12, అదే కంప్యూటర్‌లో browser మరియు Desktop app OAuth JSON అవసరం. ఐచ్ఛిక Codex మార్గానికి Node.js, npm కూడా కావాలి. Translate మరియు LLM Translation prompt కు OpenAI లేదా ఇతర LLM API key అవసరం లేదు.

## ఇన్‌స్టాలేషన్

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

## Google OAuth సెటప్

Google Cloud Console లో project సృష్టించి YouTube Data API v3 ను enable చేయండి. Google Auth Platform లో **Desktop app** client సృష్టించి JSON ను కచ్చితంగా ఇక్కడ ఉంచండి:

~~~text
config/account_client_secrets_main.json
~~~

మొదటి authorization లో channel నిర్వహించే account ను ఉపయోగించి local callback 127.0.0.1:8080 కు అనుమతి ఇవ్వండి. Web application client లేదా సాధారణ API key ఉపయోగించవద్దు.

## యాప్ ప్రారంభించండి

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows లో `..venv\Scripts\Activate.ps1` తర్వాత అదే Streamlit command నడపండి. http://127.0.0.1:8501 తెరవండి.

## Translate workflow

1. Sidebar లో ఒక వీడియోను ఎంచుకోండి.
2. **Source languages** లో default భాషను primary source గా ఉంచి, ఉన్న localizations ను optional references గా ఎంచుకోండి.
3. draft కోసం **Codex** లేదా **External LLM** ఉపయోగించండి.
4. **Preview changes** లో diff పరిశీలించండి.
5. ప్రస్తుత preview valid గా ఉన్నప్పుడే **Publish changes** చేయండి.
6. YouTube Studio లో ఫలితాన్ని నిర్ధారించండి.

### Primary source మరియు optional references

Default భాష read-only **Primary source**. ఉన్న localizations మాత్రమే **Optional reference translations** అవుతాయి; references clear చేసినా primary source తొలగదు. వీడియో మారితే draft మరియు preview state clear అవుతాయి.

## Codex

లోకల్ Codex CLI install చేసి login చేయండి:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** లో target languages ఎంచుకుని generation నడపండి. Codex review కోసం draft మాత్రమే తయారు చేస్తుంది, నేరుగా publish చేయదు. విఫలమైతే అదే terminal లో `codex --version` మరియు `codex login status` నడిపి Streamlit restart చేయండి.

## External LLM

1. **Prepare prompt** ఎంచుకోండి.
2. Prompt ను external LLM లో ఉపయోగించి అడిగిన language codes మాత్రమే ఉన్న UTF-8 JSON తయారు చేయండి.
3. **Upload JSON** తో file upload చేయండి. Prompt ప్రస్తుత video మరియు target set కు bound అయిన తర్వాతే uploader enable అవుతుంది; JSON validation మరియు Preview తర్వాత publish చేయవచ్చు.

ప్రతి value లో title మరియు description మాత్రమే ఉండాలి; title 100, description 5,000 characters లోపు ఉండాలి. wrapper metadata, Markdown, language names లేదా duplicate keys upload చేయవద్దు.

## Preview changes

Preview read-only మరియు videos.update ను call చేయదు. Report లో added, changed, unchanged మరియు draft లో లేని కారణంగా YouTube లో ఉంచబడే localizations కనిపిస్తాయి.

## Publish changes

Publish draft ను మళ్లీ validate చేసి write ముందు video ను మళ్లీ fetch చేస్తుంది. Video మారితే write జరగదు. విజయవంతమైన write తర్వాత sidebar cache clear చేసి count మళ్లీ fetch అవుతుంది; no-change లేదా conflict ను successful refresh గా చూపదు.

## Danger zone: Reset languages

**Reset languages** ఎంచుకున్న video యొక్క collapsed **Danger zone** లో మాత్రమే ఉంటుంది. నిర్ధారించిన తర్వాత fresh usable ETag అవసరం, conditional If-Match write జరుగుతుంది; non-default localizations తొలగి default metadata నిలుస్తుంది. selection మారడం, ETag లేకపోవడం లేదా HTTP 412 no-write failure; automatic retry లేదు. కావాల్సిన translations ముందుగా save చేయండి.

## సమస్య పరిష్కారం మరియు భద్రత

OAuth file లేకపోతే లేదా malformed అయితే కొత్త Desktop app JSON download చేయండి. callback విఫలమైతే terminal తెరిచి 127.0.0.1:8080 అనుమతించండి; authorization expire/revoke అయితే మళ్లీ authorize చేసి అవసరమైతే మాత్రమే token.json తొలగించండి. quota, network, missing video మరియు Codex login errors కు UI action ను అనుసరించండి. OAuth JSON, token.json, API token లేదా పూర్తి environment output share చేయవద్దు.

## లైసెన్స్

[LICENSE](../../../LICENSE) చూడండి.
