# AI Debate Trainer

AI Debate Trainer là ứng dụng luyện tranh biện tiếng Việt, hỗ trợ người dùng luyện lập luận, nhận phản biện từ AI, chấm điểm theo cấu trúc Claim – Evidence – Reasoning (C-E-R), kiểm chứng dẫn chứng và theo dõi tiến độ học tập.

Ứng dụng được triển khai dưới dạng desktop app trên Windows bằng `pywebview`. Backend sử dụng `FastAPI`, frontend là giao diện web chạy trong cửa sổ desktop. Hệ thống tích hợp Groq LLM để sinh phản biện và feedback, ElevenLabs STT để chuyển giọng nói thành văn bản, Microsoft Edge TTS để đọc phản hồi bằng giọng nói và Supabase để xác thực/lưu trữ dữ liệu người dùng.

---

## 1. Chức năng chính

- Đăng ký và đăng nhập bằng Supabase Auth.
- Tạo phiên luyện tranh biện theo topic, stance, difficulty và practice mode.
- Hỗ trợ các chế độ luyện tập:
  - Free Debate
  - Claim Writing
  - Evidence Finding
  - Quick Rebuttal
  - Full Argument
- Sinh phản biện, câu hỏi truy vấn và feedback bằng Groq LLM.
- Chấm điểm lập luận theo Claim – Evidence – Reasoning.
- Chế độ Claim Writing tập trung đánh giá chất lượng luận điểm dựa trên độ rõ lập trường, mức độ liên quan và độ cụ thể.
- Hỗ trợ nhập liệu bằng giọng nói thông qua ElevenLabs Speech-to-Text.
- Hỗ trợ đọc phản hồi bằng Microsoft Edge Text-to-Speech.
- Hỗ trợ Search & Fact-checking để kiểm chứng Evidence và hiển thị source links.
- Lưu lịch sử luyện tập, điểm số, feedback và tiến độ bằng Supabase.
- Dashboard tiến độ hiển thị tổng quan quá trình luyện tập của người dùng.

---

## 2. Cấu trúc mã nguồn

```text
Source code/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── data/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── assets/
│   ├── components/
│   ├── fonts/
│   ├── scripts/
│   ├── styles/
│   └── web.html
│
├── prompts/
│   └── system_prompt.md
│
├── scripts/
│   ├── run_windows_app.ps1
│   ├── build_windows_app.ps1
│   └── check_groq_provider.py
│
├── tests/
│   └── ...
│
├── docs/
│   └── ...
│
├── desktop_app.py
├── requirements.txt
├── requirements-desktop.txt
└── README.md
```

---

## 3. Công nghệ sử dụng

| Thành phần | Công nghệ |
|---|---|
| Desktop app | pywebview |
| Frontend | HTML, CSS, JavaScript |
| Backend | FastAPI, Python |
| AI phản biện/chấm điểm | Groq LLM |
| Speech-to-Text | ElevenLabs STT |
| Text-to-Speech | Microsoft Edge TTS |
| Database/Auth | Supabase Auth & Supabase PostgreSQL |
| Packaging/Run script | PowerShell scripts |

---

## 4. Yêu cầu môi trường

Máy chạy cần có:

- Windows 10/11.
- Python 3.10 trở lên.
- PowerShell.
- Kết nối Internet để gọi Groq, ElevenLabs và Supabase.
- Groq API key.
- ElevenLabs API key.
- Supabase project đã được tạo sẵn.

---

## 5. Cài đặt và chạy ứng dụng

### Bước 1 — Mở thư mục Source code

```powershell
cd "Source code"
```

### Bước 2 — Tạo file môi trường backend

Copy file mẫu:

```powershell
copy backend\.env.example backend\.env
```

Mở file `backend/.env` và điền các biến cần thiết.

### Bước 3 — Cấu hình biến môi trường

Nội dung mẫu:

