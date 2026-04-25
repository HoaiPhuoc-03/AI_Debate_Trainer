from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "datasets" / "debate_cer_v1_1000.jsonl"
TOLERANCE = 0.01

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INPUT_REQUIRED = {
    "topic",
    "stance",
    "difficulty",
    "age_group",
    "debate_level",
    "language",
    "user_argument",
}
OUTPUT_REQUIRED = {"rebuttal", "cer", "feedback"}
CER_REQUIRED = {"claim", "evidence", "reasoning", "total"}
FEEDBACK_REQUIRED = {"strengths", "weaknesses", "suggestions"}
METADATA_REQUIRED = {
    "topic_category",
    "argument_quality",
    "main_weakness",
    "safety_label",
    "generation_method",
}

ENUMS = {
    "stance": {"support", "oppose", "neutral"},
    "difficulty": {"basic", "intermediate", "advanced"},
    "age_group": {"teen", "adult", "senior"},
    "debate_level": {"basic", "intermediate", "advanced"},
    "language": {"vi"},
    "topic_category": {"education", "technology_ai", "society", "environment", "economy"},
    "argument_quality": {
        "medium",
        "weak_evidence",
        "weak_reasoning",
        "vague_claim",
        "strong",
        "too_short",
        "off_topic",
        "unsafe",
    },
    "main_weakness": {"claim", "evidence", "reasoning", "safety"},
    "safety_label": {"safe", "unsafe", "needs_review"},
}


def is_non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_missing_errors(errors: list[str], line_no: int, container: dict, required: set[str], prefix: str):
    for key in sorted(required):
        if key not in container:
            errors.append(f"line {line_no}: missing {prefix}.{key}")


def validate_enum(errors: list[str], line_no: int, name: str, value):
    if value not in ENUMS[name]:
        errors.append(f"line {line_no}: invalid {name}={value!r}")


def validate_score(errors: list[str], line_no: int, cer: dict, key: str) -> float:
    value = cer.get(key)
    if not isinstance(value, (int, float)):
        errors.append(f"line {line_no}: cer.{key} must be a number")
        return 0.0
    if value < 0 or value > 10:
        errors.append(f"line {line_no}: cer.{key} out of range 0-10")
    return float(value)


