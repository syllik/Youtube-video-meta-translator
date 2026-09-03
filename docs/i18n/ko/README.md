# YouTube Video Metadata Translator

**언어 탐색:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · **한국어** · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## 무엇을 하나요?

YouTube 동영상의 title과 description localization을 관리하는 로컬 Streamlit 앱입니다. 동영상을 선택하고 JSON을 생성하거나 업로드한 뒤 Preview changes로 확인하고 Publish changes를 실행합니다. Codex 또는 외부 LLM의 결과는 자동으로 게시되지 않습니다.

## 요구 사항

채널 권한이 있는 Google account, Python 3.12, 같은 컴퓨터의 browser, Desktop app OAuth JSON이 필요합니다. 선택 사항인 Codex 경로에는 Node.js와 npm도 필요합니다. Translate와 LLM Translation prompt에는 OpenAI 또는 다른 LLM API key가 필요하지 않습니다.

## 설치

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

## Google OAuth 설정

Google Cloud Console에서 project를 만들고 YouTube Data API v3를 활성화합니다. Google Auth Platform에서 **Desktop app** client를 만든 뒤 JSON을 다음 위치에 정확히 저장합니다.

~~~text
config/account_client_secrets_main.json
~~~

처음 authorization에는 채널을 관리하는 account를 사용하고 local callback 127.0.0.1:8080을 허용합니다. Web application client나 일반 API key를 사용하지 마세요.

## 앱 시작

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows에서는 `..venv\Scripts\Activate.ps1` 실행 후 같은 Streamlit 명령을 사용합니다. http://127.0.0.1:8501을 엽니다.

## Translate workflow

1. Sidebar에서 동영상 하나를 선택합니다.
2. **Source languages**에서 default 언어를 primary source로 유지하고 기존 localizations를 optional references로 선택합니다.
3. **Codex** 또는 **External LLM**으로 draft를 만듭니다.
4. **Preview changes**에서 diff를 검토합니다.
5. 현재 preview가 유효할 때만 **Publish changes**를 누릅니다.
6. YouTube Studio에서 결과를 확인합니다.

### Primary source와 optional references

Default 언어는 읽기 전용 **Primary source**입니다. 기존 localizations만 **Optional reference translations**가 될 수 있으며 references를 지워도 primary source는 지워지지 않습니다. 동영상을 바꾸면 draft와 preview state가 지워집니다.

## Codex

로컬 Codex CLI를 설치하고 로그인합니다.

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate**에서 target languages를 선택하고 generation을 실행합니다. Codex는 검토용 draft만 만들며 직접 publish하지 않습니다. 실패하면 같은 terminal에서 `codex --version`과 `codex login status`를 실행하고 Streamlit을 다시 시작합니다.

## External LLM

1. **Prepare prompt**를 누릅니다.
2. Prompt를 외부 LLM에 넣고 요청한 language codes만 포함한 UTF-8 JSON을 만듭니다.
3. **Upload JSON**으로 파일을 올립니다. Prompt가 현재 video와 target set에 연결된 뒤에만 uploader가 활성화되며, 앱은 JSON을 검증하고 Preview 후 publish를 허용합니다.

각 value에는 title과 description만 포함해야 합니다. title은 100자, description은 5,000자 이하여야 합니다. wrapper metadata, Markdown, 언어 이름 또는 duplicate keys를 업로드하지 마세요.

## Preview changes

Preview는 읽기 전용이며 videos.update를 호출하지 않습니다. Report에는 added, changed, unchanged와 draft에서 빠졌지만 YouTube에 보존되는 localizations가 표시됩니다.

## Publish changes

Publish는 draft를 다시 검증하고 쓰기 직전에 video를 다시 가져옵니다. video가 변경되면 write하지 않습니다. 성공한 write 후 sidebar cache가 지워지고 count가 다시 로드되며, no-change나 conflict를 성공적인 refresh로 표시하지 않습니다.

## Danger zone: Reset languages

**Reset languages**는 선택된 video의 접힌 **Danger zone**에만 나타납니다. 확인 후 사용 가능한 최신 ETag가 필요하며 조건부 If-Match write를 사용합니다. 기본값이 아닌 localizations를 제거하고 default metadata를 보존합니다. selection 변경, ETag 누락 또는 HTTP 412는 no-write 실패이며 자동 retry가 없습니다. 보존할 번역은 먼저 저장하세요.

## 문제 해결과 보안

OAuth file이 없거나 잘못되었으면 새 Desktop app JSON을 다운로드하세요. callback이 실패하면 terminal을 열어 두고 127.0.0.1:8080을 허용합니다. authorization이 만료되거나 취소되면 다시 authorize하고 token.json은 필요한 경우에만 삭제합니다. quota, network, missing video 또는 Codex login 오류에서는 UI의 안내를 따르세요. OAuth JSON, token.json, API token 또는 전체 환경 출력을 공유하지 마세요.

## 라이선스

[LICENSE](../../../LICENSE)를 참조하세요.
