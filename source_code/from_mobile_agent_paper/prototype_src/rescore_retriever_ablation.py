"""
Chạy sau khi download 3 prediction files từ Kaggle về
prototype/results/rescored/:
  - bm25_k5_final48_predictions.jsonl
  - hybrid_k5_final48_predictions.jsonl
  - no_retrieval_final48_predictions.jsonl

Usage:
  python src/rescore_retriever_ablation.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))

from evaluate import evaluate
from common import ROOT

EVAL_PATH   = ROOT / "data" / "eval" / "vi_droidcall_final48.jsonl"
RESCORED    = ROOT / "results" / "rescored"

CONFIGS = {
    "bm25_k5":      RESCORED / "bm25_k5_final48_predictions.jsonl",
    "hybrid_k5":    RESCORED / "hybrid_k5_final48_predictions.jsonl",
    "no_retrieval": RESCORED / "no_retrieval_final48_predictions.jsonl",
}

# Also include the v4_final (trained with hybrid) for direct comparison
REFERENCE = {
    "v21_final (191, hybrid)":  RESCORED / "v21_final_rescored.json",
    "v4_final  (251, hybrid)":  RESCORED / "v4_final_rescored.json",
    "classical baseline":       RESCORED / "classical_baseline_report.json",
}

def main() -> None:
    print("=" * 65)
    print("Retriever Ablation — final48 (N=48, post-hoc holdout)")
    print("=" * 65)
    print(f"{'Config':<26} {'ToolAcc':>8} {'SchemaVal':>10} {'E2E':>8}  {'CI-95'}")
    print("-" * 65)

    # Reference rows from already-scored files
    for label, path in REFERENCE.items():
        if not path.exists():
            print(f"  {label:<24}  MISSING: {path}")
            continue
        d = json.loads(path.read_text(encoding="utf-8"))
        tool_acc   = d.get("tool_selection_accuracy", d.get("tool_acc", "N/A"))
        schema_val = d.get("schema_valid_rate",       d.get("schema_valid", "N/A"))
        e2e        = d.get("end_to_end_task_success", d.get("e2e", "N/A"))
        ci         = d.get("end_to_end_ci_95", d.get("tool_selection_accuracy_ci_95", ""))
        def _fmt(v):
            return f"{v:>6.4f}" if isinstance(v, (int, float)) else f"{v!r:>8}"
        print(f"  {label:<24}  {_fmt(tool_acc)}   {_fmt(schema_val)}   {_fmt(e2e)}  {ci}")

    print()

    # Ablation configs
    for name, pred_path in CONFIGS.items():
        if not pred_path.exists():
            print(f"  {name:<24}  NOT YET DOWNLOADED — run Kaggle notebook first")
            continue

        out_path = RESCORED / f"{name}_final48_report.json"
        report   = evaluate(eval_path=EVAL_PATH, predictions_path=pred_path)
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        ta  = report["tool_selection_accuracy"]
        sv  = report["schema_valid_rate"]
        e2e = report["end_to_end_task_success"]
        ci  = report["end_to_end_ci_95"]
        print(f"  {name:<24}  {ta:>6.4f}   {sv:>8.4f}   {e2e:>6.4f}  {ci}")
        print(f"    -> saved: {out_path}")

    print()
    print("Note: CI overlap between any two configs means no significant difference.")
    print("      v4_final is the 'train-retriever-matches-eval-retriever' condition.")
    print("      hybrid_k5 here uses SAME adapter but checks if retrain mattered.")


if __name__ == "__main__":
    main()
