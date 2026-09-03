# YouTube Video Metadata Translator

**Navegación de idiomas:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · **Español** · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Qué hace

Aplicación local de Streamlit para administrar títulos y descripciones localizadas de vídeos de YouTube. Selecciona un vídeo, genera o sube JSON, revisa con Preview changes y publica con Publish changes. Los resultados de Codex o de un LLM externo nunca se publican automáticamente.

## Requisitos

Necesitas una cuenta de Google con acceso al canal, Python 3.12, un navegador en el mismo equipo y un JSON OAuth de tipo Desktop app. La ruta opcional de Codex también requiere Node.js y npm. Translate y LLM Translation prompt no requieren una API key de OpenAI ni de otro LLM.

## Instalación

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

## Configuración de Google OAuth

En Google Cloud Console crea un proyecto y activa YouTube Data API v3. En Google Auth Platform crea un cliente **Desktop app** y descarga el JSON. Guárdalo exactamente en:

~~~text
config/account_client_secrets_main.json
~~~

Autoriza con la cuenta que administra el canal y permite el callback local 127.0.0.1:8080. No uses un cliente Web application ni una API key normal.

## Iniciar la aplicación

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

En Windows activa `..venv\Scripts\Activate.ps1` y ejecuta el mismo comando. Abre http://127.0.0.1:8501.

## Flujo de Translate

1. Selecciona un vídeo en la barra lateral.
2. En **Source languages**, conserva el idioma predeterminado como primary source y selecciona localizaciones existentes como referencias opcionales.
3. Usa **Codex** o **External LLM** para crear el borrador.
4. Pulsa **Preview changes** y revisa las diferencias.
5. Pulsa **Publish changes** solo si la vista previa actual sigue siendo válida.
6. Comprueba el resultado en YouTube Studio.

### Primary source y referencias opcionales

El idioma predeterminado es el **Primary source** de solo lectura. Las localizaciones existentes son únicamente **Optional reference translations**; borrar las referencias no borra el primary source. Al cambiar de vídeo se borran el borrador y la vista previa.

## Codex

Instala e inicia sesión en el Codex CLI local:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

En **Translate**, selecciona los idiomas de destino y genera. Codex solo crea un borrador para revisar y nunca publica directamente. Si falla, ejecuta `codex --version` y `codex login status` en la misma terminal y reinicia Streamlit.

## External LLM

1. Pulsa **Prepare prompt**.
2. Copia el prompt a un LLM externo y genera un JSON UTF-8 que contenga exactamente los códigos solicitados.
3. En **Upload JSON**, sube el archivo. El cargador se activa solo cuando el prompt está vinculado al vídeo y al conjunto de idiomas actuales; la aplicación valida el JSON y permite Preview antes de publicar.

Cada valor solo puede tener title y description; title admite 100 caracteres como máximo y description 5.000. No subas metadatos envolventes, Markdown, nombres de idiomas ni claves duplicadas.

## Preview changes

Preview es de solo lectura y no llama a videos.update. El informe muestra entradas added, changed y unchanged, además de las localizaciones de YouTube omitidas del borrador que se conservarán.

## Publish changes

Publish valida otra vez el borrador y vuelve a obtener el vídeo. Si cambió, no escribe. Tras una escritura correcta se limpia la caché de la barra lateral y se actualiza el contador; un resultado sin cambios o un conflicto no se presenta como una actualización exitosa.

## Danger zone: Reset languages

**Reset languages** solo aparece en **Danger zone**, contraída y correspondiente al vídeo seleccionado. Requiere un ETag reciente y utilizable y envía una escritura condicional If-Match; elimina localizaciones no predeterminadas y conserva los metadatos predeterminados. Un cambio de selección, ETag ausente o HTTP 412 es un fallo no-write sin reintento automático. Guarda antes las traducciones que quieras conservar.

## Solución de problemas y seguridad

Si falta o es incorrecto el OAuth, descarga de nuevo un JSON Desktop app y sigue la acción mostrada. Si falla el callback, deja abierta la terminal y permite 127.0.0.1:8080; si caduca la autorización, autoriza de nuevo y elimina token.json solo cuando sea necesario. Sigue las acciones mostradas para cuota, red, vídeo inexistente o Codex. Nunca compartas OAuth JSON, token.json, API tokens ni la salida completa del entorno.

## Licencia

Consulta [LICENSE](../../../LICENSE).
