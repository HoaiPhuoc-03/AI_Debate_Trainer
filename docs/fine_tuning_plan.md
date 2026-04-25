# Kế hoạch fine-tuning/QLoRA cho AI Debate Trainer

## 1. Mục tiêu

Fine-tuning/QLoRA nhằm giúp model phản biện đúng vai trò Debate Trainer hơn, trả output ổn định theo schema, chấm CER nhất quán hơn và đưa feedback bám vào điểm yếu chính của lập luận.

## 2. Vì sao không train local ở giai đoạn này

Project hiện ưu tiên demo backend/frontend và pipeline dữ liệu. Training local chưa phù hợp vì:

- Máy cá nhân có thể yếu hoặc thiếu GPU.
- QLoRA vẫn cần GPU để train ổn định.
- Việc train sẽ tốn thời gian, bộ nhớ và cần kiểm soát experiment kỹ hơn.
- Giai đoạn hiện tại chỉ cần chuẩn hóa prompt, parser, dataset và evaluation.

## 3. Roadmap

- Giai đoạn 1: Prompt + parser + structured output.
- Giai đoạn 2: Dataset 1000 mẫu.
- Giai đoạn 3: Evaluation pipeline.
- Giai đoạn 4: QLoRA prototype trên Colab/Kaggle.
- Giai đoạn 5: Tích hợp model/adaptor nếu kịp.

## 4. Model có thể thử

- Qwen 1.5B/3B Instruct.
- Llama 3.2 1B/3B.

Các model nhỏ phù hợp hơn cho prototype vì chi phí thấp, dễ chạy trên Colab/Kaggle và đủ để đánh giá format/output behavior.

## 5. Cách tích hợp vào backend

Backend nên tiếp tục giữ abstraction provider:

- `AI_PROVIDER`: chọn provider runtime.
- `OLLAMA_MODEL`: model local hiện tại.
- Fine-tuned model mode: thêm cấu hình model/adaptor sau khi có artifact QLoRA.

Route `/turn` không nên phụ thuộc trực tiếp vào model cụ thể. Backend chỉ cần gọi service sinh phân tích debate và nhận về output chuẩn gồm rebuttal, CER, feedback, raw_text và error.

## 6. Rủi ro

- Synthetic data chưa đủ tự nhiên.
- Format output có thể bị overfit nếu sample quá giống nhau.
- CER cần review thêm để gần rubric chuyên gia.
- Dataset unsafe/off_topic cần kiểm tra kỹ để tránh học phản hồi không mong muốn.
- Model nhỏ có thể cải thiện format nhưng chưa chắc cải thiện reasoning sâu.

## 7. Tiêu chí thành công

- Output đúng format hơn.
- Phản biện rõ hơn và không đồng ý hoàn toàn với user.
- Feedback khớp `main_weakness` hơn.
- CER ổn định hơn giữa các topic và difficulty.
- Tỷ lệ parser fallback giảm trong evaluation.

## 8. Chuẩn bị trước khi QLoRA

- Chạy validate và split check sạch.
- Review thủ công một phần train/dev/test.
- Khóa test set, không dùng test để tune prompt hoặc hyperparameter.
- Xây evaluation script ở giai đoạn 3.
- Tạo baseline từ model hiện tại trước khi train.
- Ghi lại config experiment để so sánh sau QLoRA.
