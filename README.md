# AI Debate Trainer

Ứng dụng luyện tranh biện tiếng Việt có AI phản biện, chấm điểm CER, và hỗ trợ nhập liệu bằng giọng nói. Backend là FastAPI, frontend là một file HTML duy nhất, chạy dưới dạng cửa sổ desktop trên Windows thông qua pywebview.

-## Cài đặt lần đầu

### Bước 1 — Clone repo

```powershell
git clone https://github.com/HoaiPhuoc-03/AI_Debate_Trainer.git
cd AI_Debate_Trainer
```

### Bước 2 — Lấy Groq API key

1. Vào `https://console.groq.com` → đăng ký / đăng nhập.
2. Vào **API Keys** → **Create API key** → copy key.

### Bước 3 — Chuẩn bị Supabase project

1. Vào Supabase Dashboard.
2. Tạo hoặc chọn project `AI-Debate-Trainer`.
3. Vào **Project Settings → API** để lấy:

   * Project URL
   * Publishable / anon key
   * Secret / service role key
4. Vào **Authentication → Providers → Email** và bật Email provider nếu chưa bật.
5. Đảm bảo database đã có các bảng chính:

   * `profiles`
   * `debate_sessions`
   * `practice_prompts`
   * `debate_turns`
   * `cer_scores`
   * `feedback_items`
   * `content_flags`
   * `user_memories`
   * `session_memories`

### Bước 4 — Tạo file `backend/.env`

Copy file mẫu rồi điền key:

```powershell
copy backend\.env_example backend\.env
```

Mở `backend\.env` và điền:

```env
GROQ_API_KEY=
GROQ_BASE_URL=
GROQ_MODEL=
GROQ_TIMEOUT_SECONDS=


# SPEECH_STT_PROVIDER=groq

# Speech mode
SPEECH_MAX_AUDIO_BYTES=
SPEECH_TTS_MAX_CHARS=


# Speech-to-Text provider
VOICE_STT_PROVIDER=elevenlabs
VOICE_STT_FALLBACK=groq

# Edge TTS only (Microsoft Edge Text-to-Speech - no API key required)
# Voices: vi-VN-NamMinhNeural (male), vi-VN-HoaiMyNeural (female)
EDGE_TTS_VOICE=vi-VN-NamMinhNeural
EDGE_TTS_RATE=+10%

# ElevenLabs experimental provider
ELEVENLABS_API_KEY=

# ElevenLabs STT
ELEVENLABS_STT_BASE_URL=https://api.elevenlabs.io/v1/speech-to-text
ELEVENLABS_STT_MODEL=scribe_v2


# Groq Whisper fallback
GROQ_STT_BASE_URL=https://api.groq.com/openai/v1/audio/transcriptions
GROQ_STT_MODEL=whisper-large-v3
GROQ_STT_TIMEOUT_SECONDS=60


# Storage provider
STORAGE_PROVIDER=supabase

# Supabase
SUPABASE_URL=https://dybmpokxehaghdkhtngv.supabase.co
SUPABASE_ANON_KEY=

SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
AUTH_PROVIDER=supabase

FIREBASE_CREDENTIALS_JSON=
```

Trong đó:

* `GROQ_API_KEY`: API key dùng để gọi Groq LLM.
* `ELEVENLABS_API_KEY`: API key dùng cho ElevenLabs STT nếu chọn `VOICE_STT_PROVIDER=elevenlabs`.
* `SUPABASE_SERVICE_ROLE_KEY`: lấy trong Supabase Dashboard → **Project Settings → API → Secret keys**. Key này chỉ dùng ở backend.
* `DATABASE_URL`: có thể để trống nếu backend dùng Supabase Python client. Chỉ cần điền nếu backend dùng SQLAlchemy/psycopg.
* `FIREBASE_CREDENTIALS_JSON`: có thể để trống nếu hệ thống đã chuyển sang Supabase. Biến này chỉ còn dùng cho rollback Firebase nếu backend vẫn hỗ trợ.

> Lưu ý: Không commit file `backend/.env` lên GitHub. Đặc biệt không public `GROQ_API_KEY`, `ELEVENLABS_API_KEY` và `SUPABASE_SERVICE_ROLE_KEY`.

---

## Database & Auth

### Supabase Auth

Hệ thống sử dụng Supabase Auth để quản lý đăng ký, đăng nhập và xác thực người dùng.

Luồng xác thực:

```text
User đăng ký / đăng nhập
→ Supabase Auth xác thực email/password
→ Backend trả access_token
→ Frontend lưu access_token
→ Các request sau gửi kèm Authorization: Bearer <access_token>
→ Backend verify token bằng Supabase
→ Backend lấy user_id và lưu dữ liệu theo user đó
```

Các endpoint auth chính:

| Method | Endpoint                | Mô tả                                       |
| ------ | ----------------------- | ------------------------------------------- |
| `POST` | `/api/v1/auth/register` | Đăng ký tài khoản bằng Supabase Auth        |
| `POST` | `/api/v1/auth/login`    | Đăng nhập và nhận access token              |
| `GET`  | `/api/v1/auth/me`       | Lấy thông tin user hiện tại từ Bearer token |
| `POST` | `/api/v1/auth/logout`   | Đăng xuất                                   |

Sau khi đăng nhập, frontend cần gửi token vào các request cần xác thực:

```http
Authorization: Bearer <access_token>
```

### Supabase Database

Hệ thống sử dụng Supabase Postgres để lưu dữ liệu luyện tập.

Các bảng chính:

| Table              | Vai trò                             |
| ------------------ | ----------------------------------- |
| `profiles`         | Lưu hồ sơ người dùng                |
| `debate_sessions`  | Lưu phiên tranh biện                |
| `practice_prompts` | Lưu đề bài từng lượt luyện tập      |
| `debate_turns`     | Lưu từng lượt lập luận và phản biện |
| `cer_scores`       | Lưu điểm Claim, Evidence, Reasoning |
| `feedback_items`   | Lưu điểm mạnh, điểm yếu, gợi ý      |
| `content_flags`    | Lưu cảnh báo/lỗi input/provider     |
| `user_memories`    | Lưu cá nhân hóa dài hạn theo user   |
| `session_memories` | Lưu memory ngắn hạn theo từng phiên |

### Rollback database

Trong giai đoạn chuyển đổi, backend vẫn có thể hỗ trợ rollback database bằng biến:

```env
STORAGE_PROVIDER=firebase
```

hoặc:

```env
STORAGE_PROVIDER=supabase
```

* `STORAGE_PROVIDER=supabase`: lưu dữ liệu mới vào Supabase.
* `STORAGE_PROVIDER=firebase`: quay lại Firebase store nếu backend còn hỗ trợ fallback.
* `AUTH_PROVIDER=supabase`: sử dụng Supabase Auth cho đăng ký/đăng nhập.

---

## Ghi chú bảo mật

* Không commit `backend/.env` lên git.
* Không đưa `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` hoặc database password vào bất kỳ file nào trong repo.
* `SUPABASE_SERVICE_ROLE_KEY` có quyền cao trên backend, không được đưa vào frontend.
* Frontend chỉ được dùng access token của user sau khi đăng nhập, không được chứa service role key.
* Nếu bật rollback Firebase, không commit `FIREBASE_CREDENTIALS_JSON` hoặc service account key.
* Khi deploy production, cần bật và kiểm tra Row Level Security policies phù hợp với Supabase Auth.
