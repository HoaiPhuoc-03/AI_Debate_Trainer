# QLoRA Experiment Report Template

## 1. Mục tiêu thí nghiệm

Mô tả mục tiêu của lần fine-tuning, ví dụ: cải thiện độ ổn định format `[REBUTTAL]`, `[CER]`, `[FEEDBACK]`, tăng chất lượng phản biện và feedback theo CER.

## 2. Dataset sử dụng

- Train file:
- Dev file:
- Test file:
- Số mẫu train/dev/test:
- Ghi chú chất lượng dữ liệu:

## 3. Base model

- Model:
- Kích thước:
- Nguồn model:
- Lý do chọn model:

## 4. Training environment

- Nền tảng: Google Colab / Kaggle / khác
- GPU:
- VRAM:
- Python version:
- Thư viện chính:

## 5. Hyperparameters

- max_seq_length:
- LoRA rank:
- LoRA alpha:
- LoRA dropout:
- batch size:
- gradient accumulation:
- learning rate:
- epochs:
- optimizer:

## 6. Training result

- Training loss:
- Validation loss:
- Thời gian train:
- Có OOM hay lỗi runtime không:
- Adapter output path:

## 7. Sample output trước/sau fine-tune

### Prompt test

```text
Chủ đề:
Lập trường người dùng:
Độ khó:
Nhóm tuổi:
Trình độ:
Lập luận người dùng:
```

### Baseline output

```text
...
```

### QLoRA output

```text
...
```

## 8. Evaluation result

- Experiment name:
- Total cases:
- Average score:
- Pass rate:
- Format valid:
- Has rebuttal:
- Has valid CER:
- Has feedback:
- Feedback aligned:
- Within word limit:
- Language valid:

## 9. Baseline vs QLoRA comparison

| Experiment | Avg Score | Pass Rate | Format | Rebuttal | CER | Feedback | Aligned | Word Limit | Language |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | | | | | | | | | |
| QLoRA | | | | | | | | | |

## 10. Limitations

- Dataset synthetic có thể lặp pattern.
- CER chưa phải nhãn chuyên gia hoàn toàn.
- Model nhỏ có thể cải thiện format nhưng chưa chắc cải thiện suy luận sâu.
- Evaluation rule-based chưa thay thế human review.

## 11. Next steps

- Review thủ công output test.
- Chạy thêm evaluation cases.
- So sánh prompt_v2 với QLoRA.
- Nếu kết quả ổn, tích hợp adapter vào backend inference mode.
