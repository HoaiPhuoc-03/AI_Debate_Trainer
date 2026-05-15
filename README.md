# AI Debate Trainer

AI Debate Trainer là ứng dụng luyện tranh biện dùng FastAPI backend, giao diện web, và bản desktop Windows chạy bằng local backend.

## Cấu trúc chính

- `backend/`: FastAPI API cho auth, tạo phiên tranh biện, chấm CER, lưu tiến độ.
- `frontend/web.html`: giao diện chính của app.
- `desktop_app.py`: launcher desktop Windows. File này tự bật backend local, serve frontend, rồi mở cửa sổ app.
- `scripts/run_windows_app.ps1`: chạy app desktop ở chế độ phát triển.
- `scripts/build_windows_app.ps1`: build app Windows thành thư mục `.exe`.
- `scripts/check_groq_provider.py`: kiểm tra nhanh cấu hình Groq mà không in API key.
- `docs/windows-desktop-app.md`: tài liệu riêng cho bản desktop.
- `docs/groq_api_integration.md`: hướng dẫn cấu hình Groq API.

## Yêu cầu trước khi chạy

Cần cài:

- Windows 10 hoặc mới hơn.
- Python 3.11+.
- Groq API key.

Kiểm tra Python:

```powershell
python --version
```

Thêm Groq API key vào `backend/.env`:

```env
GROQ_API_KEY=your_real_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

## Chạy app Windows

Từ thư mục project:

```powershell
cd E:\AI_Debate_Trainer
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

Script sẽ tự:

1. Tạo `.venv` nếu chưa có.
2. Cài backend dependencies.
3. Cài desktop dependencies.
4. Bật FastAPI backend ở `http://127.0.0.1:8000`.
5. Serve `frontend/web.html` bằng local static server.
6. Mở cửa sổ desktop `AI Debate Trainer`.

Không cần mở `frontend/web.html` trực tiếp bằng trình duyệt. Nếu mở trực tiếp file HTML, frontend có thể báo `Failed to fetch` vì backend chưa chạy.

## Build file `.exe`

Từ thư mục project:

```powershell
cd E:\AI_Debate_Trainer
powershell -ExecutionPolicy Bypass -File scripts\build_windows_app.ps1
```

Sau khi build xong, app nằm tại:

```text
dist\AI Debate Trainer\AI Debate Trainer.exe
```

Khi gửi app cho máy khác, giữ nguyên cả thư mục:

```text
dist\AI Debate Trainer
```

Không chỉ gửi riêng file `.exe`, vì app cần các file đi kèm trong thư mục build.

## Dữ liệu đăng nhập và phiên tranh biện

Desktop app lưu database SQLite ở:

```text
%LOCALAPPDATA%\AI Debate Trainer\ai_debate_trainer.db
```

Nếu người dùng tick `Ghi nhớ đăng nhập`, token đăng nhập sẽ được lưu và lần sau mở app có thể tự restore phiên đăng nhập. Khi bấm `Đăng xuất`, token bị xóa.

## Chạy test

```powershell
python -m unittest discover -s tests
```

## Lỗi thường gặp

### Failed to fetch

Nguyên nhân thường gặp: mở trực tiếp `frontend/web.html` mà backend chưa chạy.

Cách đúng:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

Hoặc kiểm tra backend:

```powershell
curl http://127.0.0.1:8000/health
```

Nếu backend chạy đúng, kết quả là:

```json
{"status":"ok"}
```

### Port 8000 đã được dùng

Đóng process đang dùng port `8000`, hoặc tắt backend cũ trước khi chạy app lại.

### Groq không phản hồi

Kiểm tra `backend/.env` có `GROQ_API_KEY` hợp lệ, `GROQ_MODEL` đúng tên model, tài khoản còn quota, và máy có kết nối mạng.
