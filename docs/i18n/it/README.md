# YouTube Video Metadata Translator

**Navigazione linguistica:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · **Italiano** · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Cosa fa

Questa applicazione Streamlit locale gestisce titoli e descrizioni localizzati dei video YouTube. Seleziona un video, crea o carica JSON, controlla con Preview changes e poi usa Publish changes. I risultati di Codex o di un LLM esterno non vengono mai pubblicati automaticamente.

## Requisiti

Servono un Google account con accesso al canale, Python 3.12, un browser sullo stesso computer e un JSON OAuth di un client Desktop app. Il percorso Codex facoltativo richiede anche Node.js e npm. Translate e LLM Translation prompt non richiedono API key di OpenAI o di altri LLM.

## Installazione

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

## Configurare Google OAuth

In Google Cloud Console crea un project e abilita YouTube Data API v3. In Google Auth Platform crea un client **Desktop app**, scarica il JSON e salvalo esattamente in:

~~~text
config/account_client_secrets_main.json
~~~

Per la prima authorization usa l'account che gestisce il canale e consenti il local callback 127.0.0.1:8080. Non usare un Web application client o una normale API key.

## Avviare l'applicazione

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Su Windows esegui prima `..venv\Scripts\Activate.ps1`, poi lo stesso comando Streamlit. Apri http://127.0.0.1:8501.

## Flusso Translate

1. Seleziona un video nella sidebar.
2. In **Source languages** mantieni la lingua predefinita come primary source e scegli le localizations esistenti come riferimenti facoltativi.
3. Crea una bozza con **Codex** o **External LLM**.
4. Controlla le differenze con **Preview changes**.
5. Usa **Publish changes** solo se il preview corrente è ancora valido.
6. Conferma il risultato in YouTube Studio.

### Primary source e riferimenti facoltativi

La lingua predefinita è il **Primary source** in sola lettura. Solo le localizations esistenti possono essere **Optional reference translations**; cancellare i riferimenti non elimina il primary source. Cambiare video elimina bozza e preview state.

## Codex

Installa e accedi al Codex CLI locale:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

In **Translate** scegli le lingue target ed esegui la generazione. Codex crea solo una bozza da revisionare e non pubblica direttamente. Se fallisce, esegui `codex --version` e `codex login status` nello stesso terminale e riavvia Streamlit.

## External LLM

1. Premi **Prepare prompt**.
2. Incolla il prompt in un LLM esterno e crea un JSON UTF-8 con esattamente i language codes richiesti.
3. Usa **Upload JSON** per caricare il file. L'uploader si abilita solo quando il prompt è collegato al video e al target set correnti; l'app valida il JSON e consente Preview prima della pubblicazione.

Ogni value deve contenere solo title e description; title massimo 100 caratteri e description massimo 5.000. Non caricare wrapper metadata, Markdown, nomi di lingue o duplicate keys.

## Preview changes

Preview è in sola lettura e non chiama videos.update. Il report mostra added, changed e unchanged, oltre alle localizations YouTube esistenti assenti nella bozza e quindi conservate.

## Publish changes

Publish valida di nuovo la bozza e recupera il video subito prima della scrittura. Se è cambiato, non viene eseguita alcuna write. Dopo una write riuscita, la sidebar cache viene svuotata e il count ricaricato; no-change o conflict non vengono mostrati come refresh riuscito.

## Danger zone: Reset languages

**Reset languages** compare solo nella **Danger zone** chiusa del video selezionato. Dopo la conferma serve un ETag fresco e valido e viene usata una write condizionale If-Match; le localizations non predefinite vengono rimosse e i default metadata conservati. Cambio di selection, ETag assente o HTTP 412 sono errori no-write senza retry automatico. Salva prima le traduzioni da conservare.

## Risoluzione problemi e sicurezza

Se il file OAuth manca o è errato, scarica un nuovo JSON Desktop app. Se il callback fallisce, lascia aperto il terminale e consenti 127.0.0.1:8080; se l'authorization scade o viene revocata, autorizza di nuovo e elimina token.json solo se necessario. Segui l'azione mostrata nell'UI per quota, network, missing video o errori di login Codex. Non condividere OAuth JSON, token.json, API token o l'output completo dell'ambiente.

## Licenza

Vedi [LICENSE](../../../LICENSE).
