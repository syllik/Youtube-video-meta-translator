# YouTube Video Metadata Translator

**Điều hướng ngôn ngữ:** [English](../../../README.md) · [简体中文](../zh-Hans/README.md) · [繁體中文](../zh-Hant/README.md) · [Español](../es/README.md) · [हिन्दी](../hi/README.md) · [Português (Brasil)](../pt-BR/README.md) · [বাংলা](../bn/README.md) · [Русский](../ru/README.md) · [日本語](../ja/README.md) · [پنجابی](../pa-Arab/README.md) · [Türkçe](../tr/README.md) · **Tiếng Việt** · [العربية](../ar/README.md) · [मराठी](../mr/README.md) · [తెలుగు](../te/README.md) · [한국어](../ko/README.md) · [தமிழ்](../ta/README.md) · [اردو](../ur/README.md) · [Bahasa Indonesia](../id/README.md) · [Deutsch](../de/README.md) · [Français](../fr/README.md) · [Basa Jawa](../jv/README.md) · [فارسی](../fa/README.md) · [Italiano](../it/README.md) · [Hausa](../ha/README.md) · [ગુજરાતી](../gu/README.md) · [भोजपुरी](../bho/README.md)

## Ứng dụng làm gì?

Đây là ứng dụng Streamlit chạy cục bộ để quản lý bản địa hóa title và description của video YouTube. Chọn video, tạo hoặc tải JSON, kiểm tra bằng Preview changes rồi mới Publish changes. Kết quả từ Codex hoặc LLM bên ngoài không bao giờ tự động được xuất bản.

## Yêu cầu

Cần tài khoản Google có quyền với kênh, Python 3.12, trình duyệt trên cùng máy tính và JSON OAuth của client Desktop app. Quy trình Codex tùy chọn cũng cần Node.js và npm. Translate và LLM Translation prompt không cần API key của OpenAI hay LLM khác.

## Cài đặt

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

## Thiết lập Google OAuth

Tạo project trong Google Cloud Console và bật YouTube Data API v3. Trong Google Auth Platform, tạo client **Desktop app**, tải JSON và lưu chính xác tại:

~~~text
config/account_client_secrets_main.json
~~~

Lần cấp quyền đầu tiên dùng tài khoản quản lý kênh và cho phép callback cục bộ 127.0.0.1:8080. Không dùng Web application client hoặc API key thông thường.

## Khởi động ứng dụng

~~~bash
source .venv/bin/activate
streamlit run streamlit_app.py
~~~

Trên Windows, chạy `..venv\Scripts\Activate.ps1` rồi dùng cùng lệnh Streamlit. Mở http://127.0.0.1:8501.

## Quy trình Translate

1. Chọn một video trong sidebar.
2. Trong **Source languages**, giữ ngôn ngữ mặc định làm primary source và chọn localization hiện có làm tham chiếu tùy chọn.
3. Tạo bản nháp bằng **Codex** hoặc **External LLM**.
4. Kiểm tra khác biệt bằng **Preview changes**.
5. Chỉ dùng **Publish changes** khi preview hiện tại vẫn hợp lệ.
6. Xác nhận kết quả trong YouTube Studio.

### Primary source và tham chiếu tùy chọn

Ngôn ngữ mặc định là **Primary source** chỉ đọc. Chỉ localization hiện có mới được làm **Optional reference translations**; xóa mọi tham chiếu không xóa primary source. Đổi video sẽ xóa bản nháp và trạng thái preview.

## Codex

Cài đặt và đăng nhập Codex CLI cục bộ:

~~~bash
npm install -g @openai/codex
codex login
codex --version
~~~

Trong **Translate**, chọn ngôn ngữ đích và chạy tạo bản dịch. Codex chỉ tạo bản nháp để xem xét, không tự publish. Nếu thất bại, chạy `codex --version` và `codex login status` trong cùng terminal rồi khởi động lại Streamlit.

## External LLM

1. Nhấn **Prepare prompt**.
2. Dán prompt vào LLM bên ngoài và tạo UTF-8 JSON chỉ chứa đúng language codes được yêu cầu.
3. Dùng **Upload JSON** để tải file. Uploader chỉ bật khi prompt được gắn với video và target languages hiện tại; ứng dụng kiểm tra JSON và cho Preview trước khi publish.

Mỗi value chỉ được có title và description; title tối đa 100 ký tự, description tối đa 5.000 ký tự. Không tải wrapper metadata, Markdown, tên ngôn ngữ hoặc duplicate keys.

## Preview changes

Preview chỉ đọc và không gọi videos.update. Báo cáo hiển thị added, changed, unchanged và các localization YouTube bị bỏ khỏi draft nhưng sẽ được giữ lại.

## Publish changes

Publish kiểm tra lại draft và lấy lại video ngay trước khi ghi. Nếu video đã đổi, không có write. Sau write thành công, sidebar cache được xóa và count được tải lại; no-change hoặc conflict không được báo như refresh thành công.

## Danger zone: Reset languages

**Reset languages** chỉ xuất hiện trong **Danger zone** đang thu gọn của video đã chọn. Sau khi xác nhận, ứng dụng cần ETag mới và hợp lệ rồi ghi bằng If-Match có điều kiện; xóa localization không mặc định nhưng giữ metadata mặc định. Đổi lựa chọn, thiếu ETag hoặc HTTP 412 là lỗi no-write, không tự retry. Hãy lưu bản dịch cần giữ trước.

## Xử lý sự cố và bảo mật

OAuth bị thiếu hoặc sai định dạng thì tải lại JSON Desktop app. Callback lỗi thì giữ terminal mở và cho phép 127.0.0.1:8080; quyền hết hạn thì cấp quyền lại và chỉ xóa token.json khi thật sự cần. Làm theo hành động trong giao diện cho quota, network, missing video hoặc lỗi đăng nhập Codex. Không chia sẻ OAuth JSON, token.json, API token hay toàn bộ output môi trường.

## Giấy phép

Xem [LICENSE](../../../LICENSE).
