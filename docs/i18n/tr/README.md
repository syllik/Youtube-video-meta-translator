# YouTube Video Metadata Translator

**Dil gezintisi:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · **Türkçe** · [Tiếng Việt](../vi/README.md) · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Ne yapar?

YouTube videolarının başlık ve açıklama yerelleştirmelerini yönetmek için yerel bir Streamlit uygulamasıdır. Bir video seçin, JSON üretin veya yükleyin, Preview changes ile inceleyin ve ardından Publish changes kullanın. Codex ya da harici LLM çıktısı otomatik yayımlanmaz.

## Gereksinimler

Kanal erişimi olan bir Google hesabı, Python 3.12, aynı bilgisayarda bir tarayıcı ve Desktop app OAuth JSON gerekir. İsteğe bağlı Codex yolu Node.js ve npm de ister. Translate ve LLM Translation prompt için OpenAI veya başka bir LLM API key gerekmez.

## Kurulum

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

## Google OAuth ayarı

Google Cloud Console'da bir proje oluşturup YouTube Data API v3'ü etkinleştirin. Google Auth Platform'da bir **Desktop app** client oluşturun ve JSON'u tam olarak şuraya kaydedin:

~~~text
config/account_client_secrets_main.json
~~~

İlk yetkilendirmede kanalı yöneten hesabı kullanın ve yerel callback 127.0.0.1:8080 erişimine izin verin. Web application client veya sıradan API key kullanmayın.

## Uygulamayı başlatma

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Windows'ta `..venv\Scripts\Activate.ps1` çalıştırdıktan sonra aynı Streamlit komutunu kullanın. http://127.0.0.1:8501 adresini açın.

## Translate akışı

1. Kenar çubuğunda bir video seçin.
2. **Source languages** içinde varsayılan dili primary source olarak bırakın; mevcut yerelleştirmeleri isteğe bağlı referans olarak seçin.
3. Taslak oluşturmak için **Codex** veya **External LLM** kullanın.
4. Farkları **Preview changes** ile inceleyin.
5. Yalnızca güncel ve geçerli preview sonrasında **Publish changes** yapın.
6. Sonucu YouTube Studio'da doğrulayın.

### Primary source ve isteğe bağlı referanslar

Varsayılan dil salt okunur **Primary source**'tur. Yalnızca mevcut yerelleştirmeler **Optional reference translations** olabilir; referansları temizlemek primary source'u kaldırmaz. Video değişince taslak ve preview durumu temizlenir.

## Codex

Yerel Codex CLI'yi kurup giriş yapın:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

**Translate** içinde hedef dilleri seçip üretimi çalıştırın. Codex yalnızca incelenecek taslak üretir, doğrudan yayımlamaz. Başarısız olursa aynı terminalde `codex --version` ve `codex login status` çalıştırıp Streamlit'i yeniden başlatın.

## External LLM

1. **Prepare prompt** düğmesine basın.
2. Prompt'u harici LLM'ye verip yalnızca istenen language codes içeren UTF-8 JSON üretin.
3. **Upload JSON** ile dosyayı yükleyin. Uploader ancak prompt mevcut video ve target languages kümesine bağlandığında etkinleşir; uygulama JSON'u doğrular ve Publish öncesi Preview yapılmasını ister.

Her değer yalnızca title ve description içermelidir; title en fazla 100, description 5.000 karakter olabilir. Wrapper metadata, Markdown, dil adları veya duplicate keys yüklemeyin.

## Preview changes

Preview salt okunurdur ve videos.update çağırmaz. Rapor added, changed, unchanged girişlerini ve taslakta bulunmadığı için korunacak YouTube yerelleştirmelerini gösterir.

## Publish changes

Publish taslağı yeniden doğrular ve videoyu yazmadan hemen önce tekrar alır. Video değişmişse yazma yapılmaz. Başarılı yazmada kenar çubuğu cache'i temizlenir ve count yeniden alınır; no-change veya conflict başarılı yenileme gibi gösterilmez.

## Danger zone: Reset languages

**Reset languages** yalnızca seçili videonun daraltılmış **Danger zone** bölümünde görünür. Onaydan sonra kullanılabilir taze ETag gerekir ve koşullu If-Match yazımı yapılır; varsayılan olmayan yerelleştirmeler silinir, varsayılan metadata korunur. Seçim değişikliği, ETag eksikliği veya HTTP 412 no-write hatasıdır; otomatik retry yoktur. Gerekli çevirileri önce kaydedin.

## Sorun giderme ve güvenlik

OAuth dosyası yoksa veya bozuksa yeni Desktop app JSON indirin. callback başarısızsa terminali açık tutup 127.0.0.1:8080 erişimine izin verin; yetki süresi dolduysa yeniden yetkilendirin ve token.json dosyasını yalnızca gerektiğinde silin. quota, network, missing video ve Codex login hatalarında arayüzün eylemini izleyin. OAuth JSON, token.json, API token veya tam ortam çıktısını paylaşmayın.

## Lisans

[LICENSE](../../../LICENSE) dosyasına bakın.
