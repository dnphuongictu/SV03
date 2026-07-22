"""
Evaluate v8 predictions after downloading from Kaggle.

Usage:
    python src/evaluate_v8.py

Reads from prototype/results/v8/
  external_hybrid_k5_predictions.jsonl
  external_no_retrieval_predictions.jsonl
  final48_hybrid_k5_predictions.jsonl

Baselines:
  v7 external hybrid K=5: ToolAcc=0.847, E2E=0.674 [0.593, 0.745]
  v7 final48   hybrid K=5: ToolAcc=0.875, E2E=0.729 [0.590, 0.834]

Decision gate v8: external E2E >= 0.70 AND final48 E2E >= 0.72
"""
from __future__ import annotations

import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SRC  = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

RESULTS = ROOT / "results"
DATA    = ROOT / "data" / "eval"

V7_BASELINES = {
    "external_hybrid":  {"ta": 0.847, "e2e": 0.674, "ci": "[0.593, 0.745]"},
    "external_noret":   {"ta": None,   "e2e": None,  "ci": ""},
    "final48_hybrid":   {"ta": 0.875,  "e2e": 0.729, "ci": "[0.590, 0.834]"},
}

CONFIGS = [
    (
        "C1: v8+hybrid (external144) [PRIMARY]",
        RESULTS / "v8" / "external_hybrid_k5_predictions.jsonl",
        DATA    / "vi_droidcall_external_test.jsonl",
        RESULTS / "v8" / "external_hybrid_k5_report.json",
        "external_hybrid",
    ),
    (
        "C2: v8+no_ret (external144)",
        RESULTS / "v8" / "external_no_retrieval_predictions.jsonl",
        DATA    / "vi_droidcall_external_test.jsonl",
        RESULTS / "v8" / "external_no_retrieval_report.json",
        "external_noret",
    ),
    (
        "C3: v8+hybrid (final48)",
        RESULTS / "v8" / "final48_hybrid_k5_predictions.jsonl",
        DATA    / "vi_droidcall_final48.jsonl",
        RESULTS / "v8" / "final48_hybrid_k5_report.json",
        "final48_hybrid",
    ),
]


def main() -> None:
    print("=" * 80)
    print("v8 Evaluation  (train408 + alpha=0.7)")
    print("=" * 80)
    print(f"  {'Config':<45} {'ToolAcc':>8} {'E2E':>8}  {'CI-95':<20}  v7_E2E  delta")
    print("  " + "-" * 80)

    results = {}
    for label, pred_path, eval_path, out_path, key in CONFIGS:
        if not pred_path.exists():
            print(f"  {label:<45}  MISSING: {pred_path.name}")
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        report = evaluate(eval_path=eval_path, predictions_path=pred_path)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        ta  = report["tool_selection_accuracy"]
        e2e = report["end_to_end_task_success"]
        ci  = report.get("end_to_end_ci_95", "")

        v7  = V7_BASELINES.get(key, {})
        v7e = v7.get("e2e")
        delta_str = f"{e2e - v7e:+.3f}" if v7e is not None else "  ---"

        print(f"  {label:<45} {ta:>8.4f} {e2e:>8.4f}  {ci:<20}  "
              f"{v7e if v7e else '  ---':>6}  {delta_str}")
        results[key] = {"ta": ta, "e2e": e2e, "ci": ci}

    print()
    # Decision gate
    ext_e2e = results.get("external_hybrid", {}).get("e2e", 0)
    f48_e2e = results.get("final48_hybrid",  {}).get("e2e", 0)
    gate_ext = ext_e2e >= 0.70
    gate_f48 = f48_e2e >= 0.72
    print("Decision gate v8:")
    print(f"  external E2E >= 0.70: {ext_e2e:.4f}  {'PASS' if gate_ext else 'FAIL'}")
    print(f"  final48  E2E >= 0.72: {f48_e2e:.4f}  {'PASS' if gate_f48 else 'FAIL'}")
    print(f"  Overall: {'PASS — v8 is new best' if gate_ext and gate_f48 else 'FAIL'}")

    print()
    print("vs v7 baselines:")
    print(f"  external hybrid: v7=0.674 → v8={ext_e2e:.4f} ({ext_e2e-0.674:+.4f})")
    print(f"  final48  hybrid: v7=0.729 → v8={f48_e2e:.4f} ({f48_e2e-0.729:+.4f})")


if __name__ == "__main__":
    main()
