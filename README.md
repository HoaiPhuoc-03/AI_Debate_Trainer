# AI Debate Trainer

Ứng dụng luyện tranh biện tiếng Việt có AI phản biện, chấm điểm CER, và hỗ trợ nhập liệu bằng giọng nói. Backend là FastAPI, frontend là một file HTML duy nhất, chạy dưới dạng cửa sổ desktop trên Windows thông qua pywebview.

---

## Mục lục

1. [Kiến trúc tổng quan](#kiến-trúc-tổng-quan)
2. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Cài đặt lần đầu](#cài-đặt-lần-đầu)
4. [Chạy app (chế độ dev)](#chạy-app-chế-độ-dev)
5. [Chạy backend riêng lẻ (tuỳ chọn)](#chạy-backend-riêng-lẻ-tuỳ-chọn)
6. [Chạy tests](#chạy-tests)
7. [Build file .exe](#build-file-exe)
8. [Cấu trúc thư mục](#cấu-trúc-thư-mục)
9. [API nhanh](#api-nhanh)
10. [Lỗi thường gặp](#lỗi-thường-gặp)

---

## Kiến trúc tổng quan

```
┌─────────────────────────────────────┐
│          desktop_app.py             │  ← launcher: khởi động backend + frontend + mở cửa sổ
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐   ┌─────────────────────┐
│  FastAPI    │   │  Static HTTP server  │
│  :8000      │   │  serve frontend/     │
│  (backend/) │   │  web.html            │
└──────┬──────┘   └─────────────────────┘
       │
       ▼
  Groq API (LLM + STT)
  Edge TTS (Microsoft, không cần API key)
  Firebase Firestore (cloud database)
```

- **Backend** (`backend/`): FastAPI, xử lý auth, tạo phiên tranh biện, phân tích lập luận, chấm điểm CER, speech-to-text/text-to-speech.
- **Frontend** (`frontend/web.html`): Single-file app, giao tiếp với backend qua REST API.
- **Desktop launcher** (`desktop_app.py`): Tự bật backend, serve frontend, mở pywebview window.
- **Database**: Firebase Firestore — toàn bộ dữ liệu (users, sessions, turns, scores) lưu trên cloud. Cần cấu hình Firebase Service Account.

---

## Yêu cầu hệ thống

| Thành phần | Phiên bản tối thiểu |
|---|---|
| OS | Windows 10 64-bit trở lên |
| Python | 3.11+ |
| pip | bất kỳ (script tự upgrade) |
| Kết nối mạng | Bắt buộc (gọi Groq API) |
| Groq API key | Bắt buộc (xem bước 3) |

Kiểm tra Python:

```powershell
python --version
# Python 3.11.x hoặc mới hơn
```

> **Nếu chưa có Python:** tải tại https://www.python.org/downloads/ — tích chọn **"Add Python to PATH"** khi cài.

---

## Cài đặt lần đầu

### Bước 1 — Clone repo

```powershell
git clone https://github.com/HoaiPhuoc-03/AI_Debate_Trainer.git
cd AI_Debate_Trainer
```

### Bước 2 — Lấy Groq API key

1. Vào [https://console.groq.com](https://console.groq.com) → đăng ký miễn phí.
2. Vào **API Keys** → **Create API key** → copy key.

### Bước 3 — Tạo file `backend/.env`

Copy file mẫu rồi điền key:

```powershell
copy backend\.env_example backend\.env
```

Mở `backend\.env` và sửa dòng đầu:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx      # ← thay bằng key thật của bạn
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT_SECONDS=90

# Speech (Groq Whisper STT)
SPEECH_MAX_AUDIO_BYTES=8388608
SPEECH_TTS_MAX_CHARS=1200
GROQ_STT_BASE_URL=https://api.groq.com/openai/v1/audio/transcriptions
GROQ_STT_MODEL=whisper-large-v3
GROQ_STT_TIMEOUT_SECONDS=60

# Edge TTS — không cần API key
EDGE_TTS_VOICE=vi-VN-NamMinhNeural
EDGE_TTS_RATE=+10%

# Firebase Firestore — BẮT BUỘC, đây là database chính của app
# Chọn một trong hai cách cấu hình:
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}  # paste nội dung file JSON vào đây
FIREBASE_CREDENTIALS_PATH=                                                 # hoặc điền đường dẫn tới file JSON
FIREBASE_PROJECT_ID=your-firebase-project-id
```

> **Lưu ý:** Không commit file `backend/.env` lên git (đã có trong `.gitignore`).

### Bước 4 — Lấy Firebase Service Account

> **Quan trọng:** App dùng **Firebase Firestore** làm database chính. Không có Firebase thì backend sẽ không khởi động được.

1. Vào [Firebase Console](https://console.firebase.google.com) → chọn project (hoặc tạo mới).
2. **Project Settings** → **Service accounts** → **Generate new private key** → tải file `.json` về.
3. Chọn một trong hai cách điền vào `backend/.env`:
   - **Cách A** — paste nội dung file JSON vào `FIREBASE_CREDENTIALS_JSON` (dùng được mọi nơi):
     ```env
     FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"my-project",...}
     ```
   - **Cách B** — điền đường dẫn tới file JSON:
     ```env
     FIREBASE_CREDENTIALS_PATH=C:\path\to\serviceAccountKey.json
     ```
4. Điền `FIREBASE_PROJECT_ID` bằng project ID lấy từ Firebase Console.
5. Trong Firestore Console, tạo database ở chế độ **Production** hoặc **Test** và thêm các **Composite Indexes** sau (bắt buộc để query hoạt động):

   | Collection | Fields |
   |---|---|
   | `debate_turns` | `session_id` ASC, `turn_number` ASC |
   | `feedback_items` | `turn_id` ASC, `created_at` ASC |
   | `debate_sessions` | `user_id` ASC, `created_at` DESC |

---

## Chạy app (chế độ dev)

Một lệnh duy nhất từ thư mục gốc của project:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

Script tự động:
1. Tạo virtual environment `.venv` nếu chưa có.
2. Cài tất cả dependencies (`backend/requirements.txt` + `requirements-desktop.txt`).
3. Khởi động FastAPI backend tại `http://127.0.0.1:8000`.
4. Serve `frontend/web.html` qua một static HTTP server local.
5. Mở cửa sổ desktop **AI Debate Trainer** bằng pywebview.

Khi cửa sổ đóng, backend cũng tự tắt.

> ⚠️ **Không mở `frontend/web.html` trực tiếp bằng trình duyệt.** File HTML cần gọi backend đang chạy, nếu không sẽ báo `Failed to fetch`.

---

## Chạy backend riêng lẻ (tuỳ chọn)

Nếu bạn muốn phát triển, test API bằng Swagger, hoặc dùng frontend trên trình duyệt:

```powershell
# Kích hoạt venv
.venv\Scripts\activate

# Khởi động backend (hot-reload)
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health check:

```powershell
curl http://127.0.0.1:8000/health
# {"status":"ok"}
```

Kiểm tra Groq hoạt động (không in API key):

```powershell
.venv\Scripts\python.exe scripts\check_groq_provider.py
```

---

## Chạy tests

```powershell
# Từ thư mục gốc, với venv đã kích hoạt
.venv\Scripts\activate
python -m unittest discover -s tests
```

Hoặc chạy một file test cụ thể:

```powershell
python -m unittest tests.test_cer_scorer
```

---

## Build file .exe

Tạo bản phân phối standalone (không cần Python cài sẵn trên máy khác):

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows_app.ps1
```

Sau khi build xong, app nằm tại:

```
dist\
└── AI Debate Trainer\
    ├── AI Debate Trainer.exe   ← chạy file này
    ├── backend\
    ├── frontend\
    └── ...
```

> ⚠️ **Phải giữ nguyên cả thư mục `AI Debate Trainer\`**, không chỉ copy riêng file `.exe`. App cần các file đi kèm trong thư mục build.

Để gửi cho người dùng khác: nén toàn bộ thư mục `dist\AI Debate Trainer\` thành `.zip`.

---

## Cấu trúc thư mục

```
AI_Debate_Trainer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # Endpoints: /register, /login, /me, /logout
│   │   │   ├── debate.py        # Endpoints: /session, /turn, /summary, /progress
│   │   │   └── speech.py        # Endpoints: STT, TTS
│   │   ├── core/                # Config, DB connection
│   │   ├── schemas/             # Pydantic models
│   │   ├── services/
│   │   │   ├── ai_service.py    # Điều phối Groq LLM
│   │   │   ├── auth_service.py  # Đăng ký, đăng nhập, token
│   │   │   ├── cer_scorer.py    # Chấm điểm CER lập luận
│   │   │   ├── groq_client.py   # HTTP client gọi Groq LLM
│   │   │   ├── groq_stt_client.py  # HTTP client gọi Groq Whisper
│   │   │   ├── elevenlabs_stt_client.py # Experimental ElevenLabs STT
│   │   │   ├── normalization.py # Chuẩn hoá input/output
│   │   │   ├── output_parser.py # Parse JSON từ LLM
│   │   │   ├── prompt_builder.py# Xây dựng system/user prompt
│   │   │   ├── session_store.py # SQLite: users, sessions, turns
│   │   │   └── speech_service.py# Orchestrate STT + TTS
│   │   └── main.py              # FastAPI app, CORS, routers
│   ├── .env                     # ← TẠO THỦ CÔNG (xem Bước 3)
│   └── requirements.txt
├── frontend/
│   └── web.html                 # Toàn bộ UI (single-file)
├── prompts/
│   └── system_prompt.md         # System prompt cho AI coach
├── scripts/
│   ├── run_windows_app.ps1      # Chạy app dev mode
│   ├── build_windows_app.ps1    # Build .exe
│   └── check_groq_provider.py   # Kiểm tra Groq config
├── tests/                       # Unit tests
├── docs/                        # Tài liệu bổ sung
├── desktop_app.py               # Desktop launcher
├── requirements.txt             # Trỏ tới backend + desktop requirements
├── requirements-desktop.txt     # pywebview, pyinstaller
└── .gitignore
```

---

## API nhanh

| Method | Endpoint | Mô tả |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/auth/register` | Đăng ký tài khoản |
| `POST` | `/api/v1/auth/login` | Đăng nhập, nhận token |
| `GET` | `/api/v1/auth/me` | Thông tin user hiện tại |
| `POST` | `/api/v1/auth/logout` | Đăng xuất |
| `POST` | `/api/v1/debate/session` | Tạo phiên tranh biện mới |
| `POST` | `/api/v1/debate/turn` | Gửi lập luận, nhận phản biện + CER |
| `GET` | `/api/v1/debate/session/{id}` | Thông tin phiên |
| `POST` | `/api/v1/debate/session/{id}/end` | Kết thúc phiên |
| `GET` | `/api/v1/debate/session/{id}/summary` | Tổng kết phiên |
| `GET` | `/api/v1/debate/progress/overview` | Tổng quan tiến độ |
| `POST` | `/api/v1/speech/stt` | Speech-to-text (Groq Whisper) |
| `POST` | `/api/v1/speech/tts` | Text-to-speech (Edge TTS) |

Xem chi tiết tại Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) (khi backend đang chạy).

---

## Cấu hình voice providers

Mặc định app dùng ElevenLabs cho STT, Groq Whisper làm fallback, và Edge TTS cho phần đọc phản biện:

```env
VOICE_STT_PROVIDER=elevenlabs
VOICE_STT_FALLBACK=groq
```

Cấu hình STT:

```env
ELEVENLABS_API_KEY=your_key_here
ELEVENLABS_STT_BASE_URL=https://api.elevenlabs.io/v1/speech-to-text
ELEVENLABS_STT_MODEL=scribe_v2
GROQ_STT_BASE_URL=https://api.groq.com/openai/v1/audio/transcriptions
GROQ_STT_MODEL=whisper-large-v3
```

TTS chỉ dùng Edge:

```env
EDGE_TTS_VOICE=vi-VN-NamMinhNeural
EDGE_TTS_RATE=+10%
```

Rollback STT nhanh về Groq:

```env
VOICE_STT_PROVIDER=groq
```

---

## Lỗi thường gặp

### `Failed to fetch` trong giao diện

**Nguyên nhân:** Mở `web.html` trực tiếp bằng trình duyệt, backend chưa chạy.

**Cách sửa:** Luôn chạy qua script:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

### `Firebase credentials not configured`

Backend không tìm thấy thông tin xác thực Firebase. Kiểm tra `backend/.env` đã có `FIREBASE_CREDENTIALS_JSON` hoặc `FIREBASE_CREDENTIALS_PATH` hợp lệ, và `FIREBASE_PROJECT_ID` đúng.

### Firestore `FAILED_PRECONDITION` / query lỗi index

Firestore yêu cầu composite index cho một số query. Vào [Firebase Console](https://console.firebase.google.com) → Firestore → **Indexes** → tạo đủ 3 index như hướng dẫn ở Bước 4. Firebase thường in link tạo index thẳng trong error message.

### `Port 8000 is already in use`

Một tiến trình khác đang dùng port 8000. Tắt tiến trình đó hoặc đóng phiên app cũ trước khi chạy lại.

```powershell
# Tìm và tắt tiến trình dùng port 8000
netstat -ano | findstr :8000
taskkill /PID <pid> /F
```

### Groq không phản hồi / `status: error`

Kiểm tra theo thứ tự:
1. `backend/.env` đã có `GROQ_API_KEY` hợp lệ chưa?
2. `GROQ_MODEL` đúng tên model không? (ví dụ: `llama-3.3-70b-versatile`)
3. Tài khoản Groq còn quota không?
4. Máy có kết nối mạng không?

```powershell
.venv\Scripts\python.exe scripts\check_groq_provider.py
```

### `python` không nhận dạng được

Python chưa được thêm vào PATH. Cài lại Python và tích chọn **"Add Python to PATH"**, hoặc chạy `py` thay vì `python`.

### Cửa sổ app không mở (pywebview lỗi)

Thử chạy lại script — lần đầu pip cài pywebview có thể chậm. Nếu vẫn lỗi:

```powershell
.venv\Scripts\pip install pywebview --force-reinstall
```

---

## Ghi chú bảo mật

- Không commit `backend/.env` lên git (đã có trong `.gitignore`).
- Không đưa `GROQ_API_KEY` hay `FIREBASE_CREDENTIALS_JSON` vào bất kỳ file nào trong repo.
- Firebase Service Account key có quyền đọc/ghi toàn bộ Firestore — bảo quản như mật khẩu, không chia sẻ công khai.
