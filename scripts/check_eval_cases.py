from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT_DIR / "datasets" / "eval_cases_v1.jsonl"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOPIC_CATEGORIES = {"education", "technology_ai", "society", "environment", "economy"}
ARGUMENT_QUALITIES = {
    "medium",
    "weak_evidence",
    "weak_reasoning",
    "vague_claim",
    "strong",
    "too_short",
    "off_topic",
    "unsafe",
}
FOCUS_VALUES = {"format", "evidence", "reasoning", "safety", "age_tone"}
REQUIRED_TOP_LEVEL = {
    "case_id",
    "topic",
    "stance",
    "difficulty",
    "age_group",
    "debate_level",
    "language",
    "user_argument",
    "expected",
    "metadata",
}
REQUIRED_EXPECTED = {
    "must_have_rebuttal",
    "must_have_cer",
    "must_have_feedback",
    "max_words",
}
REQUIRED_METADATA = {"topic_category", "argument_quality", "focus"}


def main() -> int:
    errors = []
    line_errors = defaultdict(list)
    ids = Counter()
    total_cases = 0

    with EVAL_PATH.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue
            total_cases += 1
            before = len(errors)
            try:
                case = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                continue
            if not isinstance(case, dict):
                errors.append(f"line {line_no}: case must be an object")
                continue

            for key in sorted(REQUIRED_TOP_LEVEL):
                if key not in case:
                    errors.append(f"line {line_no}: missing {key}")

            case_id = case.get("case_id")
            if isinstance(case_id, str) and case_id.strip():
                ids[case_id] += 1
            else:
                errors.append(f"line {line_no}: case_id must be non-empty")

            expected = case.get("expected")
            if not isinstance(expected, dict):
                errors.append(f"line {line_no}: expected must be an object")
                expected = {}
            for key in sorted(REQUIRED_EXPECTED):
                if key not in expected:
                    errors.append(f"line {line_no}: missing expected.{key}")
            if not isinstance(expected.get("max_words"), int) or expected.get("max_words", 0) <= 0:
                errors.append(f"line {line_no}: expected.max_words must be a positive integer")

            metadata = case.get("metadata")
            if not isinstance(metadata, dict):
                errors.append(f"line {line_no}: metadata must be an object")
                metadata = {}
            for key in sorted(REQUIRED_METADATA):
                if key not in metadata:
                    errors.append(f"line {line_no}: missing metadata.{key}")
            if metadata.get("topic_category") not in TOPIC_CATEGORIES:
                errors.append(f"line {line_no}: invalid metadata.topic_category")
            if metadata.get("argument_quality") not in ARGUMENT_QUALITIES:
                errors.append(f"line {line_no}: invalid metadata.argument_quality")
            if metadata.get("focus") not in FOCUS_VALUES:
                errors.append(f"line {line_no}: invalid metadata.focus")

            for error in errors[before:]:
                line_errors[line_no].append(error)

    duplicate_ids = sorted(case_id for case_id, count in ids.items() if count > 1)
    for case_id in duplicate_ids:
        errors.append(f"duplicate case_id: {case_id}")

    print("Eval cases report")
    print(f"- total eval cases: {total_cases}")
    print(f"- duplicate case_id: {len(duplicate_ids)}")
    print(f"- errors: {len(errors)}")

    if errors:
        print("\nErrors:")
        for line_no in sorted(line_errors):
            for error in line_errors[line_no]:
                print(f"  - {error}")
        for error in errors:
            if error.startswith("duplicate case_id"):
                print(f"  - {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