```env
# Groq LLM
GROQ_API_KEY=
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT_SECONDS=90

# Speech-to-Text: ElevenLabs
VOICE_STT_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=
ELEVENLABS_STT_BASE_URL=https://api.elevenlabs.io/v1/speech-to-text
ELEVENLABS_STT_MODEL=scribe_v2

# Text-to-Speech: Microsoft Edge TTS
EDGE_TTS_VOICE=vi-VN-NamMinhNeural
EDGE_TTS_RATE=+10%

# Storage and Auth
STORAGE_PROVIDER=supabase
AUTH_PROVIDER=supabase

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
```

Ghi chú:

- `GROQ_API_KEY`: dùng để gọi Groq LLM.
- `ELEVENLABS_API_KEY`: dùng cho ElevenLabs STT.
- `SUPABASE_URL`: URL project Supabase.
- `SUPABASE_ANON_KEY`: public/anon key dùng cho luồng xác thực cơ bản.
- `SUPABASE_SERVICE_ROLE_KEY`: service role key dùng ở backend, không được đưa vào frontend.
- `DATABASE_URL`: chỉ cần điền nếu backend dùng kết nối trực tiếp PostgreSQL/SQLAlchemy. Nếu backend chỉ dùng Supabase client thì có thể để trống.

Không commit hoặc public file `backend/.env`.

### Bước 4 — Chuẩn bị Supabase

1. Vào Supabase Dashboard.
2. Tạo hoặc chọn project Supabase.
3. Vào **Project Settings → API** để lấy:
   - Project URL
   - Anon/Public key
   - Service role key
4. Vào **Authentication → Providers → Email** và bật Email provider.
5. Mở Supabase SQL Editor.
6. Chạy file schema nếu có:

```text
docs/supabase-schema.sql
```

Schema này tạo các bảng phục vụ xác thực người dùng, phiên luyện tập, lượt tranh biện, điểm số, feedback, fact-checking và tiến độ.

### Bước 5 — Chạy ứng dụng

Từ thư mục `Source code/`, chạy:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_windows_app.ps1
```

Script sẽ tự động:

1. Tạo môi trường ảo `.venv` nếu chưa có.
2. Cài dependency backend từ `backend/requirements.txt`.
3. Cài dependency desktop từ `requirements-desktop.txt`.
4. Khởi động FastAPI ở `127.0.0.1:8000`.
5. Mở giao diện desktop bằng pywebview.

---

## 6. Cách chạy backend riêng

Trong trường hợp muốn chạy backend riêng để debug:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Sau đó mở frontend hoặc desktop app để gọi API backend.

---

## 7. Database & Auth

### Supabase Auth

Hệ thống dùng Supabase Auth để đăng ký, đăng nhập và xác thực người dùng.

Luồng cơ bản:

```text
User đăng ký / đăng nhập
→ Supabase Auth xác thực email/password
→ Backend nhận access token
→ Frontend gửi Authorization: Bearer <access_token>
→ Backend verify token
→ Backend lưu dữ liệu luyện tập theo user_id
```

Một số endpoint xác thực chính:

| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/v1/auth/register` | Đăng ký tài khoản |
| POST | `/api/v1/auth/login` | Đăng nhập |
| GET | `/api/v1/auth/me` | Lấy thông tin user hiện tại |
| POST | `/api/v1/auth/logout` | Đăng xuất |

### Supabase Database

Hệ thống dùng Supabase PostgreSQL để lưu dữ liệu luyện tập.

Các nhóm dữ liệu chính:

| Nhóm dữ liệu | Vai trò |
|---|---|
| User/Profile | Thông tin người dùng |
| Practice/Debate Session | Phiên luyện tập |
| Debate Turn | Từng lượt người dùng gửi lập luận và nhận phản biện |
| C-E-R Score | Điểm Claim, Evidence, Reasoning |
| Feedback | Điểm mạnh, điểm yếu, gợi ý cải thiện |
| Fact-checking | Kết quả kiểm chứng Evidence hoặc factual claim |
| Source Links | Nguồn tham khảo cho fact-checking |
| Progress | Dữ liệu dashboard và tiến độ học tập |

