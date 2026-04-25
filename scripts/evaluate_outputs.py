from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"
EVAL_CASES_PATH = ROOT_DIR / "datasets" / "eval_cases_v1.jsonl"
PASS_THRESHOLD = 6
CRITERIA_KEYS = [
    "format_valid",
    "has_rebuttal",
    "has_valid_cer",
    "has_feedback",
    "feedback_aligned",
    "within_word_limit",
    "language_valid",
]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from app.services.evaluation import evaluate_debate_output  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                records.append(
                    {
                        "case_id": f"malformed_line_{line_no}",
                        "parsed_output": {},
                        "raw_output": "",
                        "error": f"malformed JSON output line {line_no}",
                    }
                )
    return records


def load_eval_cases() -> dict[str, dict[str, Any]]:
    cases = {}
    with EVAL_CASES_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                case = json.loads(line)
                cases[str(case.get("case_id", ""))] = case
    return cases


def experiment_name_from_input(path: Path) -> str:
    stem = path.stem
    return stem[: -len("_outputs")] if stem.endswith("_outputs") else stem


def markdown_escape(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def evaluate_records(records: list[dict[str, Any]], cases_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    for record in records:
        case_id = str(record.get("case_id", "unknown"))
        case = cases_by_id.get(case_id, {"case_id": case_id, "expected": {"max_words": 300}})
        result = evaluate_debate_output(
            case=case,
            parsed_output=record.get("parsed_output", {}),
            raw_output=record.get("raw_output", ""),
        )
        error = record.get("error", "")
        if error:
            result["score"] = min(result["score"], 1)
            result["passed"] = False
            result["notes"].append(f"generation error: {error}")
        results.append(result)
    return results


def build_report(experiment_name: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    total_cases = len(results)
    criteria_summary = {key: 0 for key in CRITERIA_KEYS}
    for result in results:
        for key, passed in result.get("criteria", {}).items():
            if key in criteria_summary and passed:
                criteria_summary[key] += 1

    average_score = round(sum(result.get("score", 0) for result in results) / total_cases, 2) if total_cases else 0
    pass_rate = round(sum(1 for result in results if result.get("passed")) / total_cases, 4) if total_cases else 0
    max_score = results[0].get("max_score", 7) if results else 7

    return {
        "experiment_name": experiment_name,
        "total_cases": total_cases,
        "average_score": average_score,
        "max_score": max_score,
        "pass_threshold": PASS_THRESHOLD,
        "pass_rate": pass_rate,
        "criteria_summary": criteria_summary,
        "case_results": results,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        f"# Evaluation Report: {report['experiment_name']}",
        "",
        f"- Total cases: {report['total_cases']}",
        f"- Average score: {report['average_score']} / {report['max_score']}",
        f"- Pass threshold: {report['pass_threshold']} / {report['max_score']}",
        f"- Pass rate: {round(report['pass_rate'] * 100, 2)}%",
        "",
        "## Criteria Summary",
        "",
        "| Criterion | Passed Cases |",
        "| --- | ---: |",
    ]
    for key in CRITERIA_KEYS:
        lines.append(f"| {key} | {report['criteria_summary'].get(key, 0)} |")

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Case ID | Score | Passed | Failed Criteria | Notes |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for result in report["case_results"]:
        failed = [
            key
            for key, passed in result.get("criteria", {}).items()
            if not passed
        ]
        notes = "; ".join(result.get("notes", []))
        lines.append(
            "| {case_id} | {score}/{max_score} | {passed} | {failed} | {notes} |".format(
                case_id=markdown_escape(result.get("case_id", "")),
                score=result.get("score", 0),
                max_score=result.get("max_score", 7),
                passed="yes" if result.get("passed") else "no",
                failed=markdown_escape(", ".join(failed) if failed else "-"),
                notes=markdown_escape(notes if notes else "-"),
            )
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate generated AI Debate Trainer outputs.")
    parser.add_argument("--input", required=True, help="Path to an *_outputs.jsonl file.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = ROOT_DIR / input_path
    if not input_path.exists():
        print(f"Missing input file: {input_path}", file=sys.stderr)
        return 1

    experiment_name = experiment_name_from_input(input_path)
    report_json_path = input_path.with_name(f"{experiment_name}_report.json")
    report_md_path = input_path.with_name(f"{experiment_name}_report.md")

    records = load_jsonl(input_path)
    cases_by_id = load_eval_cases()
    results = evaluate_records(records, cases_by_id)
    report = build_report(experiment_name, results)

    report_json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, report_md_path)

    print(f"Evaluated {report['total_cases']} cases")
    print(f"Average score: {report['average_score']} / {report['max_score']}")
    print(f"Pass rate: {round(report['pass_rate'] * 100, 2)}%")
    print(f"Wrote {report_json_path}")
    print(f"Wrote {report_md_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
