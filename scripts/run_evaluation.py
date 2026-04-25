from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
EVAL_CASES_PATH = ROOT_DIR / "datasets" / "eval_cases_v1.jsonl"
EXPERIMENTS_DIR = ROOT_DIR / "experiments"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services.output_parser import parse_debate_output  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing eval cases file: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: line {line_no}: invalid JSON: {exc}") from exc
    return records


def choose_mock_scores(case: dict[str, Any]) -> dict[str, float]:
    quality = case.get("metadata", {}).get("argument_quality", "medium")
    focus = case.get("metadata", {}).get("focus", "")
    if quality == "weak_evidence" or focus == "evidence":
        claim, evidence, reasoning = 7.0, 3.0, 6.0
    elif quality == "weak_reasoning" or focus == "reasoning":
        claim, evidence, reasoning = 7.0, 6.0, 3.0
    elif quality in {"vague_claim", "too_short", "off_topic"}:
        claim, evidence, reasoning = 3.0, 4.0, 5.0
    elif quality == "unsafe" or focus == "safety":
        claim, evidence, reasoning = 2.0, 2.0, 3.0
    elif quality == "strong":
        claim, evidence, reasoning = 8.0, 7.0, 8.0
    else:
        claim, evidence, reasoning = 6.0, 5.0, 6.0
    return {
        "claim": claim,
        "evidence": evidence,
        "reasoning": reasoning,
        "total": round((claim + evidence + reasoning) / 3, 2),
    }


def weakness_text(scores: dict[str, float]) -> tuple[str, str, str]:
    weakest = min(("claim", "evidence", "reasoning"), key=lambda key: scores[key])
    if weakest == "evidence":
        return (
            "Bằng chứng còn mỏng.",
            "Thiếu ví dụ, số liệu hoặc dẫn chứng cụ thể để bảo vệ quan điểm.",
            "Hãy thêm một ví dụ rõ ràng hoặc số liệu đáng tin cậy.",
        )
    if weakest == "reasoning":
        return (
            "Suy luận còn thiếu liên kết.",
            "Logic giữa nguyên nhân, bằng chứng và kết luận chưa đủ chặt.",
            "Hãy giải thích rõ vì sao bằng chứng dẫn tới kết luận của bạn.",
        )
    return (
        "Quan điểm chính chưa đủ sắc nét.",
        "Luận điểm hoặc lập trường còn mơ hồ, khiến phản biện dễ tấn công.",
        "Hãy viết lại ý chính thành một khẳng định cụ thể hơn.",
    )


def build_mock_raw_output(case: dict[str, Any]) -> str:
    scores = choose_mock_scores(case)
    strength, weakness, suggestion = weakness_text(scores)
    topic = case.get("topic", "chủ đề này")
    return f"""[REBUTTAL]
Tuy nhiên, lập luận của bạn về "{topic}" vẫn có điểm yếu vì nó chưa xử lý trường hợp ngoại lệ và chưa chứng minh vì sao lựa chọn đó tốt hơn các phương án khác.

[CER]
Claim: {scores["claim"]}
Evidence: {scores["evidence"]}
Reasoning: {scores["reasoning"]}

[FEEDBACK]
Strengths:
- Có nêu được hướng quan điểm chính.
Weaknesses:
- {weakness}
Suggestions:
- {suggestion}
"""


def parsed_view(parsed: dict[str, Any]) -> dict[str, Any]:
    return {
        "rebuttal": parsed.get("rebuttal", ""),
        "cer": parsed.get("cer", {"claim": 0, "evidence": 0, "reasoning": 0, "total": 0}),
        "feedback": parsed.get("feedback", {"strengths": [], "weaknesses": [], "suggestions": []}),
    }


def run_mock_case(case: dict[str, Any]) -> tuple[str, dict[str, Any], str, str, str]:
    raw_output = build_mock_raw_output(case)
    parsed = parse_debate_output(raw_output)
    return raw_output, parsed_view(parsed), "mock", "mock-structured-v1", ""


def run_live_case(case: dict[str, Any]) -> tuple[str, dict[str, Any], str, str, str]:
    try:
        from app.core.config import settings
        from app.services.ai_service import generate_debate_analysis

        analysis = generate_debate_analysis(
            topic=case.get("topic", ""),
            stance=case.get("stance", ""),
            difficulty=case.get("difficulty", ""),
            user_argument=case.get("user_argument", ""),
            age_group=case.get("age_group", "adult"),
            debate_level=case.get("debate_level", "intermediate"),
            language=case.get("language", "vi"),
        )
        return (
            analysis.get("raw_text", ""),
            parsed_view(analysis),
            "ollama",
            getattr(settings, "OLLAMA_MODEL", ""),
            analysis.get("error", ""),
        )
    except Exception as exc:
        return "", parsed_view({}), "ollama", "", str(exc)


def build_record(case: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode == "live":
        raw_output, parsed_output, provider, model, error = run_live_case(case)
    else:
        raw_output, parsed_output, provider, model, error = run_mock_case(case)

    return {
        "case_id": case.get("case_id", ""),
        "input": {
            "topic": case.get("topic", ""),
            "stance": case.get("stance", ""),
            "difficulty": case.get("difficulty", ""),
            "age_group": case.get("age_group", ""),
            "debate_level": case.get("debate_level", ""),
            "language": case.get("language", ""),
            "user_argument": case.get("user_argument", ""),
        },
        "raw_output": raw_output,
        "parsed_output": parsed_output,
        "provider": provider,
        "model": model,
        "mode": mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AI Debate Trainer evaluation cases.")
    parser.add_argument("--name", default="mock_eval", help="Experiment name.")
    parser.add_argument("--mode", choices=("mock", "live"), default="mock", help="Evaluation mode.")
    parser.add_argument("--limit", type=int, default=None, help="Optional number of cases to run.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = load_jsonl(EVAL_CASES_PATH)
    if args.limit is not None:
        cases = cases[: max(0, args.limit)]

    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EXPERIMENTS_DIR / f"{args.name}_outputs.jsonl"

    print(f"Running evaluation: name={args.name}, mode={args.mode}, cases={len(cases)}")
    with output_path.open("w", encoding="utf-8") as file:
        for index, case in enumerate(cases, start=1):
            case_id = case.get("case_id", f"case_{index}")
            print(f"[{index}/{len(cases)}] {case_id}")
            record = build_record(case, args.mode)
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
