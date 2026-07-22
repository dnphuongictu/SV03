"""
Chay canonical evaluator (src/evaluate.py) tren cac predictions da luu.
Usage: python src/run_canonical_eval.py
"""
import sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common
from evaluate import evaluate

ROOT = Path(__file__).parent.parent

JOBS = [
    # (predictions_jsonl, eval_jsonl, output_report)
    ("results/model_ft_v21_hybrid_top5_fixconf.jsonl",
     "data/eval/vi_smoke_test.jsonl",
     "results/v21_clean_canonical_report.json"),

    ("results/v21_noisy_light.jsonl",
     "data/eval/noisy_smoke_light.jsonl",
     "results/v21_noisy_light_canonical2_report.json"),

    ("results/v21_noisy_medium.jsonl",
     "data/eval/noisy_smoke_medium.jsonl",
     "results/v21_noisy_medium_canonical2_report.json"),

    ("results/v21_noisy_heavy.jsonl",
     "data/eval/noisy_smoke_heavy.jsonl",
     "results/v21_noisy_heavy_canonical2_report.json"),

    ("results/v3_noisy_light.jsonl",
     "data/eval/noisy_smoke_light.jsonl",
     "results/v3_noisy_light_canonical2_report.json"),

    ("results/zeroshot_predictions.jsonl",
     "data/eval/vi_smoke_test.jsonl",
     "results/zeroshot_clean_canonical_report.json"),
]

print(f"{'Predictions':<45} {'ToolAcc':>8} {'Schema':>8} {'SoftArg':>8} {'E2E':>8}")
print("-" * 80)

for preds_rel, eval_rel, out_rel in JOBS:
    preds_path = ROOT / preds_rel
    eval_path  = ROOT / eval_rel
    out_path   = ROOT / out_rel

    if not preds_path.exists():
        print(f"  MISSING: {preds_rel}")
        continue
    if not eval_path.exists():
        print(f"  MISSING eval: {eval_rel}")
        continue

    common.EVAL_PATH = eval_path
    report = evaluate(preds_path)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    label = preds_rel.replace("results/", "").replace(".jsonl", "")[:43]
    print(f"  {label:<45} "
          f"{report['tool_selection_accuracy']:>8.4f} "
          f"{report['schema_valid_rate']:>8.4f} "
          f"{report['soft_argument_accuracy']:>8.4f} "
          f"{report['end_to_end_task_success']:>8.4f}")

print("\nDone. Reports saved to results/")
