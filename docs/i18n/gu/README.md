# YouTube Video Metadata Translator

**ભાષા નેવિગેશન:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · **ગુજરાતી** · [भोजपुरी](../bho/README.md)

## આ શું કરે છે?

આ સ્થાનિક Streamlit એપ YouTube વિડિઓના title અને description localization સંભાળે છે. વિડિઓ પસંદ કરો, JSON બનાવો અથવા upload કરો, Preview changesથી તપાસો અને પછી Publish changes કરો. Codex અથવા બહારના LLMનું પરિણામ આપમેળે publish થતું નથી.

## જરૂરી વસ્તુઓ

Channel access ધરાવતું Google account, Python 3.12, એ જ કમ્પ્યુટરનું browser અને Desktop app clientનું OAuth JSON જરૂરી છે. વૈકલ્પિક Codex માર્ગ માટે Node.js અને npm પણ જરૂરી છે. Translate અને LLM Translation prompt માટે OpenAI કે અન્ય LLM API key જરૂરી નથી.

## ઇન્સ્ટોલેશન

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

## Google OAuth સેટઅપ

Google Cloud Consoleમાં project બનાવી YouTube Data API v3 સક્ષમ કરો. Google Auth Platformમાં **Desktop app** client બનાવો, JSON download કરો અને ચોક્કસ અહીં મૂકો:

~~~text
config/account_client_secrets_main.json
~~~

પ્રથમ authorization માટે channel ચલાવતા accountનો ઉપયોગ કરો અને local callback 127.0.0.1:8080ને મંજૂરી આપો. Web application client અથવા સામાન્ય API key ઉપયોગ ન કરો.

## એપ શરૂ કરો

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windowsમાં `..venv\Scripts\Activate.ps1` ચલાવીને એ જ Streamlit command વાપરો. http://127.0.0.1:8501 ખોલો.

## Translate workflow

1. Sidebarમાં એક વિડિઓ પસંદ કરો.
2. **Source languages**માં default ભાષાને primary source રાખો અને ઉપલબ્ધ localizationsને optional references તરીકે પસંદ કરો.
3. **Codex** અથવા **External LLM**થી draft બનાવો.
4. **Preview changes**માં diff તપાસો.
5. હાલનું preview valid હોય ત્યારે જ **Publish changes** કરો.
6. YouTube Studioમાં પરિણામ તપાસો.

### Primary source અને optional references

Default ભાષા read-only **Primary source** છે. ઉપલબ્ધ localizations જ **Optional reference translations** બની શકે; references દૂર કરવાથી primary source દૂર થતો નથી. વિડિઓ બદલવાથી draft અને preview state સાફ થાય છે.

## Codex

સ્થાનિક Codex CLI install અને login કરો:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate**માં target languages પસંદ કરી generation ચલાવો. Codex માત્ર review માટે draft બનાવે છે અને સીધું publish કરતું નથી. નિષ્ફળતા હોય તો એ જ terminalમાં `codex --version` અને `codex login status` ચલાવી Streamlit restart કરો.

## External LLM

1. **Prepare prompt** દબાવો.
2. Promptને બહારના LLMમાં આપીને માત્ર માંગેલા language codes ધરાવતું UTF-8 JSON બનાવો.
3. **Upload JSON**થી file upload કરો. Prompt હાલના વિડિઓ અને target set સાથે bound થયા પછી જ uploader ચાલુ થાય છે; app JSON validate કરી Preview પછી publish કરવાની મંજૂરી આપે છે.

દરેક valueમાં title અને description જ હોવા જોઈએ; title 100 અને description 5,000 characters સુધી. wrapper metadata, Markdown, language names અથવા duplicate keys upload ન કરો.

## Preview changes

Preview read-only છે અને videos.update call કરતું નથી. Reportમાં added, changed, unchanged તથા draftમાં ન હોવા છતાં YouTubeમાં જળવાતી localizations દેખાય છે.

## Publish changes

Publish draftને ફરી validate કરે છે અને write પહેલાં વિડિઓ ફરી fetch કરે છે. વિડિઓ બદલાઈ હોય તો write થતું નથી. સફળ write પછી sidebar cache clear થઈ count ફરી fetch થાય છે; no-change અથવા conflictને સફળ refresh તરીકે દર્શાવવામાં આવતું નથી.

## Danger zone: Reset languages

**Reset languages** પસંદ કરેલા વિડિઓની collapsed **Danger zone**માં જ દેખાય છે. Confirm પછી fresh usable ETag જરૂરી છે અને conditional If-Match write થાય છે; non-default localizations દૂર થાય છે, default metadata રહે છે. selection બદલાય, ETag ન મળે અથવા HTTP 412 આવે તો no-write failure છે અને automatic retry નથી. રાખવાના translations પહેલાં save કરો.

## સમસ્યા અને સુરક્ષા

OAuth file missing અથવા malformed હોય તો નવું Desktop app JSON download કરો. callback નિષ્ફળ જાય તો terminal ખુલ્લું રાખી 127.0.0.1:8080ને મંજૂરી આપો; authorization expire/revoke થાય તો ફરી authorize કરો અને જરૂર હોય ત્યારે જ token.json કાઢો. quota, network, missing video અથવા Codex login errors માટે UIનું action કરો. OAuth JSON, token.json, API token કે સંપૂર્ણ environment output શેર ન કરો.

## લાઇસન્સ

[LICENSE](../../../LICENSE) જુઓ.
