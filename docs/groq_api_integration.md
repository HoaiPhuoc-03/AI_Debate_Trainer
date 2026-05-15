# Tích hợp Groq API cho AI Debate Trainer

## 1. Vì sao dùng Groq?

- Backend không còn phụ thuộc Ollama local.
- Groq API phù hợp hơn cho demo và phản hồi nhanh trên máy yếu.
- Nếu Groq lỗi, backend trả lỗi thân thiện thay vì dùng phản biện mẫu.

## 2. Cách lấy Groq API key

1. Vào Groq Console.
2. Tạo API key mới.
3. Thêm key vào `backend/.env`.

Không commit file `.env` thật và không đưa API key vào code.

## 3. Cấu hình `backend/.env`

```env
GROQ_API_KEY=your_real_groq_api_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1/chat/completions
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_TIMEOUT_SECONDS=90
```

Muốn dùng model Groq nhẹ hơn hoặc nhanh hơn, đổi `GROQ_MODEL`.

## 4. Chạy backend

```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload
```

Kiểm tra health:

```powershell
curl http://127.0.0.1:8000/health
```

Kết quả mong đợi:

```json
{"status":"ok"}
```

## 5. Test qua API

Các endpoint frontend đang dùng không đổi:

- `POST /api/v1/debate/session`
- `POST /api/v1/debate/turn`

Bạn có thể mở Swagger tại:

```text
http://127.0.0.1:8000/docs
```

Luồng test:

1. Gọi `POST /api/v1/debate/session` để tạo session.
2. Lấy `session_id`.
3. Gọi `POST /api/v1/debate/turn` với `session_id` và `user_argument`.
4. Kiểm tra response có `ai_rebuttal`, `cer`, `feedback`, `status`.

Nếu Groq lỗi, `status` sẽ là `error`, `cer` về 0 và `ai_rebuttal` là thông báo lỗi, không phải phản biện mẫu.

## 6. Test riêng Groq provider

Từ thư mục project:

```powershell
python scripts\check_groq_provider.py
```

Script chỉ in provider, model, trạng thái `ok`, text và lỗi nếu có. Script không in API key.

## 7. Troubleshooting

- Thiếu `GROQ_API_KEY`: thêm key vào `backend/.env`.
- Sai model name: kiểm tra lại `GROQ_MODEL` trong Groq Console.
- Hết quota hoặc rate limit: đổi key/tài khoản hoặc chờ quota reset.
- Mạng lỗi: backend báo Groq không phản hồi, endpoint không crash.
- Groq trả sai format: backend báo lỗi định dạng và không dùng phản biện mẫu.
- Frontend vẫn hiện không phản hồi: kiểm tra backend log, `/health`, và endpoint `/api/v1/debate/turn`.
