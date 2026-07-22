"""Run all P5 experiments in sequence.

This script runs each experiment using evaluate_ft.py and produces predictions.
Then runs evaluate.py to produce metrics.

Usage:
    python -X utf8 src/run_p5_experiments.py [--adapter-path ...]

Order:
    1. Noisy eval (light, medium, heavy)  — 5.2
    2. Code-switching eval                — 5.4
    3. No-retrieval baseline (topK=24)    — 5.5
    4. topK ablation (K=1,2,3,5)          — 5.6
    5. Adaptive topK analysis             — 5.7
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
EVAL_DIR = ROOT / "data" / "eval"
ADAPTER_DEFAULT = ROOT.parent / "models" / "qwen2.5-0.5b-vidroidcall-lora" / "vidroidcall_lora_adapter_v2"

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def run_eval(label: str, eval_path: Path, top_k: int, retriever: str = "hybrid",
             extra_args: list[str] | None = None) -> Path:
    """Run evaluate_ft.py and return predictions path."""
    label_slug = label.lower().replace(" ", "_")
    out_path = RESULTS_DIR / f"p5_{label_slug}_top{top_k}.jsonl"

    cmd = [
        sys.executable, "-X", "utf8",
        str(ROOT / "src" / "run_eval_custom.py"),
        "--eval-path", str(eval_path),
        "--top-k", str(top_k),
        "--retriever", retriever,
        "--fix-confirmation",
        "--output", str(out_path),
    ]
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n{'='*60}")
    print(f"Experiment: {label}")
    print(f"  Eval: {eval_path}")
    print(f"  topK: {top_k}, retriever: {retriever}")
    print(f"  Output: {out_path}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  ❌ FAILED (rc={result.returncode})")
        return out_path

    print(f"  ✅ Done → {out_path}")

    # Run evaluate.py
    report_path = out_path.with_suffix("").name + "_report.json"
    report_full = out_path.parent / report_path
    cmd_eval = [
        sys.executable, "-X", "utf8",
        str(ROOT / "src" / "evaluate.py"),
        str(out_path),
        "--output", str(report_full),
    ]
    print(f"  Evaluating metrics...")
    subprocess.run(cmd_eval, capture_output=False)

    return out_path


def run_ablation(label: str, eval_path: Path, top_k_list: list[int]) -> dict[int, dict]:
    """Run topK ablation and return results."""
    results = {}
    for k in top_k_list:
        out = run_eval(f"{label}_K{k}", eval_path, k)
        report_path = out.parent / (out.stem + "_report.json")
        if report_path.exists():
            results[k] = json.loads(report_path.read_text("utf-8"))
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, default=ADAPTER_DEFAULT)
    parser.add_argument("--skip-noisy", action="store_true")
    parser.add_argument("--skip-codeswitch", action="store_true")
    parser.add_argument("--skip-noretrieval", action="store_true")
    parser.add_argument("--skip-ablation", action="store_true")
    parser.add_argument("--skip-adaptive", action="store_true")
    args = parser.parse_args()

    if not args.adapter.exists():
        print(f"Error: adapter not found at {args.adapter}")
        sys.exit(1)

    adapter = args.adapter
    adapter_base = adapter.parent.parent.name

    print(f"Adapter: {adapter.resolve()}")
    print(f"Base:    {BASE_MODEL}")
    print(f"Results: {RESULTS_DIR}")
    print()

    start = None
    smoke_test = EVAL_DIR / "vi_smoke_test.jsonl"
    assert smoke_test.exists(), f"{smoke_test} not found"

    # ── Step 1: Run clean baseline first (for comparison) ──────────────────
    clean_out = run_eval("clean_baseline", smoke_test, 5)

    # ── Step 2: Noisy eval (light, medium, heavy) ──────────────────────────
    if not args.skip_noisy:
        for level in ["light", "medium", "heavy"]:
            noisy_path = EVAL_DIR / f"noisy_smoke_{level}.jsonl"
            if not noisy_path.exists():
                print(f"  ⚠️  {noisy_path} not found, skipping")
                continue
            run_eval(f"noisy_{level}", noisy_path, 5)

    # ── Step 3: Code-switching eval ────────────────────────────────────────
    if not args.skip_codeswitch:
        cs_path = EVAL_DIR / "codeswitch_queries.jsonl"
        if cs_path.exists():
            run_eval("codeswitch", cs_path, 5)
        else:
            print(f"  ⚠️  {cs_path} not found, skipping")

    # ── Step 4: No-retrieval baseline (topK=24) ────────────────────────────
    if not args.skip_noretrieval:
        run_eval("no_retrieval", smoke_test, 24)

    # ── Step 5: topK ablation (K=1,2,3,5) ──────────────────────────────────
    if not args.skip_ablation:
        for k in [1, 2, 3, 5]:
            run_eval(f"ablation_K{k}", smoke_test, k)

    # ── Step 6: Adaptive topK analysis ─────────────────────────────────────
    if not args.skip_adaptive:
        # First collect BM25 score distribution from eval
        score_script = str(ROOT / "src" / "adaptive_topk.py")
        if Path(score_script).exists():
            print("\n" + "="*60)
            print("Step 6: Adaptive topK analysis")
            print("="*60)
            subprocess.run([
                sys.executable, "-X", "utf8", score_script,
                "--eval", str(smoke_test),
                "--results", str(RESULTS_DIR),
            ])
        else:
            print("  ⚠️  adaptive_topk.py not found, skipping")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    print("P5 Experiments Complete!")
    print("="*60)
    print(f"\nResults in: {RESULTS_DIR}")
    print("\nRun `python -X utf8 src/collect_p5_results.py` to compile summary table.")


if __name__ == "__main__":
    main()