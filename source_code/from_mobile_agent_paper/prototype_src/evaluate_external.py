"""
Evaluate predictions on the external test set.

Usage (after downloading from Kaggle):
    python src/evaluate_external.py

Reads from:
    prototype/results/external/hybrid_k5_external_predictions.jsonl
    prototype/results/external/no_retrieval_external_predictions.jsonl

Eval set:
    prototype/data/eval/vi_droidcall_external_test.jsonl

Saves reports to:
    prototype/results/external/hybrid_k5_external_report.json
    prototype/results/external/no_retrieval_external_report.json
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

EVAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"
EXT_DIR   = ROOT / "results" / "external"

CONFIGS = {
    "hybrid_k5":    EXT_DIR / "hybrid_k5_external_predictions.jsonl",
    "no_retrieval": EXT_DIR / "no_retrieval_external_predictions.jsonl",
}


def main() -> None:
    EXT_DIR.mkdir(parents=True, exist_ok=True)

    if not EVAL_PATH.exists():
        raise FileNotFoundError(f"Eval set not found: {EVAL_PATH}")

    eval_data = [json.loads(l) for l in EVAL_PATH.read_text("utf-8").splitlines() if l.strip()]
    n_pos = sum(1 for r in eval_data if r["expected"]["tool"] is not None)
    n_neg = len(eval_data) - n_pos

    print("=" * 65)
    print(f"External Test Set Evaluation  (N={len(eval_data)}: {n_pos} pos, {n_neg} neg)")
    print("=" * 65)
    print(f"{'Config':<22} {'ToolAcc':>8} {'SchemaVal':>10} {'E2E':>8}  CI-95")
    print("-" * 65)

    results = {}
    for name, pred_path in CONFIGS.items():
        if not pred_path.exists():
            print(f"  {name:<20}  NOT FOUND: {pred_path}")
            print(f"    -> Download from Kaggle /kaggle/working/ and place here")
            continue

        out_path = EXT_DIR / f"{name}_external_report.json"
        report   = evaluate(eval_path=EVAL_PATH, predictions_path=pred_path)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        ta  = report["tool_selection_accuracy"]
        sv  = report["schema_valid_rate"]
        e2e = report["end_to_end_task_success"]
        ci  = report.get("end_to_end_ci_95", "")
        print(f"  {name:<22}  {ta:>6.4f}   {sv:>8.4f}   {e2e:>6.4f}  {ci}")
        print(f"    saved: {out_path}")
        results[name] = report

    print()

    # Per-group breakdown for hybrid_k5
    if "hybrid_k5" in results:
        r = results["hybrid_k5"]
        per_ex = {ex["id"]: ex for ex in r.get("per_example", [])}
        by_group: dict[str, dict] = defaultdict(lambda: {"n": 0, "tool_ok": 0, "e2e_ok": 0})
        for ex in eval_data:
            g = ex.get("group", "unknown")
            rec = per_ex.get(ex["id"], {})
            by_group[g]["n"] += 1
            by_group[g]["tool_ok"] += int(rec.get("tool_correct", False))
            by_group[g]["e2e_ok"]  += int(rec.get("end_to_end",   False))

        print("Per-group breakdown (hybrid_k5):")
        print(f"  {'Group':<25} {'N':>4}  {'ToolAcc':>8}  {'E2E':>8}")
        print(f"  {'-'*25} {'-'*4}  {'-'*8}  {'-'*8}")
        for g in sorted(by_group):
            v = by_group[g]
            ta_g  = v["tool_ok"] / v["n"]
            e2e_g = v["e2e_ok"]  / v["n"]
            print(f"  {g:<25} {v['n']:>4}  {ta_g:>8.3f}  {e2e_g:>8.3f}")

    print()
    print("Reference (final48 post-hoc holdout, same model):")
    print("  hybrid_k5    : ToolAcc=0.8750, E2E=0.7500  [0.612, 0.851]")
    print("  no_retrieval : ToolAcc=0.6667, E2E=0.5208  [0.383, 0.655]")


if __name__ == "__main__":
    main()
