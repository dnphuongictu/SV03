"""
Evaluate v6 predictions after downloading from Kaggle.

Usage:
    python src/evaluate_v6.py

Reads from  prototype/results/
  external_prompt_patch/hybrid_k5_external_predictions.jsonl
  v6_external_robust/external_hybrid_k5_predictions.jsonl
  v6_external_robust/external_no_retrieval_predictions.jsonl
  v6_external_robust/final48_hybrid_k5_predictions.jsonl

Saves reports to same directories (replaces _predictions with _report).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

RESULTS = ROOT / "results"

CONFIGS = [
    # (label, predictions_path, eval_path, out_report_path, baseline_e2e)
    (
        "Phase A: patch+hybrid (external)",
        RESULTS / "external_prompt_patch" / "hybrid_k5_external_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_external_test.jsonl",
        RESULTS / "external_prompt_patch" / "hybrid_k5_external_report.json",
        0.5556,
    ),
    (
        "C1: v6+hybrid (external)",
        RESULTS / "v6_external_robust" / "external_hybrid_k5_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_external_test.jsonl",
        RESULTS / "v6_external_robust" / "external_hybrid_k5_report.json",
        0.5556,
    ),
    (
        "C2: v6+no_retrieval (external)",
        RESULTS / "v6_external_robust" / "external_no_retrieval_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_external_test.jsonl",
        RESULTS / "v6_external_robust" / "external_no_retrieval_report.json",
        0.4167,
    ),
    (
        "C3: v6+hybrid (final48)",
        RESULTS / "v6_external_robust" / "final48_hybrid_k5_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_final48.jsonl",
        RESULTS / "v6_external_robust" / "final48_hybrid_k5_report.json",
        0.7500,
    ),
    # v7 (populated after Kaggle run)
    (
        "C1: v7+hybrid (external)",
        RESULTS / "v7" / "external_hybrid_k5_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_external_test.jsonl",
        RESULTS / "v7" / "external_hybrid_k5_report.json",
        0.6250,
    ),
    (
        "C2: v7+no_retrieval (external)",
        RESULTS / "v7" / "external_no_retrieval_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_external_test.jsonl",
        RESULTS / "v7" / "external_no_retrieval_report.json",
        0.4444,
    ),
    (
        "C3: v7+hybrid (final48)",
        RESULTS / "v7" / "final48_hybrid_k5_predictions.jsonl",
        ROOT / "data/eval/vi_droidcall_final48.jsonl",
        RESULTS / "v7" / "final48_hybrid_k5_report.json",
        0.7292,
    ),
]


def main() -> None:
    print("=" * 68)
    print("v6 External-Robust Evaluation")
    print("=" * 68)
    print(f"{'Config':<40} {'ToolAcc':>8} {'E2E':>8}  {'CI-95':<18}  {'Delta-E2E'}")
    print("-" * 68)

    for label, pred_path, eval_path, out_path, baseline in CONFIGS:
        if not pred_path.exists():
            print(f"  {label:<38}  MISSING: {pred_path.name}")
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        report = evaluate(eval_path=eval_path, predictions_path=pred_path)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        ta    = report["tool_selection_accuracy"]
        e2e   = report["end_to_end_task_success"]
        ci    = report.get("end_to_end_ci_95", "")
        delta = e2e - baseline
        print(f"  {label:<40} {ta:>6.4f}  {e2e:>6.4f}  {ci:<18}  {delta:+.4f}")

    print()
    print("Decision gate (v6 keep criteria):")
    print("  external hybrid E2E >= 0.65  AND  final48 hybrid E2E >= 0.72")
    print()
    print("Baselines (v4_final):")
    print("  external hybrid : E2E=0.5556  [0.474, 0.634]")
    print("  final48 hybrid  : E2E=0.7500  [0.612, 0.851]")


if __name__ == "__main__":
    main()
