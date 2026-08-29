# YouTube Video Metadata Translator

**語言導覽：** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · **繁體中文** · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## 功能

這是一個本機 Streamlit 應用程式，用來管理 YouTube 影片標題與描述的本地化。選取影片後，可以產生或上傳 JSON，先執行 Preview changes，再安全地 Publish changes。Codex 或外部 LLM 的結果不會自動發佈。

## 需求

需要有頻道權限的 Google 帳戶、Python 3.12、同一台電腦上的瀏覽器，以及 Desktop app OAuth JSON。選用的 Codex 流程還需要 Node.js 和 npm。Translate 與 LLM Translation prompt 不需要 OpenAI 或其他 LLM API key。

## 安裝

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

## Google OAuth 設定

在 Google Cloud Console 建立專案並啟用 YouTube Data API v3。在 Google Auth Platform 建立 **Desktop app** client，下載 JSON，並準確放在：

~~~text
config/account_client_secrets_main.json
~~~

首次授權使用擁有頻道的帳戶，允許本機回呼 127.0.0.1:8080。不要使用 Web application client 或一般 API key。

## 啟動應用程式

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows PowerShell 先執行 `..venv\Scripts\Activate.ps1`。然後開啟 http://127.0.0.1:8501。

## Translate 流程

1. 在側邊欄選取一部影片。
2. 在 **Source languages** 保留預設語言作為 primary source，並可選取現有本地化作為參考。
3. 使用 **Codex** 或 **External LLM** 產生草稿。
4. 按 **Preview changes** 檢查差異。
5. 只有在目前預覽仍有效時才按 **Publish changes**。
6. 在 YouTube Studio 確認結果。

### Primary source 與可選參考

預設語言是唯讀的 **Primary source**。只有現有本地化可以成為 **Optional reference translations**；清除參考不會清除 primary source。切換影片會清除草稿與預覽狀態。

## Codex

安裝並登入本機 Codex CLI：

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

在 **Translate** 選取目標語言並執行產生。Codex 只建立待審核草稿，不會直接發佈。若失敗，請在同一終端機執行 `codex --version` 和 `codex login status`，再重新啟動 Streamlit。

## External LLM

1. 按 **Prepare prompt**。
2. 將提示詞複製到外部 LLM，產生只包含要求語言代碼的 UTF-8 JSON。
3. 用 **Upload JSON** 上傳檔案。只有當提示詞繫結目前影片與目標語言集合後，才會啟用上傳器；應用程式會先驗證 JSON 和 Preview，之後才可發佈。

每個值只能有 title 和 description；title 最多 100 個字元，description 最多 5,000 個字元。不要上傳包裝中繼資料、Markdown、語言名稱或重複鍵。

## Preview changes

Preview 是唯讀操作，不會呼叫 videos.update。報告會顯示 added、changed、unchanged，以及草稿省略但將保留的 YouTube 本地化。

## Publish changes

Publish 會再次驗證草稿並重新擷取影片。若影片已變更，不會寫入。成功寫入會清除側邊欄快取並重新擷取計數；無變更或衝突時不會顯示虛假的成功刷新。

## Danger zone：Reset languages

**Reset languages** 只會在目前選取影片的摺疊 **Danger zone** 中顯示。確認後要求最新且有效的 ETag，並以條件式 If-Match 寫入；移除所有非預設本地化並保留預設中繼資料。選取變更、缺少 ETag 或 HTTP 412 都是 no-write 失敗，不會自動重試。請先保存要保留的翻譯。

## 疑難排解與安全

OAuth 檔案遺失或格式錯誤時，依照介面提示重新下載 Desktop app JSON。回呼失敗時保持終端機開啟並允許 127.0.0.1:8080；授權過期時重新授權，只有確實需要才刪除 token.json。配額、網路、影片不存在與 Codex 登入錯誤都應依介面動作處理。不要分享 OAuth JSON、token.json、API token 或完整環境輸出。

## 授權條款

請參閱 [LICENSE](../../../LICENSE)。
