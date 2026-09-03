# YouTube Video Metadata Translator

**Sprachnavigation:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · **Deutsch** · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Was macht die Anwendung?

Diese lokale Streamlit-Anwendung verwaltet lokalisierte Titel und Beschreibungen von YouTube-Videos. Video auswählen, JSON erzeugen oder hochladen, mit Preview changes prüfen und erst danach Publish changes ausführen. Ergebnisse von Codex oder einem externen LLM werden nie automatisch veröffentlicht.

## Voraussetzungen

Ein Google-Konto mit Kanalzugriff, Python 3.12, ein Browser auf demselben Computer und eine OAuth-JSON-Datei für einen Desktop app-Client. Der optionale Codex-Weg benötigt außerdem Node.js und npm. Für Translate und LLM Translation prompt ist kein OpenAI- oder anderes LLM API key nötig.

## Installation

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

## Google-OAuth einrichten

In Google Cloud Console ein Projekt erstellen und YouTube Data API v3 aktivieren. In Google Auth Platform einen **Desktop app**-Client erstellen, JSON herunterladen und exakt hier speichern:

~~~text
config/account_client_secrets_main.json
~~~

Für die erste authorization das Konto verwenden, das den Kanal verwaltet, und den lokalen callback 127.0.0.1:8080 erlauben. Keinen Web application-Client und keinen normalen API key verwenden.

## Anwendung starten

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Unter Windows zuerst `..venv\Scripts\Activate.ps1` ausführen. Dann http://127.0.0.1:8501 öffnen.

## Translate-Ablauf

1. In der Sidebar ein Video auswählen.
2. Unter **Source languages** die Standardsprache als primary source beibehalten und vorhandene localizations als optionale Referenzen auswählen.
3. Mit **Codex** oder **External LLM** einen Entwurf erstellen.
4. Die Änderungen mit **Preview changes** prüfen.
5. **Publish changes** nur bei einer aktuellen gültigen Vorschau verwenden.
6. Das Ergebnis in YouTube Studio bestätigen.

### Primary source und optionale Referenzen

Die Standardsprache ist der schreibgeschützte **Primary source**. Nur vorhandene localizations können **Optional reference translations** sein; das Löschen der Referenzen entfernt den primary source nicht. Ein Video-Wechsel löscht Entwurf und preview state.

## Codex

Lokales Codex CLI installieren und anmelden:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

In **Translate** die Zielsprachen wählen und die Erzeugung starten. Codex erstellt nur einen Entwurf zur Prüfung und veröffentlicht nicht direkt. Bei einem Fehler im selben Terminal `codex --version` und `codex login status` ausführen und Streamlit neu starten.

## External LLM

1. **Prepare prompt** auswählen.
2. Den Prompt in ein externes LLM kopieren und ein UTF-8-JSON nur mit den angeforderten language codes erzeugen.
3. Mit **Upload JSON** hochladen. Der Uploader wird erst aktiviert, wenn der Prompt an das aktuelle Video und die Zielsprachen gebunden ist; danach validiert die Anwendung das JSON und erlaubt Preview vor Publish.

Jeder Wert darf nur title und description enthalten; title höchstens 100, description höchstens 5.000 Zeichen. Keine wrapper metadata, kein Markdown, keine Sprachnamen und keine duplicate keys hochladen.

## Preview changes

Preview ist schreibgeschützt und ruft videos.update nicht auf. Der Bericht zeigt added, changed und unchanged sowie vorhandene YouTube-localizations, die im Entwurf fehlen und deshalb erhalten bleiben.

## Publish changes

Publish validiert den Entwurf erneut und ruft das Video direkt vor dem Schreiben erneut ab. Bei einer Änderung wird nicht geschrieben. Nach erfolgreichem Schreiben werden Sidebar-Cache und count aktualisiert; no-change oder conflict werden nicht als erfolgreicher Refresh angezeigt.

## Danger zone: Reset languages

**Reset languages** erscheint nur in der eingeklappten **Danger zone** des ausgewählten Videos. Nach der Bestätigung ist ein frischer gültiger ETag erforderlich und es wird bedingt mit If-Match geschrieben; nicht standardmäßige localizations werden entfernt, default metadata bleibt erhalten. Eine Auswahländerung, fehlender ETag oder HTTP 412 ist ein no-write-Fehler ohne automatischen retry. Gewünschte Übersetzungen vorher speichern.

## Fehlerbehebung und Sicherheit

Bei fehlender oder fehlerhafter OAuth-Datei eine neue Desktop app-JSON-Datei laden. Bei callback-Fehler Terminal geöffnet lassen und 127.0.0.1:8080 erlauben; bei abgelaufener authorization erneut autorisieren und token.json nur bei Bedarf löschen. Den UI-Aktionen für quota, network, missing video oder Codex-Loginfehler folgen. OAuth JSON, token.json, API tokens und vollständige Umgebungsdaten nie teilen.

## Lizenz

Siehe [LICENSE](../../../LICENSE).
