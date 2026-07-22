"""
Evaluate v9 predictions after downloading from Kaggle.

Usage:
    python src/evaluate_v9.py

Reads from prototype/results/v9/
  external_hybrid_k5_predictions.jsonl
  external_no_retrieval_predictions.jsonl
  final48_hybrid_k5_predictions.jsonl

Baselines (canonical):
  v7 external hybrid K=5: ToolAcc=0.847, E2E=0.674 [0.593, 0.745]
  v7 final48   hybrid K=5: ToolAcc=0.875, E2E=0.729 [0.590, 0.834]
  v8 external hybrid K=5: ToolAcc=0.868, E2E=0.729 [0.651, 0.795]
  v8 final48   hybrid K=5: ToolAcc=0.833, E2E=0.667 [0.525, 0.783]

Decision gate v9: external E2E >= 0.74 AND final48 E2E >= 0.70
"""
from __future__ import annotations

import json, sys, io, math
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

RESULTS = ROOT / "results"
DATA    = ROOT / "data" / "eval"

V8_BASELINES = {
    "external_hybrid": {"ta": 0.868, "e2e": 0.7292, "ci": "[0.651, 0.795]"},
    "external_noret":  {"ta": None,  "e2e": None,    "ci": ""},
    "final48_hybrid":  {"ta": 0.833, "e2e": 0.6667,  "ci": "[0.525, 0.783]"},
}

V7_BASELINES = {
    "external_hybrid": {"e2e": 0.674},
    "final48_hybrid":  {"e2e": 0.729},
}

CONFIGS = [
    (
        "C1: v9+hybrid (external144) [PRIMARY]",
        RESULTS / "v9" / "external_hybrid_k5_predictions.jsonl",
        DATA    / "vi_droidcall_external_test.jsonl",
        RESULTS / "v9" / "external_hybrid_k5_report.json",
        "external_hybrid",
    ),
    (
        "C2: v9+no_ret (external144)",
        RESULTS / "v9" / "external_no_retrieval_predictions.jsonl",
        DATA    / "vi_droidcall_external_test.jsonl",
        RESULTS / "v9" / "external_no_retrieval_report.json",
        "external_noret",
    ),
    (
        "C3: v9+hybrid (final48)",
        RESULTS / "v9" / "final48_hybrid_k5_predictions.jsonl",
        DATA    / "vi_droidcall_final48.jsonl",
        RESULTS / "v9" / "final48_hybrid_k5_report.json",
        "final48_hybrid",
    ),
]


def mcnemar(pred_a_path: Path, pred_b_path: Path, gt_path: Path) -> tuple[float, float]:
    gt    = {json.loads(l)["id"]: json.loads(l) for l in gt_path.read_text("utf-8").splitlines() if l.strip()}
    pa    = {json.loads(l)["id"]: json.loads(l) for l in pred_a_path.read_text("utf-8").splitlines() if l.strip()}
    pb    = {json.loads(l)["id"]: json.loads(l) for l in pred_b_path.read_text("utf-8").splitlines() if l.strip()}

    def ok(pred_rec: dict, gt_rec: dict) -> bool:
        p = pred_rec.get("prediction", pred_rec)
        e = gt_rec["expected"]
        if p.get("tool") != e.get("tool"): return False
        gt_args = e.get("arguments") or {}
        pd_args = p.get("arguments") or {}
        for k, v in gt_args.items():
            pv = pd_args.get(k)
            if pv is None: return False
            if isinstance(v, str) and isinstance(pv, str):
                if v.lower() != pv.lower(): return False
            elif v != pv: return False
        if e.get("status") and p.get("status") != e.get("status"): return False
        return True

    n10 = n01 = 0
    for eid, gt_rec in gt.items():
        a = ok(pa.get(eid, {}), gt_rec)
        b = ok(pb.get(eid, {}), gt_rec)
        if a and not b: n10 += 1
        if not a and b: n01 += 1
    disc = n10 + n01
    if disc == 0: return 0.0, 1.0
    z = (n10 - n01) / math.sqrt(disc)
    p = 2 * (1 - 0.5*(1 + math.erf(abs(z)/math.sqrt(2))))
    return z, p


def main() -> None:
    print("=" * 80)
    print("v9 Evaluation  (train444 + alpha=0.7)")
    print("=" * 80)
    print(f"  {'Config':<45} {'ToolAcc':>8} {'E2E':>8}  {'CI-95':<20}  v8_E2E  delta")
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

        v8  = V8_BASELINES.get(key, {})
        v8e = v8.get("e2e")
        delta_str = f"{e2e - v8e:+.3f}" if v8e is not None else "  ---"

        print(f"  {label:<45} {ta:>8.4f} {e2e:>8.4f}  {ci:<20}  "
              f"{v8e if v8e else '  ---':>6}  {delta_str}")
        results[key] = {"ta": ta, "e2e": e2e, "ci": ci}

    print()
    ext_e2e = results.get("external_hybrid", {}).get("e2e", 0)
    f48_e2e = results.get("final48_hybrid",  {}).get("e2e", 0)

    # McNemar v8 vs v9
    v8_ext_path = RESULTS / "v8" / "external_hybrid_k5_predictions.jsonl"
    v9_ext_path = RESULTS / "v9" / "external_hybrid_k5_predictions.jsonl"
    v8_f48_path = RESULTS / "v8" / "final48_hybrid_k5_predictions.jsonl"
    v9_f48_path = RESULTS / "v9" / "final48_hybrid_k5_predictions.jsonl"

    if v8_ext_path.exists() and v9_ext_path.exists():
        z_e, p_e = mcnemar(v8_ext_path, v9_ext_path, DATA/"vi_droidcall_external_test.jsonl")
        print(f"McNemar v8 vs v9 (external): z={z_e:.2f}, p={p_e:.3f}  "
              f"({'sig' if abs(z_e)>1.96 else 'NOT sig'})")
    if v8_f48_path.exists() and v9_f48_path.exists():
        z_f, p_f = mcnemar(v8_f48_path, v9_f48_path, DATA/"vi_droidcall_final48.jsonl")
        print(f"McNemar v8 vs v9 (final48):  z={z_f:.2f}, p={p_f:.3f}  "
              f"({'sig' if abs(z_f)>1.96 else 'NOT sig'})")

    print()
    gate_ext = ext_e2e >= 0.74
    gate_f48 = f48_e2e >= 0.70
    print("Decision gate v9:")
    print(f"  external E2E >= 0.74: {ext_e2e:.4f}  {'PASS' if gate_ext else 'FAIL'}")
    print(f"  final48  E2E >= 0.70: {f48_e2e:.4f}  {'PASS' if gate_f48 else 'FAIL'}")
    print(f"  Overall: {'PASS -- v9 is new best' if gate_ext and gate_f48 else 'FAIL'}")

    print()
    print("vs v7 baselines:")
    v7_ext = V7_BASELINES.get("external_hybrid", {}).get("e2e", 0)
    v7_f48 = V7_BASELINES.get("final48_hybrid",  {}).get("e2e", 0)
    print(f"  external hybrid: v7=0.674 -> v9={ext_e2e:.4f} ({ext_e2e-v7_ext:+.4f})")
    print(f"  final48  hybrid: v7=0.729 -> v9={f48_e2e:.4f} ({f48_e2e-v7_f48:+.4f})")


if __name__ == "__main__":
    main()
