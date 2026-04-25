# AI Debate Trainer Debate-CER Synthetic Dataset v1

Dataset này dùng để chuẩn bị cho evaluation và fine-tuning/QLoRA của hệ thống AI Debate Trainer. Dữ liệu tập trung vào bài toán phản biện lập luận, chấm điểm CER và đưa feedback cải thiện.

## Files

- `debate_cer_v1_1000.jsonl`: dataset chính gồm 1000 mẫu.
- `train.jsonl`: split huấn luyện.
- `dev.jsonl`: split phát triển/validation.
- `test.jsonl`: split kiểm thử.
- `topic_bank.json`: ngân hàng chủ đề và nhóm chủ đề.
- `eval_cases_v1.jsonl`: các case evaluation cố định cho phase 3.
- `dataset_stats.json`: thống kê đi kèm dataset gốc.
- `dataset_stats_generated.json`: thống kê sinh lại bằng script local.

## Sample Schema

Mỗi dòng trong file JSONL là một JSON object:

```json
{
  "id": "EDU_TEEN_0001",
  "instruction": "Bạn là AI Debate Trainer...",
  "input": {
    "topic": "...",
    "stance": "support|oppose|neutral",
    "difficulty": "basic|intermediate|advanced",
    "age_group": "teen|adult|senior",
    "debate_level": "basic|intermediate|advanced",
    "language": "vi",
    "user_argument": "..."
  },
  "output": {
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
  },
  "metadata": {
    "topic_category": "education|technology_ai|society|environment|economy",
    "argument_quality": "medium|weak_evidence|weak_reasoning|vague_claim|strong|too_short|off_topic|unsafe",
    "main_weakness": "claim|evidence|reasoning|safety",
    "safety_label": "safe|unsafe|needs_review",
    "generation_method": "template_synthetic_v1"
  }
}
```

## Commands

Validate dataset:

```powershell
python scripts/validate_dataset.py
```

Generate statistics:

```powershell
python scripts/dataset_stats.py
```

Check train/dev/test split:

```powershell
python scripts/check_dataset_split.py
```

Check evaluation cases:

```powershell
python scripts/check_eval_cases.py
```

## Important Notes

- Dataset hiện là synthetic template-generated v1.
- Dataset phù hợp để test pipeline và chuẩn bị QLoRA.
- Trước khi train thật, cần review thủ công một phần dữ liệu.
- Nên review kỹ test set, các mẫu `unsafe`, `off_topic`, và `too_short`.
- Không nên tuyên bố đây là dataset gán nhãn thủ công hoàn toàn.

## Suggested Report Wording

“Dataset được xây dựng theo phương pháp bán tự động, dựa trên topic bank, rubric CER và template phản biện; sau đó được kiểm tra bằng script validate và review thủ công một phần.”
