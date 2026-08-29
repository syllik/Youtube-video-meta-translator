# YouTube Video Metadata Translator

**Навигация по языкам:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · **Русский** · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Что делает приложение

Это локальное Streamlit-приложение для управления локализациями названий и описаний видео YouTube. Выберите видео, создайте или загрузите JSON, выполните Preview changes и только затем Publish changes. Результаты Codex и внешней LLM не публикуются автоматически.

## Требования

Нужны Google-аккаунт с доступом к каналу, Python 3.12, браузер на том же компьютере и OAuth JSON клиента типа Desktop app. Для необязательного пути Codex также нужны Node.js и npm. Для Translate и LLM Translation prompt не нужен API key OpenAI или другой LLM.

## Установка

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

## Настройка Google OAuth

В Google Cloud Console создайте проект и включите YouTube Data API v3. В Google Auth Platform создайте client **Desktop app** и скачайте JSON. Сохраните его точно здесь:

~~~text
config/account_client_secrets_main.json
~~~

Для первой авторизации используйте аккаунт владельца или менеджера канала и разрешите локальный callback 127.0.0.1:8080. Не используйте client Web application и обычный API key.

## Запуск приложения

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

В Windows сначала выполните `..venv\Scripts\Activate.ps1`. Откройте http://127.0.0.1:8501.

## Рабочий процесс Translate

1. Выберите видео в боковой панели.
2. В **Source languages** оставьте язык по умолчанию как primary source и при необходимости выберите существующие локализации как ссылки.
3. Создайте черновик через **Codex** или **External LLM**.
4. Нажмите **Preview changes** и проверьте diff.
5. Нажимайте **Publish changes** только для актуального корректного preview.
6. Проверьте результат в YouTube Studio.

### Primary source и необязательные ссылки

Язык по умолчанию — доступный только для чтения **Primary source**. Существующие локализации могут быть только **Optional reference translations**; удаление ссылок не удаляет primary source. При смене видео черновик и состояние preview очищаются.

## Codex

Установите и авторизуйте локальный Codex CLI:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

В **Translate** выберите целевые языки и запустите генерацию. Codex создаёт только черновик для проверки и не публикует напрямую. При ошибке выполните в том же терминале `codex --version` и `codex login status`, затем перезапустите Streamlit.

## External LLM

1. Нажмите **Prepare prompt**.
2. Передайте prompt внешней LLM и получите UTF-8 JSON ровно с запрошенными language codes.
3. В **Upload JSON** загрузите файл. Uploader включается только после привязки prompt к текущему видео и набору target languages; затем приложение проверяет JSON и допускает Preview перед публикацией.

Каждое значение должно содержать только title и description; title — не более 100, description — не более 5 000 символов. Не загружайте wrapper metadata, Markdown, названия языков или повторяющиеся ключи.

## Preview changes

Preview работает только на чтение и не вызывает videos.update. Отчёт показывает added, changed и unchanged, а также существующие локализации YouTube, пропущенные в черновике и поэтому сохраняемые.

## Publish changes

Publish повторно проверяет черновик и заново получает видео. Если оно изменилось, запись не выполняется. После успешной записи очищается кэш боковой панели и обновляется счётчик; no-change или конфликт не выдаются за успешное обновление.

## Danger zone: Reset languages

**Reset languages** находится только в свёрнутом **Danger zone** выбранного видео. После подтверждения требуется свежий корректный ETag и условная запись If-Match; удаляются все неосновные локализации, а metadata языка по умолчанию сохраняется. Изменение выбора, отсутствие ETag или HTTP 412 означают no-write без автоматического повтора. Сначала сохраните нужные переводы.

## Устранение проблем и безопасность

Если OAuth-файл отсутствует или повреждён, скачайте новый JSON клиента Desktop app. При ошибке callback оставьте терминал открытым и разрешите 127.0.0.1:8080; при истёкшей авторизации авторизуйтесь снова, удаляя token.json только при необходимости. Для quota, network, missing video и ошибок входа Codex выполните действие из сообщения приложения. Не передавайте OAuth JSON, token.json, API tokens или полный вывод окружения.

## Лицензия

См. [LICENSE](../../../LICENSE).
