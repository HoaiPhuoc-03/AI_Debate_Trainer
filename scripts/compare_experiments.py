from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]
EXPERIMENTS_DIR = ROOT_DIR / "experiments"
CRITERIA_COLUMNS = [
    ("Format", "format_valid"),
    ("Rebuttal", "has_rebuttal"),
    ("CER", "has_valid_cer"),
    ("Feedback", "has_feedback"),
    ("Aligned", "feedback_aligned"),
    ("Word Limit", "within_word_limit"),
    ("Language", "language_valid"),
]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_reports() -> list[dict[str, Any]]:
    reports = []
    if not EXPERIMENTS_DIR.exists():
        return reports
    for path in sorted(EXPERIMENTS_DIR.glob("*_report.json")):
        try:
            report = json.loads(path.read_text(encoding="utf-8"))
            report["_path"] = str(path)
            reports.append(report)
        except json.JSONDecodeError:
            print(f"Skipping invalid report: {path}")
    return reports


def print_table(rows: list[list[str]]) -> None:
    widths = [max(len(row[index]) for row in rows) for index in range(len(rows[0]))]
    for index, row in enumerate(rows):
        print(" | ".join(value.ljust(widths[column]) for column, value in enumerate(row)))
        if index == 0:
            print("-+-".join("-" * width for width in widths))


def main() -> int:
    reports = load_reports()
    if not reports:
        print("No experiment reports found.")
        print("Run:")
        print("  python scripts/run_evaluation.py --name mock_eval --mode mock")
        print("  python scripts/evaluate_outputs.py --input experiments/mock_eval_outputs.jsonl")
        return 0

    header = ["Experiment", "Cases", "Avg Score", "Pass Rate"] + [label for label, _ in CRITERIA_COLUMNS]
    rows = [header]
    for report in reports:
        summary = report.get("criteria_summary", {})
        rows.append(
            [
                str(report.get("experiment_name", "")),
                str(report.get("total_cases", 0)),
                f"{float(report.get('average_score', 0)):.2f}",
                f"{float(report.get('pass_rate', 0)) * 100:.1f}%",
                *[str(summary.get(key, 0)) for _, key in CRITERIA_COLUMNS],
            ]
        )

    print_table(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
