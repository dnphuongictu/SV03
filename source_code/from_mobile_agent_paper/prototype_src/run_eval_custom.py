"""Run evaluate_ft.py with custom eval data path.

Usage:
    python -X utf8 src/run_eval_custom.py --eval-path data/eval/noisy_smoke.jsonl --top-k 5 --retriever hybrid --output results/noisy_light.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Override EVAL_PATH in evaluate_ft before it's fully loaded
import evaluate_ft as ft_mod

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-path", type=Path, required=True,
                        help="Path to eval JSONL file")
    parser.add_argument("--adapter", type=Path, default=None,
                        help="LoRA adapter path (default: v2 adapter)")
    parser.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--fix-confirmation", action="store_true", default=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    # Override EVAL_PATH
    eval_path = args.eval_path.resolve()
    if not eval_path.exists():
        print(f"Error: {eval_path} not found")
        sys.exit(1)
    ft_mod.EVAL_PATH = eval_path
    ft_mod.RESULTS_DIR = ROOT / "results"

    # Default adapter path
    if args.adapter is None:
        args.adapter = (
            ROOT.parent / "models" / "qwen2.5-0.5b-vidroidcall-lora" / "vidroidcall_lora_adapter_v2"
        )
    if not args.adapter.exists():
        print(f"Error: Adapter not found at {args.adapter}")
        sys.exit(1)

    # Build sys.argv for evaluate_ft.main()
    save_output = args.output or ft_mod.RESULTS_DIR / f"model_ft_{args.retriever}_top{args.top_k}_fixconf.jsonl"
    sys.argv = [
        "evaluate_ft.py",
        "--adapter", str(args.adapter),
        "--retriever", args.retriever,
        "--top-k", str(args.top_k),
        "--fix-confirmation",
        "--output", str(save_output),
    ]

    print(f"Eval path: {eval_path}")
    print(f"Adapter:   {args.adapter}")
    print(f"Retriever: {args.retriever}")
    print(f"top-k:     {args.top_k}")
    print(f"Output:    {save_output}")
    print("-" * 60)

    ft_mod.main()


if __name__ == "__main__":
    main()