from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "datasets"

SPLITS = {
    "train": (DATASET_DIR / "train.jsonl", DATASET_DIR / "sft_train.jsonl"),
    "dev": (DATASET_DIR / "dev.jsonl", DATASET_DIR / "sft_dev.jsonl"),
    "test": (DATASET_DIR / "test.jsonl", DATASET_DIR / "sft_test.jsonl"),
}

SYSTEM_PROMPT = (
    "Bạn là AI Debate Trainer. Luôn phản biện lập luận của người dùng, "
    "chấm CER theo Claim-Evidence-Reasoning và đưa feedback cải thiện bằng tiếng Việt. "
    "Trả lời đúng format [REBUTTAL], [CER], [FEEDBACK]."
)

INPUT_REQUIRED = {
    "topic",
    "stance",
    "difficulty",
    "age_group",
    "debate_level",
    "language",
    "user_argument",
}
CER_REQUIRED = {"claim", "evidence", "reasoning", "total"}
FEEDBACK_REQUIRED = {"strengths", "weaknesses", "suggestions"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def has_required_fields(sample: dict[str, Any], split: str, line_no: int) -> bool:
    sample_id = sample.get("id", f"{split}:{line_no}")
    input_data = sample.get("input")
    output = sample.get("output")

    if not isinstance(input_data, dict):
        warn(f"{split} line {line_no} ({sample_id}): missing or invalid input")
        return False
    if not isinstance(output, dict):
        warn(f"{split} line {line_no} ({sample_id}): missing or invalid output")
        return False

    missing_input = sorted(key for key in INPUT_REQUIRED if key not in input_data)
    if missing_input:
        warn(f"{split} line {line_no} ({sample_id}): missing input fields {missing_input}")
        return False

    cer = output.get("cer")
    feedback = output.get("feedback")
    if not isinstance(output.get("rebuttal"), str) or not output.get("rebuttal", "").strip():
        warn(f"{split} line {line_no} ({sample_id}): missing output.rebuttal")
        return False
    if not isinstance(cer, dict):
        warn(f"{split} line {line_no} ({sample_id}): missing or invalid output.cer")
        return False
    if not isinstance(feedback, dict):
        warn(f"{split} line {line_no} ({sample_id}): missing or invalid output.feedback")
        return False

    missing_cer = sorted(key for key in CER_REQUIRED if key not in cer)
    missing_feedback = sorted(key for key in FEEDBACK_REQUIRED if key not in feedback)
    if missing_cer:
        warn(f"{split} line {line_no} ({sample_id}): missing CER fields {missing_cer}")
        return False
    if missing_feedback:
        warn(f"{split} line {line_no} ({sample_id}): missing feedback fields {missing_feedback}")
        return False

    for key in FEEDBACK_REQUIRED:
        if not isinstance(feedback.get(key), list):
            warn(f"{split} line {line_no} ({sample_id}): feedback.{key} must be a list")
            return False
    return True


def format_bullets(items: list[Any]) -> str:
    clean_items = [str(item).strip() for item in items if str(item).strip()]
    if not clean_items:
        return "- Không có nội dung."
    return "\n".join(f"- {item}" for item in clean_items)


def build_user_content(input_data: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Chủ đề: {input_data.get('topic', '')}",
            f"Lập trường người dùng: {input_data.get('stance', '')}",
            f"Độ khó: {input_data.get('difficulty', '')}",
            f"Nhóm tuổi: {input_data.get('age_group', '')}",
            f"Trình độ: {input_data.get('debate_level', '')}",
            f"Lập luận người dùng: {input_data.get('user_argument', '')}",
        ]
    )


def build_assistant_content(output: dict[str, Any]) -> str:
    cer = output["cer"]
    feedback = output["feedback"]
    return "\n".join(
        [
            "[REBUTTAL]",
            str(output["rebuttal"]).strip(),
            "",
            "[CER]",
            f"Claim: {cer['claim']}",
            f"Evidence: {cer['evidence']}",
            f"Reasoning: {cer['reasoning']}",
            "",
            "[FEEDBACK]",
            "Strengths:",
            format_bullets(feedback["strengths"]),
            "Weaknesses:",
            format_bullets(feedback["weaknesses"]),
            "Suggestions:",
            format_bullets(feedback["suggestions"]),
        ]
    )


def convert_sample(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_user_content(sample["input"]),
            },
            {
                "role": "assistant",
                "content": build_assistant_content(sample["output"]),
            },
        ]
    }


def convert_split(split: str, input_path: Path, output_path: Path) -> tuple[int, int]:
    converted = 0
    skipped = 0

    if not input_path.exists():
        raise FileNotFoundError(f"Missing input split: {input_path}")

    with input_path.open("r", encoding="utf-8") as input_file, output_path.open("w", encoding="utf-8") as output_file:
        for line_no, line in enumerate(input_file, start=1):
            if not line.strip():
                continue
            try:
                sample = json.loads(line)
            except json.JSONDecodeError as exc:
                warn(f"{split} line {line_no}: invalid JSON: {exc}")
                skipped += 1
                continue

            if not isinstance(sample, dict):
                warn(f"{split} line {line_no}: sample must be a JSON object")
                skipped += 1
                continue
            if not has_required_fields(sample, split, line_no):
                skipped += 1
                continue

            output_file.write(json.dumps(convert_sample(sample), ensure_ascii=False) + "\n")
            converted += 1

    return converted, skipped


def main() -> int:
    total_converted = 0
    total_skipped = 0

    for split, (input_path, output_path) in SPLITS.items():
        try:
            converted, skipped = convert_split(split, input_path, output_path)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        total_converted += converted
        total_skipped += skipped
        print(f"{split}: converted={converted}, skipped={skipped}, output={output_path}")

    print(f"Total converted: {total_converted}")
    print(f"Total skipped: {total_skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
