# API Contract - Week 5: AI Debate Trainer
Base URL (Local): http://127.0.0.1:8000

## 1. Health Check
Kiểm tra trạng thái hoạt động của hệ thống backend.

### Endpoint: GET /health

### Response Body:

JSON
{
  "status": "ok"
}
## 2. Start Session
Khởi tạo một phiên tranh biện mới với các cấu hình về chủ đề và độ khó.

### Endpoint: POST /api/v1/debate/session

### Request Body:

JSON
{
  "topic": "Có nên cấm học sinh dùng điện thoại trong lớp học?",
  "stance": "Ủng hộ",
  "difficulty": "Trung bình",
  "input_mode": "text"
}
### Response Body:

JSON
{
  "session_id": "uuid-string-here",
  "topic": "Có nên cấm học sinh dùng điện thoại trong lớp học?",
  "stance": "Ủng hộ",
  "difficulty": "Trung bình",
  "input_mode": "text",
  "status": "ready"
}
## 3. Debate Turn
Gửi luận điểm của người dùng và nhận phản biện từ AI.

### Endpoint: POST /api/v1/debate/turn

### Request Body:

JSON
{
  "session_id": "uuid-string-here",
  "user_argument": "Em cho rằng nên cấm vì điện thoại làm học sinh mất tập trung trong giờ học."
}
### Response (Success)
### Status Code: 200 OK

JSON
{
  "session_id": "uuid-string-here",
  "user_argument": "Em cho rằng nên cấm vì điện thoại làm học sinh mất tập trung trong giờ học.",
  "ai_rebuttal": "Tuy nhiên, điện thoại cũng là công cụ tra cứu thông tin nhanh chóng...",
  "status": "success"
}
### Response (Error/Overload)
### Status Code: 503 Service Unavailable hoặc 200 với status error.

JSON
{
  "session_id": "uuid-string-here",
  "user_argument": "Em cho rằng nên cấm vì điện thoại làm học sinh mất tập trung trong giờ học.",
  "ai_rebuttal": "AI hiện đang quá tải tạm thời. Vui lòng thử lại sau ít phút.",
  "status": "error"
}
## 4. Get Session Info
Truy xuất thông tin chi tiết của một phiên tranh biện đã tồn tại.

### Endpoint: GET /api/v1/debate/session/{session_id}

Example: GET /api/v1/debate/session/1e3ac524-df5e-446a-b90a-e9f4718ce949

### Response Body:

JSON
{
  "session_id": "1e3ac524-df5e-446a-b90a-e9f4718ce949",
  "topic": "Có nên cấm học sinh dùng điện thoại trong lớp học?",
  "stance": "Ủng hộ",
  "difficulty": "Trung bình",
  "input_mode": "text",
  "status": "found"
}
## 5. Workflow Logic (Frontend)
Khởi tạo: Gọi POST /api/v1/debate/session để tạo phiên.

Lưu trữ: Lưu session_id từ response để sử dụng cho các bước tiếp theo.

Tương tác: Gọi POST /api/v1/debate/turn mỗi khi người dùng gửi luận điểm.

Hiển thị: Render nội dung từ ai_rebuttal lên giao diện chat.

Xử lý lỗi: Nếu status trả về error, hiển thị thông báo lỗi thân thiện để người dùng thử lại sau.

## 6. Lưu ý quan trọng
Swagger UI: Khi kiểm tra trên Swagger, nhập trực tiếp session_id vào trường tham số, không bao gồm dấu ngoặc kép.

Validation: Trường user_argument là bắt buộc, không được để trống.

CORS: Đảm bảo Backend đã cấu hình cho phép Frontend truy cập.