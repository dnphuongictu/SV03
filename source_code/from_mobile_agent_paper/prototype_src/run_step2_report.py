"""Run evaluate.py on codeswitch predictions with the correct EVAL_PATH."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

# ── Override EVAL_PATH before importing evaluate ──
# Must set EVAL_PATH in common module BEFORE evaluate imports it
import common
common_old = common.EVAL_PATH  # remember original
common.EVAL_PATH = ROOT / "data" / "eval" / "codeswitch_queries.jsonl"

# Now import evaluate — it will get the overridden EVAL_PATH from common
import evaluate

predictions_path = ROOT / "results" / "v3_codeswitch_predictions.jsonl"
if not predictions_path.exists():
    print(f"Error: {predictions_path} not found")
    sys.exit(1)

print(f"EVAL_PATH (old): {common_old}")
print(f"EVAL_PATH (new): {common.EVAL_PATH}")
print(f"Predictions:     {predictions_path}")
print("-" * 60)

report = evaluate.evaluate(predictions_path)
rendered = json.dumps(report, ensure_ascii=False, indent=2)

output_path = ROOT / "results" / "v3_codeswitch_report_fixedlabels.json"
output_path.write_text(rendered, encoding="utf-8")
print(rendered)
print(f"\n✅ Saved to {output_path}")