Tên bảng cụ thể phụ thuộc vào file `docs/supabase-schema.sql` của phiên bản hiện tại.

---

## 8. Ghi chú về các chế độ luyện tập

### Free Debate

Người dùng tranh biện tự do với AI. AI phản biện lại quan điểm của người dùng dựa trên topic, stance và difficulty.

### Claim Writing

Người dùng luyện viết luận điểm. Hệ thống tập trung đánh giá chất lượng Claim, bao gồm:

- Độ rõ lập trường.
- Mức độ liên quan đến chủ đề.
- Độ cụ thể và phạm vi của Claim.
- Gợi ý một Claim mẫu tốt hơn nếu có.

### Evidence Finding

Người dùng luyện tìm Evidence để hỗ trợ hoặc phản bác một claim. Hệ thống đánh giá mức độ liên quan, độ tin cậy và có thể kiểm chứng của Evidence.

### Quick Rebuttal

Người dùng luyện phản biện nhanh, phát hiện điểm yếu, lỗi lập luận hoặc đưa ra phản ví dụ.

### Full Argument

Người dùng xây dựng lập luận hoàn chỉnh. Hệ thống đánh giá đầy đủ theo Claim – Evidence – Reasoning.

---

## 9. Search & Fact-checking

Hệ thống có thể sử dụng Search Service để hỗ trợ kiểm chứng Evidence hoặc factual claim.

Kết quả fact-checking có thể gồm:

- Verdict: verified, inaccurate, unverifiable hoặc outdated.
- Explanation: giải thích ngắn gọn kết quả kiểm chứng.
- Source links: các nguồn tham khảo liên quan.
- Better source suggestions: gợi ý nguồn tốt hơn nếu Evidence chưa đủ mạnh.

Tính năng này giúp tăng tính minh bạch khi người dùng sử dụng dẫn chứng trong tranh biện.

---

## 10. Voice Interaction

### Speech-to-Text

Hệ thống dùng ElevenLabs STT để chuyển giọng nói của người dùng thành văn bản trước khi gửi vào backend xử lý.

### Text-to-Speech

Hệ thống dùng Microsoft Edge TTS để đọc phản hồi của AI bằng tiếng Việt. Mặc định sử dụng giọng:

```text
vi-VN-NamMinhNeural
```

Có thể đổi sang giọng khác nếu cấu hình trong `.env`.

---

## 11. Dashboard / Progress

Dashboard tiến độ giúp người dùng theo dõi quá trình luyện tập.

Các thông tin có thể hiển thị:

- Tổng số phiên luyện tập.
- Tổng số lượt trả lời.
- Điểm C-E-R trung bình.
- Kỹ năng mạnh/yếu.
- Chủ đề đã luyện.
- Mục tiêu luyện tập.
- Streak hoặc chuỗi ngày luyện tập nếu có.
- Xu hướng cải thiện qua thời gian.

---

## 12. Chạy test

Nếu project có test, chạy:

```powershell
pytest
```

Hoặc compile nhanh backend để kiểm tra lỗi cú pháp:

```powershell
python -m compileall backend/app
```

---

## 13. Ghi chú bảo mật

- Không commit file `backend/.env`.
- Không public `GROQ_API_KEY`.
- Không public `ELEVENLABS_API_KEY`.
- Không public `SUPABASE_SERVICE_ROLE_KEY`.
- Không đưa service role key vào frontend.
- Frontend chỉ được dùng token người dùng sau khi đăng nhập.
- Khi triển khai thật, cần kiểm tra Row Level Security policies của Supabase.

---

## 14. Ghi chú khác

Các thư mục/file sau không nên public:

```text
.git/
.venv/
venv/
__pycache__/
.pytest_cache/
.env
backend/.env
*.log
docs/mockups/chrome-profile/
docs/mockups/chrome-app-profile/
docs/mockups/chrome-cdp-profile2/
```