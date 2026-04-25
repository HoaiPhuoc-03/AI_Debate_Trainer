from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT_DIR / "datasets"
MAIN_DATASET = DATASET_DIR / "debate_cer_v1_1000.jsonl"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SPLITS = {
    "train": DATASET_DIR / "train.jsonl",
    "dev": DATASET_DIR / "dev.jsonl",
    "test": DATASET_DIR / "test.jsonl",
}


def load_ids(path: Path, id_key: str = "id") -> list[str]:
    ids = []
    with path.open("r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: line {line_no}: invalid JSON: {exc}") from exc
            if id_key not in item:
                raise ValueError(f"{path}: line {line_no}: missing {id_key}")
            ids.append(str(item[id_key]))
    return ids


def main() -> int:
    errors = []
    main_ids = set(load_ids(MAIN_DATASET))
    split_ids = {}
    all_split_ids = []

    for name, path in SPLITS.items():
        ids = load_ids(path)
        split_ids[name] = ids
        all_split_ids.extend(ids)

    counts = {name: len(ids) for name, ids in split_ids.items()}
    total_split_count = len(all_split_ids)
    duplicate_ids = sorted(item for item, count in Counter(all_split_ids).items() if count > 1)
    missing_ids = sorted(main_ids - set(all_split_ids))
    extra_ids = sorted(set(all_split_ids) - main_ids)

    if counts["train"] != 800:
        errors.append(f"train count expected 800, got {counts['train']}")
    if counts["dev"] != 100:
        errors.append(f"dev count expected 100, got {counts['dev']}")
    if counts["test"] != 100:
        errors.append(f"test count expected 100, got {counts['test']}")
    if total_split_count != 1000:
        errors.append(f"total split count expected 1000, got {total_split_count}")
    if duplicate_ids:
        errors.append(f"duplicate ids across splits: {len(duplicate_ids)}")
    if missing_ids:
        errors.append(f"missing ids from splits: {len(missing_ids)}")
    if extra_ids:
        errors.append(f"extra ids not in main dataset: {len(extra_ids)}")

    print("Dataset split report")
    print(f"- train count: {counts['train']}")
    print(f"- dev count: {counts['dev']}")
    print(f"- test count: {counts['test']}")
    print(f"- total split count: {total_split_count}")
    print(f"- duplicate ids across splits: {len(duplicate_ids)}")
    print(f"- missing ids: {len(missing_ids)}")
    print(f"- extra ids: {len(extra_ids)}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