def validate_sample(sample: dict, line_no: int, errors: list[str], warnings: list[str]) -> str | None:
    for key in ("id", "instruction", "input", "output", "metadata"):
        if key not in sample:
            errors.append(f"line {line_no}: missing {key}")

    if not is_non_empty_string(sample.get("id")):
        errors.append(f"line {line_no}: id must be non-empty")
    if not is_non_empty_string(sample.get("instruction")):
        errors.append(f"line {line_no}: instruction must be non-empty")

    input_data = sample.get("input")
    output = sample.get("output")
    metadata = sample.get("metadata")

    if not isinstance(input_data, dict):
        errors.append(f"line {line_no}: input must be an object")
        input_data = {}
    if not isinstance(output, dict):
        errors.append(f"line {line_no}: output must be an object")
        output = {}
    if not isinstance(metadata, dict):
        errors.append(f"line {line_no}: metadata must be an object")
        metadata = {}

    add_missing_errors(errors, line_no, input_data, INPUT_REQUIRED, "input")
    add_missing_errors(errors, line_no, output, OUTPUT_REQUIRED, "output")
    add_missing_errors(errors, line_no, metadata, METADATA_REQUIRED, "metadata")

    for key in ("stance", "difficulty", "age_group", "debate_level", "language"):
        if key in input_data:
            validate_enum(errors, line_no, key, input_data.get(key))
    for key in ("topic_category", "argument_quality", "main_weakness", "safety_label"):
        if key in metadata:
            validate_enum(errors, line_no, key, metadata.get(key))

    if not is_non_empty_string(input_data.get("topic")):
        errors.append(f"line {line_no}: input.topic must be non-empty")
    if not is_non_empty_string(input_data.get("user_argument")):
        errors.append(f"line {line_no}: input.user_argument must be non-empty")
    if not is_non_empty_string(output.get("rebuttal")):
        errors.append(f"line {line_no}: output.rebuttal must be non-empty")
    if not is_non_empty_string(metadata.get("generation_method")):
        errors.append(f"line {line_no}: metadata.generation_method must be non-empty")
    elif not str(metadata.get("generation_method")).startswith("template_synthetic_v1"):
        warnings.append(f"line {line_no}: generation_method is not template_synthetic_v1 family")

    cer = output.get("cer")
    if not isinstance(cer, dict):
        errors.append(f"line {line_no}: output.cer must be an object")
        cer = {}
    add_missing_errors(errors, line_no, cer, CER_REQUIRED, "output.cer")
    claim = validate_score(errors, line_no, cer, "claim")
    evidence = validate_score(errors, line_no, cer, "evidence")
    reasoning = validate_score(errors, line_no, cer, "reasoning")
    total = validate_score(errors, line_no, cer, "total")
    expected_total = round((claim + evidence + reasoning) / 3, 2)
    if abs(total - expected_total) > TOLERANCE:
        errors.append(
            f"line {line_no}: cer.total={total} does not match expected {expected_total}"
        )

    feedback = output.get("feedback")
    if not isinstance(feedback, dict):
        errors.append(f"line {line_no}: output.feedback must be an object")
        feedback = {}
    add_missing_errors(errors, line_no, feedback, FEEDBACK_REQUIRED, "output.feedback")
    for key in sorted(FEEDBACK_REQUIRED):
        value = feedback.get(key)
        if not isinstance(value, list):
            errors.append(f"line {line_no}: feedback.{key} must be a list")
        elif not value or not all(is_non_empty_string(item) for item in value):
            errors.append(f"line {line_no}: feedback.{key} must contain non-empty strings")

    return input_data.get("user_argument") if isinstance(input_data.get("user_argument"), str) else None


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    ids = Counter()
    arguments = Counter()
    line_errors = defaultdict(list)
    total_samples = 0

    if not DATASET_PATH.exists():
        print(f"Dataset not found: {DATASET_PATH}")
        return 1

    with DATASET_PATH.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                warnings.append(f"line {line_no}: blank line")
                continue
            total_samples += 1
            before_error_count = len(errors)
            try:
                sample = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON: {exc}")
                line_errors[line_no].append(str(exc))
                continue
            if not isinstance(sample, dict):
                errors.append(f"line {line_no}: sample must be a JSON object")
                continue

            sample_id = sample.get("id")
            if isinstance(sample_id, str):
                ids[sample_id] += 1
            argument = validate_sample(sample, line_no, errors, warnings)
            if argument:
                arguments[" ".join(argument.split()).casefold()] += 1
            for error in errors[before_error_count:]:
                line_errors[line_no].append(error)

    duplicate_ids = sorted(sample_id for sample_id, count in ids.items() if count > 1)
    for sample_id in duplicate_ids:
        errors.append(f"duplicate id: {sample_id}")

    duplicate_arguments = {
        argument: count for argument, count in arguments.items() if count > 1
    }
    repeated_too_much = {
        argument: count for argument, count in duplicate_arguments.items() if count > 5
    }
    for argument, count in sorted(repeated_too_much.items(), key=lambda item: item[1], reverse=True)[:20]:
        warnings.append(f"user_argument repeated {count} times: {argument[:120]}")

    invalid_lines = set(line_errors)
    valid_samples = total_samples - len(invalid_lines)

    print("Dataset validation report")
    print(f"- total samples: {total_samples}")
    print(f"- valid samples: {valid_samples}")
    print(f"- invalid samples: {len(invalid_lines)}")
    print(f"- duplicate ids: {len(duplicate_ids)}")
    print(f"- duplicate arguments: {len(duplicate_arguments)}")
    print(f"- warnings: {len(warnings)}")
    print(f"- errors: {len(errors)}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings[:50]:
            print(f"  - {warning}")
        if len(warnings) > 50:
            print(f"  ... {len(warnings) - 50} more warnings")

    if errors:
        print("\nErrors by line:")
        for line_no in sorted(line_errors):
            for error in line_errors[line_no]:
                print(f"  - {error}")
        for error in errors:
            if error.startswith("duplicate id"):
                print(f"  - {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
