"""Run evaluate.py with custom eval data path.

Usage:
    python -X utf8 src/run_evaluate_custom.py \\
        --predictions results/p5_codeswitch_top5.jsonl \\
        --eval-path data/eval/codeswitch_queries.jsonl \\
        --output results/p5_codeswitch_top5_report.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import common
import evaluate as eval_mod

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--eval-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    # Override EVAL_PATH in common module (used by evaluate.py via `from common import EVAL_PATH`)
    eval_path = args.eval_path.resolve()
    if not eval_path.exists():
        print(f"Error: {eval_path} not found")
        sys.exit(1)

    common.EVAL_PATH = eval_path

    pred_path = args.predictions.resolve()
    if not pred_path.exists():
        print(f"Error: {pred_path} not found")
        sys.exit(1)

    report = eval_mod.evaluate(pred_path)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        out_path = args.output.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered, encoding="utf-8")

    print(rendered)


if __name__ == "__main__":
    main()