"""
B1: Classical baseline — TF-IDF char n-gram + Logistic Regression
for tool routing on ViDroidCall.

Answers: "Why do we need an SLM? Can a simple classifier suffice?"

Trains on train191_final, evaluates on final48.
Reports ToolAcc (tool routing only); E2E is not achievable because
the classifier cannot extract typed arguments.

Usage:
  python src/classical_baseline.py [--output results/rescored/classical_baseline_report.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from common import load_jsonl, ROOT

TRAIN_PATH = ROOT / "data" / "eval" / "vi_droidcall_train191_final.jsonl"
EVAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_final48.jsonl"

NULL_LABEL = "__NULL__"


def _wilson_ci(success: int, total: int, z: float = 1.96) -> str:
    if total == 0:
        return "N/A"
    p = success / total
    denom = 1 + z**2 / total
    centre = (p + z**2 / (2 * total)) / denom
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * total)) / total) / denom
    return f"[{max(0.0, centre - margin):.3f}, {min(1.0, centre + margin):.3f}]"


def tool_label(expected: dict) -> str:
    t = expected.get("tool")
    return NULL_LABEL if t is None else str(t)


def run(train_path: Path, eval_path: Path, output: Path | None) -> dict:
    train_data = load_jsonl(train_path)
    eval_data = load_jsonl(eval_path)

    train_queries = [r["query"] for r in train_data]
    train_labels = [tool_label(r["expected"]) for r in train_data]

    eval_queries = [r["query"] for r in eval_data]
    eval_labels = [tool_label(r["expected"]) for r in eval_data]
    eval_ids = [r["id"] for r in eval_data]
    eval_groups = [r.get("group", "unknown") for r in eval_data]

    # Two feature sets: char n-grams + word n-grams, then vote via soft proba
    char_pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4),
            min_df=1, max_features=15000, sublinear_tf=True,
        )),
        ("clf", LogisticRegression(C=2.0, max_iter=2000, solver="lbfgs")),
    ])
    word_pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, max_features=8000, sublinear_tf=True,
        )),
        ("clf", LogisticRegression(C=2.0, max_iter=2000, solver="lbfgs")),
    ])

    char_pipe.fit(train_queries, train_labels)
    word_pipe.fit(train_queries, train_labels)

    classes = char_pipe.classes_
    char_proba = char_pipe.predict_proba(eval_queries)
    word_proba = word_pipe.predict_proba(eval_queries)

    # Align class order (both should be same after fit on same labels)
    word_classes = word_pipe.classes_
    if list(classes) == list(word_classes):
        combined = 0.5 * char_proba + 0.5 * word_proba
    else:
        combined = char_proba  # fallback

    pred_indices = np.argmax(combined, axis=1)
    predictions = [classes[i] for i in pred_indices]

    # === Metrics ===
    correct_tool = [p == g for p, g in zip(predictions, eval_labels)]
    tool_acc = sum(correct_tool) / len(correct_tool)

    # Group breakdown
    group_counts: dict[str, dict] = defaultdict(lambda: {"count": 0, "tool_correct": 0})
    for i, grp in enumerate(eval_groups):
        group_counts[grp]["count"] += 1
        if correct_tool[i]:
            group_counts[grp]["tool_correct"] += 1

    # Null class
    null_indices = [i for i, l in enumerate(eval_labels) if l == NULL_LABEL]
    pos_indices = [i for i, l in enumerate(eval_labels) if l != NULL_LABEL]

    null_tool_acc = (
        sum(correct_tool[i] for i in null_indices) / len(null_indices)
        if null_indices else None
    )
    pos_tool_acc = (
        sum(correct_tool[i] for i in pos_indices) / len(pos_indices)
        if pos_indices else None
    )

    # per_example (no E2E possible — classifier cannot extract typed arguments)
    per_example = [
        {
            "id": eval_ids[i],
            "tool_correct": correct_tool[i],
            "arguments_exact": False,  # not applicable
            "schema_valid": False,      # not applicable
            "status_correct": correct_tool[i] if eval_labels[i] == NULL_LABEL else True,
            "confirmation_correct": False,  # not applicable
            "end_to_end": False,  # cannot do E2E without argument extraction
        }
        for i in range(len(eval_data))
    ]

    report = {
        "model": "TF-IDF char(2-4)+word(1-2) ensemble + LogisticRegression (C=2)",
        "train_path": str(train_path),
        "eval_path": str(eval_path),
        "count": len(eval_data),
        "tool_selection_accuracy": tool_acc,
        "tool_selection_accuracy_ci_95": _wilson_ci(sum(correct_tool), len(correct_tool)),
        "tool_acc_null_class": null_tool_acc,
        "tool_acc_positive_class": pos_tool_acc,
        "schema_valid_rate": "N/A — no argument extraction",
        "end_to_end_task_success": "N/A — no argument extraction",
        "note": (
            "Classical baseline provides tool routing only. "
            "It cannot extract typed arguments (integers, URIs, phone numbers), "
            "so E2E success is not achievable. This motivates the SLM approach."
        ),
        "groups": {
            grp: {
                "count": v["count"],
                "tool_selection_accuracy": v["tool_correct"] / v["count"],
            }
            for grp, v in sorted(group_counts.items())
        },
        "per_example": per_example,
        "sklearn_report": classification_report(
            eval_labels, predictions, zero_division=0
        ),
    }

    print("=" * 60)
    print("B1: Classical Baseline — TF-IDF + LogReg")
    print("=" * 60)
    print(f"  Train: {len(train_data)} samples ({len(set(train_labels))} classes)")
    print(f"  Eval:  {len(eval_data)} samples")
    print()
    print(f"  ToolAcc (all):      {tool_acc:.4f}  {_wilson_ci(sum(correct_tool), len(correct_tool))}")
    print(f"  ToolAcc (null, n={len(null_indices)}):  {null_tool_acc:.4f}" if null_tool_acc is not None else "  ToolAcc (null): N/A")
    print(f"  ToolAcc (pos,  n={len(pos_indices)}):  {pos_tool_acc:.4f}" if pos_tool_acc is not None else "  ToolAcc (pos): N/A")
    print()
    print("  Per-group ToolAcc:")
    for grp, v in sorted(group_counts.items()):
        print(f"    {grp:<25}: {v['tool_correct']}/{v['count']} = {v['tool_correct']/v['count']:.3f}")
    print()
    print("  E2E: NOT APPLICABLE — classifier cannot extract typed arguments")
    print()
    print("  Classification report (tool routing):")
    print(report["sklearn_report"])

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        report_serializable = {k: v for k, v in report.items() if k != "sklearn_report"}
        report_serializable["sklearn_report"] = report["sklearn_report"]
        output.write_text(
            json.dumps(report_serializable, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  Saved: {output}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/rescored/classical_baseline_report.json"),
    )
    args = parser.parse_args()
    run(TRAIN_PATH, EVAL_PATH, args.output)


if __name__ == "__main__":
    main()
