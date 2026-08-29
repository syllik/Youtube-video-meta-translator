# YouTube Video Metadata Translator

**Navegação de idiomas:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · **Português (Brasil)** · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## O que faz

Aplicativo local em Streamlit para administrar títulos e descrições localizados de vídeos do YouTube. Selecione um vídeo, gere ou envie JSON, revise em Preview changes e publique em Publish changes. Resultados do Codex ou de um LLM externo nunca são publicados automaticamente.

## Requisitos

Você precisa de uma conta Google com acesso ao canal, Python 3.12, navegador no mesmo computador e JSON OAuth de um cliente Desktop app. O caminho opcional do Codex também requer Node.js e npm. Translate e LLM Translation prompt não exigem API key da OpenAI ou de outro LLM.

## Instalação

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

## Configuração do Google OAuth

No Google Cloud Console, crie um projeto e ative a YouTube Data API v3. No Google Auth Platform, crie um cliente **Desktop app** e baixe o JSON. Salve-o exatamente em:

~~~text
config/account_client_secrets_main.json
~~~

Autorize com a conta que administra o canal e permita o callback local 127.0.0.1:8080. Não use cliente Web application nem uma API key comum.

## Iniciar o aplicativo

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

No Windows, ative `..venv\Scripts\Activate.ps1` e execute o mesmo comando. Abra http://127.0.0.1:8501.

## Fluxo do Translate

1. Selecione um vídeo na barra lateral.
2. Em **Source languages**, mantenha o idioma padrão como primary source e selecione localizações existentes como referências opcionais.
3. Use **Codex** ou **External LLM** para criar o rascunho.
4. Clique em **Preview changes** e revise o diff.
5. Clique em **Publish changes** somente se o preview atual ainda for válido.
6. Confirme o resultado no YouTube Studio.

### Primary source e referências opcionais

O idioma padrão é o **Primary source** somente para leitura. Localizações existentes são apenas **Optional reference translations**; limpar referências não remove o primary source. Trocar de vídeo limpa o rascunho e o estado do preview.

## Codex

Instale e faça login no Codex CLI local:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

No **Translate**, selecione os idiomas de destino e gere. O Codex cria apenas um rascunho para revisão e nunca publica diretamente. Se falhar, execute `codex --version` e `codex login status` no mesmo terminal e reinicie o Streamlit.

## External LLM

1. Clique em **Prepare prompt**.
2. Cole o prompt em um LLM externo e gere um JSON UTF-8 contendo exatamente os códigos solicitados.
3. Em **Upload JSON**, envie o arquivo. O uploader só é habilitado quando o prompt está vinculado ao vídeo e ao conjunto de idiomas atual; o app valida o JSON e permite Preview antes do Publish.

Cada valor pode conter apenas title e description; title tem no máximo 100 caracteres e description 5.000. Não envie metadados de wrapper, Markdown, nomes de idiomas ou chaves duplicadas.

## Preview changes

Preview é somente leitura e não chama videos.update. O relatório mostra entradas added, changed e unchanged, além das localizações existentes omitidas do rascunho que serão preservadas.

## Publish changes

Publish valida novamente o rascunho e busca o vídeo outra vez. Se ele mudou, nada é escrito. Uma escrita bem-sucedida limpa o cache da barra lateral e atualiza a contagem; no-change ou conflito não aparece como atualização bem-sucedida.

## Danger zone: Reset languages

**Reset languages** aparece apenas na **Danger zone** recolhida do vídeo selecionado. Após a confirmação, exige ETag recente e utilizável e envia uma gravação condicional If-Match; remove localizações não padrão e preserva os metadados padrão. Mudança de seleção, ETag ausente ou HTTP 412 é falha no-write sem retry automático. Salve antes as traduções que deseja manter.

## Solução de problemas e segurança

Se o OAuth estiver ausente ou inválido, baixe novamente um JSON Desktop app e siga a ação exibida. Se o callback falhar, mantenha o terminal aberto e permita 127.0.0.1:8080; se a autorização expirar, autorize de novo e remova token.json apenas quando necessário. Siga as ações da interface para quota, rede, vídeo ausente ou Codex. Nunca compartilhe OAuth JSON, token.json, API tokens ou a saída completa do ambiente.

## Licença

Consulte [LICENSE](../../../LICENSE).
