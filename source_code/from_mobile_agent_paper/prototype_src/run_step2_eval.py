"""Wrapper script for Step 2: Re-evaluate v3 on fixed codeswitch labels."""
from __future__ import annotations

import sys
from pathlib import Path

# Add current dir for imports
sys.path.insert(0, str(Path(__file__).parent))

import evaluate_ft as ft_mod

ROOT = Path(__file__).resolve().parents[1]

# Override EVAL_PATH in evaluate_ft
eval_path = ROOT / "data" / "eval" / "codeswitch_queries.jsonl"
ft_mod.EVAL_PATH = eval_path
ft_mod.RESULTS_DIR = ROOT / "results"

# Default adapter for v3
adapter = (
    ROOT.parent / "models" / "qwen2.5-1.5b-vidroidcall-lora" / "vidroidcall_lora_adapter_v3_cs"
)
output = ROOT / "results" / "v3_codeswitch_predictions.jsonl"

sys.argv = [
    "evaluate_ft.py",
    "--adapter", str(adapter),
    "--retriever", "hybrid",
    "--top-k", "5",
    "--fix-confirmation",
    "--output", str(output),
]

print(f"Eval path: {eval_path}")
print(f"Adapter:   {adapter}")
print(f"Output:    {output}")
print("-" * 60)

ft_mod.main()