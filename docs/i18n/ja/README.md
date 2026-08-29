# YouTube Video Metadata Translator

**言語ナビゲーション:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · **日本語** · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## できること

YouTube 動画のタイトルと説明のローカライズを管理するローカル Streamlit アプリです。動画を選び、JSON を生成またはアップロードし、Preview changes で確認してから Publish changes を実行します。Codex や外部 LLM の結果が自動公開されることはありません。

## 必要条件

チャンネルへのアクセス権を持つ Google アカウント、Python 3.12、同じコンピューターのブラウザー、Desktop app OAuth JSON が必要です。任意の Codex 手順には Node.js と npm も必要です。Translate と LLM Translation prompt に OpenAI などの LLM API key は不要です。

## インストール

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

## Google OAuth の設定

Google Cloud Console でプロジェクトを作成し、YouTube Data API v3 を有効にします。Google Auth Platform で **Desktop app** client を作成して JSON をダウンロードし、次の場所に正確に保存します。

~~~text
config/account_client_secrets_main.json
~~~

初回認証にはチャンネルを管理するアカウントを使い、ローカル callback 127.0.0.1:8080 を許可します。Web application client や通常の API key は使わないでください。

## アプリを起動する

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows では `..venv\Scripts\Activate.ps1` を実行してから同じコマンドを使います。http://127.0.0.1:8501 を開きます。

## Translate の流れ

1. サイドバーで動画を 1 本選択します。
2. **Source languages** で既定言語を primary source として残し、既存のローカライズを任意の参照として選びます。
3. **Codex** または **External LLM** で下書きを作成します。
4. **Preview changes** で差分を確認します。
5. 最新で有効な preview の後だけ **Publish changes** を押します。
6. YouTube Studio で結果を確認します。

### Primary source と任意の参照

既定言語は読み取り専用の **Primary source** です。既存のローカライズだけが **Optional reference translations** になり、参照をすべて解除しても primary source は解除されません。動画を変えると下書きと preview 状態が消去されます。

## Codex

ローカル Codex CLI をインストールしてログインします。

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** で対象言語を選び、生成を実行します。Codex は確認用の下書きだけを作り、直接公開しません。失敗した場合は同じターミナルで `codex --version` と `codex login status` を実行して Streamlit を再起動します。

## External LLM

1. **Prepare prompt** を押します。
2. prompt を外部 LLM に貼り付け、指定された language codes だけを含む UTF-8 JSON を生成します。
3. **Upload JSON** でファイルをアップロードします。prompt が現在の動画と target languages に結び付いたときだけ uploader が有効になり、JSON の検証と Preview の後に公開できます。

各値は title と description だけを含めます。title は 100 文字以内、description は 5,000 文字以内です。wrapper metadata、Markdown、言語名、重複キーはアップロードしないでください。

## Preview changes

Preview は読み取り専用で、videos.update を呼びません。レポートには added、changed、unchanged と、下書きにないため保持される既存の YouTube ローカライズが表示されます。

## Publish changes

Publish は下書きを再検証し、直前に動画を再取得します。動画が変更されていれば書き込みません。成功した書き込みではサイドバーのキャッシュを消去して件数を再取得します。no-change や conflict は成功した更新として表示されません。

## Danger zone: Reset languages

**Reset languages** は選択中の動画の折りたたまれた **Danger zone** にだけ表示されます。確認後は新しい有効な ETag を必須とし、条件付き If-Match で書き込みます。既定以外のローカライズを削除し、既定メタデータを保持します。選択の変更、ETag の欠落、HTTP 412 は no-write 失敗で、自動再試行はありません。必要な翻訳を先に保存してください。

## トラブルシューティングと安全性

OAuth ファイルがない、または不正な場合は Desktop app JSON を再ダウンロードします。callback に失敗したらターミナルを開いたまま 127.0.0.1:8080 を許可し、認証の期限切れや取り消しには再認証します。token.json の削除は必要な場合だけにします。quota、network、missing video、Codex のログインエラーは画面の指示に従ってください。OAuth JSON、token.json、API token、完全な環境出力を共有しないでください。

## ライセンス

[LICENSE](../../../LICENSE) を参照してください。
