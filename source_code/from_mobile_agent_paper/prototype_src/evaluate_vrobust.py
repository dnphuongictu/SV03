"""
Evaluate v_robust predictions after downloading from Kaggle.

Usage:
    python src/evaluate_vrobust.py

Reads from prototype/results/vrobust/
  external_hybrid_k5_predictions.jsonl
  noisy_light_predictions.jsonl
  noisy_medium_predictions.jsonl
  noisy_heavy_predictions.jsonl
  final48_hybrid_k5_predictions.jsonl

Baselines (for comparison):
  v2.1  noisy_light=0.688, noisy_medium=0.344, noisy_heavy=0.313
  v3_cs noisy_light=0.750, noisy_medium=0.375, noisy_heavy=0.344
  v7    extTest144=0.674, final48=0.729
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

RESULTS = ROOT / "results"
DATA    = ROOT / "data" / "eval"

CONFIGS = [
    # (label, pred_path, eval_path, out_path, v21_e2e, v7_e2e)
    (
        "C1: vrobust+hybrid (external144)",
        RESULTS / "vrobust" / "external_hybrid_k5_predictions.jsonl",
        DATA / "vi_droidcall_external_test.jsonl",
        RESULTS / "vrobust" / "external_hybrid_k5_report.json",
        0.556, 0.674,
    ),
    (
        "C2: vrobust+hybrid (noisy_light)",
        RESULTS / "vrobust" / "noisy_light_predictions.jsonl",
        DATA / "noisy_smoke_light.jsonl",
        RESULTS / "vrobust" / "noisy_light_report.json",
        0.688, None,
    ),
    (
        "C3: vrobust+hybrid (noisy_medium)",
        RESULTS / "vrobust" / "noisy_medium_predictions.jsonl",
        DATA / "noisy_smoke_medium.jsonl",
        RESULTS / "vrobust" / "noisy_medium_report.json",
        0.344, None,
    ),
    (
        "C4: vrobust+hybrid (noisy_heavy)",
        RESULTS / "vrobust" / "noisy_heavy_predictions.jsonl",
        DATA / "noisy_smoke_heavy.jsonl",
        RESULTS / "vrobust" / "noisy_heavy_report.json",
        0.313, None,
    ),
    (
        "C5: vrobust+hybrid (final48)",
        RESULTS / "vrobust" / "final48_hybrid_k5_predictions.jsonl",
        DATA / "vi_droidcall_final48.jsonl",
        RESULTS / "vrobust" / "final48_hybrid_k5_report.json",
        0.667, 0.729,
    ),
]

# v3_cs baselines (for noisy conditions)
V3CS_BASELINES = {
    "noisy_light":  0.750,
    "noisy_medium": 0.375,
    "noisy_heavy":  0.344,
}


def main() -> None:
    print("=" * 80)
    print("v_robust Evaluation (Clean + Noisy)")
    print("=" * 80)
    print(f"{'Config':<40} {'ToolAcc':>8} {'E2E':>8}  {'CI-95':<18}  v2.1   v7/v3")
    print("-" * 80)

    results = {}
    for label, pred_path, eval_path, out_path, v21_e2e, v7_e2e in CONFIGS:
        if not pred_path.exists():
            print(f"  {label:<38}  MISSING: {pred_path.name}")
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        report = evaluate(eval_path=eval_path, predictions_path=pred_path)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        ta   = report["tool_selection_accuracy"]
        e2e  = report["end_to_end_task_success"]
        ci   = report.get("end_to_end_ci_95", "")
        key  = label.split("(")[1].rstrip(")")

        v3cs = V3CS_BASELINES.get(key.replace("noisy_", "").replace("noisy ", ""), None)
        base_str = f"v2.1={v21_e2e:.3f}"
        comp_str = f"v3cs={v3cs:.3f}" if v3cs else (f"v7={v7_e2e:.3f}" if v7_e2e else "—")

        print(f"  {label:<40} {ta:>6.4f}  {e2e:>6.4f}  {ci:<18}  {base_str}  {comp_str}")
        results[key] = e2e

    print()
    print("Decision gate v_robust:")
    noisy_heavy_e2e = results.get("noisy_heavy", 0)
    ext_e2e = results.get("external144", 0)
    gate = noisy_heavy_e2e >= 0.40 and ext_e2e >= 0.63
    print(f"  noisy_heavy E2E >= 0.40: {noisy_heavy_e2e:.4f}  {'PASS' if noisy_heavy_e2e >= 0.40 else 'FAIL'}")
    print(f"  extTest144  E2E >= 0.63: {ext_e2e:.4f}  {'PASS' if ext_e2e >= 0.63 else 'FAIL'}")
    print(f"  Overall: {'PASS' if gate else 'FAIL'}")

    print()
    print("Comparison vs baselines:")
    print("  Condition    v2.1   v3_cs  v_robust  Delta_v21  Delta_v3cs")
    for cond, v21 in [("Light ", 0.688), ("Medium", 0.344), ("Heavy ", 0.313)]:
        key  = f"noisy_{cond.strip().lower()}"
        v3cs = V3CS_BASELINES.get(key, 0)
        rob  = results.get(key, 0)
        print(f"  {cond}  {v21:.3f}  {v3cs:.3f}  {rob:.3f}     {rob-v21:+.3f}     {rob-v3cs:+.3f}")


if __name__ == "__main__":
    main()
