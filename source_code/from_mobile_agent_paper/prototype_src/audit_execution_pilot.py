"""Audit the locked Android execution pilot against development/eval queries."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "ondevice" / "execution_pilot_v1.json"
DEFAULT_OUTPUT = (
    ROOT / "results" / "execution_pilot_v1_20260627" / "protocol_audit.json"
)
SOURCES = {
    "v21_train239": ROOT / "data" / "eval" / "vi_droidcall_train239.jsonl",
    "v8_train408": ROOT / "data" / "eval" / "vi_droidcall_train408_v8.jsonl",
    "fresh_locked126": (
        ROOT / "data" / "eval" / "vi_droidcall_fresh_test_locked_20260626.jsonl"
    ),
}


def configure_console() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def normalize(text: str) -> str:
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"\s+", " ", text.lower().strip())


def trigrams(text: str) -> set[str]:
    value = normalize(text)
    if len(value) < 3:
        return {value}
    return {value[index : index + 3] for index in range(len(value) - 2)}


def jaccard(left: str, right: str) -> float:
    a, b = trigrams(left), trigrams(right)
    return len(a & b) / len(a | b) if a or b else 1.0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def query_from(row: dict[str, Any]) -> str:
    return str(row.get("query") or row.get("input") or "")


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    tasks_path = args.tasks.resolve()
    protocol = json.loads(tasks_path.read_text(encoding="utf-8"))
    source_rows = {}
    for label, path in SOURCES.items():
        if not path.is_file():
            raise SystemExit(f"Missing audit source {label}: {path}")
        source_rows[label] = load_jsonl(path)

    rows = []
    exact_count = 0
    high_sequence_count = 0
    high_jaccard_count = 0
    for task in protocol["tasks"]:
        query = task["query"]
        best: dict[str, Any] | None = None
        exact_hits = []
        for source, examples in source_rows.items():
            for example in examples:
                candidate = query_from(example)
                sequence = SequenceMatcher(
                    None,
                    normalize(query),
                    normalize(candidate),
                ).ratio()
                char_jaccard = jaccard(query, candidate)
                exact = normalize(query) == normalize(candidate)
                comparison = {
                    "source": source,
                    "source_id": example.get("id"),
                    "source_query": candidate,
                    "exact_normalized": exact,
                    "sequence_ratio": round(sequence, 6),
                    "char3_jaccard": round(char_jaccard, 6),
                }
                if exact:
                    exact_hits.append(comparison)
                if best is None or (
                    sequence,
                    char_jaccard,
                ) > (
                    best["sequence_ratio"],
                    best["char3_jaccard"],
                ):
                    best = comparison
        exact_count += int(bool(exact_hits))
        high_sequence_count += int(
            best is not None and best["sequence_ratio"] >= 0.90
        )
        high_jaccard_count += int(
            best is not None and best["char3_jaccard"] >= 0.70
        )
        rows.append(
            {
                "id": task["id"],
                "query": query,
                "exact_hits": exact_hits,
                "best_match": best,
            }
        )

    report = {
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": sha256_file(tasks_path),
        "task_count": len(protocol["tasks"]),
        "sources": {
            label: {
                "path": str(path),
                "sha256": sha256_file(path),
                "count": len(source_rows[label]),
            }
            for label, path in SOURCES.items()
        },
        "thresholds": {
            "sequence_ratio": 0.90,
            "char3_jaccard": 0.70,
        },
        "summary": {
            "exact_normalized_overlap_tasks": exact_count,
            "high_sequence_match_tasks": high_sequence_count,
            "high_char3_jaccard_tasks": high_jaccard_count,
            "interpretation": (
                "This pilot measures execution feasibility rather than an "
                "unbiased model-generalization estimate. Similarities are "
                "reported for transparency and must not be hidden."
            ),
        },
        "rows": rows,
    }
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Audit report: {output}")


if __name__ == "__main__":
    main()
