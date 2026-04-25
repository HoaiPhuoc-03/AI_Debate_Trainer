from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = ROOT_DIR / "datasets" / "debate_cer_v1_1000.jsonl"
OUTPUT_PATH = ROOT_DIR / "datasets" / "dataset_stats_generated.json"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                yield json.loads(line)


def average(values: list[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def main() -> int:
    topic_category = Counter()
    age_group = Counter()
    difficulty = Counter()
    debate_level = Counter()
    argument_quality = Counter()
    main_weakness = Counter()
    safety_label = Counter()
    claim_scores = []
    evidence_scores = []
    reasoning_scores = []
    total_scores = []

    samples = list(load_jsonl(DATASET_PATH))
    for sample in samples:
        input_data = sample.get("input", {})
        output = sample.get("output", {})
        metadata = sample.get("metadata", {})
        cer = output.get("cer", {})

        topic_category[metadata.get("topic_category", "missing")] += 1
        age_group[input_data.get("age_group", "missing")] += 1
        difficulty[input_data.get("difficulty", "missing")] += 1
        debate_level[input_data.get("debate_level", "missing")] += 1
        argument_quality[metadata.get("argument_quality", "missing")] += 1
        main_weakness[metadata.get("main_weakness", "missing")] += 1
        safety_label[metadata.get("safety_label", "missing")] += 1

        claim_scores.append(float(cer.get("claim", 0)))
        evidence_scores.append(float(cer.get("evidence", 0)))
        reasoning_scores.append(float(cer.get("reasoning", 0)))
        total_scores.append(float(cer.get("total", 0)))

    stats = {
        "total_samples": len(samples),
        "by_topic_category": dict(topic_category),
        "by_age_group": dict(age_group),
        "by_difficulty": dict(difficulty),
        "by_debate_level": dict(debate_level),
        "by_argument_quality": dict(argument_quality),
        "by_main_weakness": dict(main_weakness),
        "by_safety_label": dict(safety_label),
        "avg_cer": {
            "avg_claim": average(claim_scores),
            "avg_evidence": average(evidence_scores),
            "avg_reasoning": average(reasoning_scores),
            "avg_total": average(total_scores),
        },
        "min_max_cer": {
            "min_total": min(total_scores) if total_scores else 0.0,
            "max_total": max(total_scores) if total_scores else 0.0,
        },
    }

    print("Dataset statistics")
    print(f"- total samples: {stats['total_samples']}")
    for key in (
        "by_topic_category",
        "by_age_group",
        "by_difficulty",
        "by_debate_level",
        "by_argument_quality",
        "by_main_weakness",
        "by_safety_label",
    ):
        print(f"- {key}: {stats[key]}")
    print(f"- average CER: {stats['avg_cer']}")
    print(f"- min/max total CER: {stats['min_max_cer']}")

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump(stats, file, ensure_ascii=False, indent=2)
        file.write("\n")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
