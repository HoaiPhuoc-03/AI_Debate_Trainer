# Thiết kế Evaluation Pipeline cho AI Debate Trainer

## 1. Mục tiêu evaluation pipeline

Evaluation pipeline dùng để đánh giá chất lượng output của AI Debate Trainer trước khi fine-tuning/QLoRA. Mục tiêu chính là kiểm tra model hoặc prompt có trả đúng cấu trúc phản biện, CER và feedback hay không, đồng thời tạo report có thể so sánh giữa các experiment.

## 2. Vì sao cần evaluation trước QLoRA

Trước khi train, project cần biết baseline hiện tại mạnh/yếu ở đâu. Nếu chưa có evaluation, việc QLoRA có thể chỉ cải thiện cảm giác chủ quan nhưng không chứng minh được output đúng format hơn, CER ổn định hơn hay feedback bám vào điểm yếu hơn.

## 3. Dữ liệu đầu vào

- `datasets/eval_cases_v1.jsonl`: bộ eval case cố định, gồm topic, stance, difficulty, age_group, debate_level, language, user_argument, expected và metadata.
- `experiments/*_outputs.jsonl`: output sinh ra từ từng experiment như `mock_eval`, `baseline`, `prompt_v2`, `ollama_qwen` hoặc `qlora_v1`.

## 4. Cấu trúc output AI cần đánh giá

Output chuẩn cần có:

```json
{
  "rebuttal": "...",
  "cer": {
    "claim": 0,
    "evidence": 0,
    "reasoning": 0,
    "total": 0
  },
  "feedback": {
    "strengths": ["..."],
    "weaknesses": ["..."],
    "suggestions": ["..."]
  }
}
```

Pipeline có thể nhận raw output theo marker `[REBUTTAL]`, `[CER]`, `[FEEDBACK]`, sau đó dùng parser để chuyển về cấu trúc trên.

## 5. Bảy tiêu chí đánh giá

- `format_valid`: output có đủ `rebuttal`, `cer`, `feedback`; CER và feedback có đủ field con.
- `has_rebuttal`: rebuttal không rỗng, không quá ngắn và có dấu hiệu phản biện.
- `has_valid_cer`: claim/evidence/reasoning/total là số trong 0-10 và total đúng công thức trung bình.
- `has_feedback`: strengths, weaknesses và suggestions đều là list không rỗng.
- `feedback_aligned`: feedback nhắc tới đúng nhóm yếu nhất trong CER, ví dụ evidence thấp thì nhắc bằng chứng/ví dụ/số liệu.
- `within_word_limit`: output không vượt `expected.max_words`, mặc định 300.
- `language_valid`: output trông giống tiếng Việt, không lẫn đoạn ngoại ngữ bất thường quá dài.

## 6. Cách tính điểm

- Mỗi tiêu chí đạt được 1 điểm.
- Tổng điểm tối đa là 7.
- Một case được xem là pass nếu đạt ít nhất 6/7.

Đây là rule-based scoring để kiểm tra tính ổn định kỹ thuật, không phải điểm chất lượng học thuật tuyệt đối.

## 7. Cách chạy

Kiểm tra eval cases:

```powershell
python scripts/check_eval_cases.py
```

Sinh output mock:

```powershell
python scripts/run_evaluation.py --name mock_eval --mode mock
```

Chấm output và tạo report:

```powershell
python scripts/evaluate_outputs.py --input experiments/mock_eval_outputs.jsonl
```

So sánh các experiment:

```powershell
python scripts/compare_experiments.py
```

## 8. Cách dùng kết quả để so sánh

Mỗi experiment nên có tên rõ ràng:

- `baseline`: prompt/model hiện tại.
- `prompt_v2`: prompt cải tiến.
- `ollama_qwen`: chạy live với model Qwen qua Ollama.
- `qlora_v1`: model/adaptor sau QLoRA.

Sau khi tạo report, dùng `compare_experiments.py` để xem điểm trung bình, pass rate và từng criteria count. Điều này giúp nhận ra cải tiến cụ thể, ví dụ prompt mới có thể tăng `format_valid` nhưng chưa tăng `feedback_aligned`.

## 9. Hạn chế

- Rule-based evaluation chưa thay thế human review.
- `feedback_aligned` chỉ kiểm tra keyword đơn giản.
- `language_valid` chỉ kiểm tra tương đối.
- `has_rebuttal` chưa hiểu lập luận sâu, chỉ nhận diện dấu hiệu phản biện.
- Cần review thủ công test set và một phần eval cases trước khi đưa vào báo cáo cuối.

## 10. Hướng mở rộng

- Thêm human evaluation trên một tập nhỏ.
- Thêm LLM-as-judge khi được phép dùng API hoặc model local đủ mạnh.
- Tạo confusion matrix theo `main_weakness` hoặc focus của eval case.
- So sánh trước/sau QLoRA bằng cùng eval set.
- Theo dõi parser fallback rate và lỗi format theo từng model.
