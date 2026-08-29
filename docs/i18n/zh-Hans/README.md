# YouTube Video Metadata Translator

**语言导航：** [English](../../../README.md) · **简体中文** · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## 功能

这是一个本地 Streamlit 应用，用于管理 YouTube 视频的标题和描述本地化。选择视频后，你可以生成或上传 JSON，先 Preview changes，再安全地 Publish changes。应用不会自动发布 Codex 或外部 LLM 的结果。

## 要求

需要有频道权限的 Google 账号、Python 3.12、同一台电脑上的浏览器，以及 Desktop app OAuth JSON。可选的 Codex 路径还需要 Node.js 和 npm。Translate 和 LLM Translation prompt 不需要 OpenAI 或其他 LLM API key。

## 安装

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

## Google OAuth 设置

在 Google Cloud Console 中创建项目，启用 YouTube Data API v3，在 Google Auth Platform 中创建 **Desktop app** client，并下载 JSON。把文件准确保存为：

~~~text
config/account_client_secrets_main.json
~~~

首次授权时使用频道所属账号。允许本地回调 127.0.0.1:8080。不要使用 Web application client 或普通 API key。

## 启动应用

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows PowerShell 使用 `..venv\Scripts\Activate.ps1` 后执行同一条 Streamlit 命令。打开 http://127.0.0.1:8501。

## Translate 工作流

1. 在侧边栏选择一个视频。
2. 在 **Source languages** 中保留默认语言作为 primary source，并选择已有本地化作为可选参考。
3. 使用 **Codex** 或 **External LLM** 生成草稿。
4. 点击 **Preview changes** 检查差异。
5. 只在预览仍然有效时点击 **Publish changes**。
6. 确认 YouTube Studio 中的结果。

### Primary source 和可选参考

默认语言是只读的 **Primary source**。已有本地化只能作为 **Optional reference translations**；清空参考不会清除 primary source。切换视频会清空草稿和预览状态。

## Codex

安装并登录本地 Codex CLI：

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

在 **Translate** 中选择目标语言并运行生成。Codex 只生成供审核的草稿，从不直接发布。若失败，请在同一终端运行 `codex --version` 和 `codex login status`，然后重启 Streamlit。

## External LLM

1. 点击 **Prepare prompt**。
2. 将提示词复制到外部 LLM，生成只包含请求语言代码的 UTF-8 JSON。
3. 在 **Upload JSON** 上传文件。上传器只在提示词绑定当前视频和目标语言集合后启用；应用会校验 JSON、Preview，然后才允许发布。

每个值只能有 title 和 description；title 最多 100 个字符，description 最多 5,000 个字符。不要上传包装元数据、Markdown、语言名称或重复键。

## Preview changes

Preview 是只读操作，不调用 videos.update。报告会显示 added、changed、unchanged，并说明草稿中省略但将被保留的 YouTube 本地化。

## Publish changes

Publish 会再次校验草稿并重新获取视频。若视频已变化，不会写入。成功写入时会清除侧边栏缓存并重新获取计数；无变化或冲突时不会冒充成功刷新。

## Danger zone：Reset languages

**Reset languages** 只在当前选中视频的折叠 **Danger zone** 中显示。确认后应用要求最新且可用的 ETag，并使用条件 If-Match 写入；移除所有非默认本地化，同时保留默认元数据。选择变化、缺少 ETag 或 HTTP 412 都是 no-write 失败，不会自动重试。请先保存需要保留的翻译。

## 故障排查与安全

缺少或格式错误的 OAuth 文件时，按界面提示重新下载 Desktop app JSON。回调失败时保持终端打开并允许 127.0.0.1:8080；授权过期时重新授权，只有确实需要时才删除 token.json。配额、网络、视频不存在和 Codex 登录错误都应按界面提供的动作处理。不要分享 OAuth JSON、token.json、API token 或完整环境输出。

## 许可证

请参阅 [LICENSE](../../../LICENSE)。
