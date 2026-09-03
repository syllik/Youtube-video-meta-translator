# YouTube Video Metadata Translator

**Navigation des langues :** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · **Français** · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Fonctionnement

Cette application Streamlit locale gère les titres et descriptions localisés des vidéos YouTube. Sélectionnez une vidéo, créez ou importez un JSON, vérifiez avec Preview changes, puis utilisez Publish changes. Les résultats de Codex ou d'un LLM externe ne sont jamais publiés automatiquement.

## Prérequis

Il faut un compte Google ayant accès à la chaîne, Python 3.12, un navigateur sur le même ordinateur et un JSON OAuth d'un client Desktop app. Le parcours Codex facultatif nécessite aussi Node.js et npm. Translate et LLM Translation prompt ne nécessitent aucune API key OpenAI ou autre LLM.

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

## Configurer Google OAuth

Dans Google Cloud Console, créez un projet et activez YouTube Data API v3. Dans Google Auth Platform, créez un client **Desktop app**, téléchargez son JSON et enregistrez-le exactement ici :

~~~text
config/account_client_secrets_main.json
~~~

Pour la première authorization, utilisez le compte qui gère la chaîne et autorisez le callback local 127.0.0.1:8080. N'utilisez pas de client Web application ni d'API key ordinaire.

## Démarrer l'application

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Sous Windows, lancez `..venv\Scripts\Activate.ps1` puis la même commande Streamlit. Ouvrez http://127.0.0.1:8501.

## Flux Translate

1. Sélectionnez une vidéo dans la barre latérale.
2. Dans **Source languages**, gardez la langue par défaut comme primary source et choisissez les localizations existantes comme références facultatives.
3. Créez un brouillon avec **Codex** ou **External LLM**.
4. Vérifiez les différences avec **Preview changes**.
5. Utilisez **Publish changes** seulement si le preview actuel est valide.
6. Confirmez le résultat dans YouTube Studio.

### Primary source et références facultatives

La langue par défaut est le **Primary source** en lecture seule. Seules les localizations existantes peuvent être des **Optional reference translations** ; effacer les références ne supprime pas le primary source. Changer de vidéo efface le brouillon et l'état du preview.

## Codex

Installez et connectez-vous au Codex CLI local :

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

Dans **Translate**, choisissez les langues cibles et lancez la génération. Codex crée uniquement un brouillon à vérifier et ne publie pas directement. En cas d'échec, exécutez `codex --version` et `codex login status` dans le même terminal puis redémarrez Streamlit.

## External LLM

1. Cliquez sur **Prepare prompt**.
2. Collez le prompt dans un LLM externe et créez un JSON UTF-8 contenant exactement les language codes demandés.
3. Avec **Upload JSON**, importez le fichier. L'uploader ne s'active que lorsque le prompt est lié à la vidéo et aux target languages actuels ; l'application valide le JSON et permet Preview avant la publication.

Chaque valeur doit contenir seulement title et description ; title est limité à 100 caractères et description à 5 000. N'importez ni wrapper metadata, ni Markdown, ni noms de langues, ni duplicate keys.

## Preview changes

Preview est en lecture seule et n'appelle pas videos.update. Le rapport affiche added, changed, unchanged ainsi que les localizations YouTube existantes absentes du brouillon et donc conservées.

## Publish changes

Publish revalide le brouillon et récupère la vidéo juste avant l'écriture. Si elle a changé, aucune écriture n'est faite. Après une écriture réussie, le cache de la barre latérale est effacé et le count est rechargé ; no-change ou conflict n'est pas présenté comme un refresh réussi.

## Danger zone : Reset languages

**Reset languages** apparaît uniquement dans la **Danger zone** repliée de la vidéo sélectionnée. Après confirmation, un ETag récent et valide est requis et l'écriture conditionnelle If-Match est utilisée ; les localizations non par défaut sont supprimées et les default metadata sont conservées. Un changement de sélection, l'absence d'ETag ou HTTP 412 est une erreur no-write sans retry automatique. Enregistrez d'abord les traductions à conserver.

## Dépannage et sécurité

Si le fichier OAuth est absent ou incorrect, téléchargez un nouveau JSON Desktop app. En cas d'échec du callback, gardez le terminal ouvert et autorisez 127.0.0.1:8080 ; si l'authorization expire ou est révoquée, recommencez et ne supprimez token.json qu'en cas de besoin. Suivez les actions affichées pour quota, network, missing video ou connexion Codex. Ne partagez jamais OAuth JSON, token.json, API token ou la sortie complète de l'environnement.

## Licence

Voir [LICENSE](../../../LICENSE).
