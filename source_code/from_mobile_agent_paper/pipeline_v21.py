"""Auto-pipeline for v2.1: evaluate → merge → GGUF → push phone.

Usage (từ prototype/):
    python -X utf8 src/pipeline_v21.py
    
Yêu cầu: adapter đã giải nén tại models/qwen2.5-1.5b-vidroidcall-lora/vidroidcall_lora_adapter_v2_1/
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE = ROOT / "prototype"
MODELS_DIR = ROOT / "models"
ADAPTER_DIR = MODELS_DIR / "qwen2.5-1.5b-vidroidcall-lora" / "vidroidcall_lora_adapter_v2_1"
MERGED_DIR  = MODELS_DIR / "qwen2.5-1.5b-vidroidcall-merged-v21"  # dir riêng, không overwrite v2
F16_GGUF    = MODELS_DIR / "vidroidcall_v21_f16.gguf"
Q4KM_GGUF   = MODELS_DIR / "vidroidcall_v21_q4km.gguf"
LLAMACPP_DIR = ROOT / "llama.cpp"
RESULTS_DIR = PROTOTYPE / "results"

BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
PREDICTIONS = RESULTS_DIR / "model_ft_v21_hybrid_top5_fixconf.jsonl"
REPORT = RESULTS_DIR / "model_ft_v21_hybrid_top5_fixconf_report.json"


def step_evaluate():
    print("\n" + "="*60)
    print("STEP 1: Evaluate v2.1 adapter on vi_smoke_test")
    print("="*60)
    if not ADAPTER_DIR.exists():
        print(f"[ERROR] Adapter not found at {ADAPTER_DIR}")
        print("Giải nén vidroidcall_lora_adapter_v2_1.zip vào thư mục đó trước.")
        return False
    
    cmd = [
        sys.executable, "-X", "utf8",
        str(PROTOTYPE / "src" / "evaluate_ft.py"),
        "--adapter", str(ADAPTER_DIR),
        "--base-model", BASE_MODEL,
        "--retriever", "hybrid",
        "--top-k", "5",
        "--fix-confirmation",
        "--output", str(PREDICTIONS),
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    # Generate report
    cmd2 = [
        sys.executable, "-X", "utf8",
        str(PROTOTYPE / "src" / "evaluate.py"),
        str(PREDICTIONS),
        "--output", str(REPORT),
    ]
    print(f"Running: {' '.join(cmd2)}")
    subprocess.run(cmd2, check=True)
    
    # Print summary
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    print(f"\n{'='*60}")
    print(f"RESULTS: E2E={report['end_to_end_task_success']:.3f}, "
          f"ToolAcc={report['tool_selection_accuracy']:.3f}")
    print(f"{'='*60}")
    
    return report["end_to_end_task_success"] >= 0.700


def step_merge():
    print("\n" + "="*60)
    print("STEP 2: Merge LoRA adapter into base model")
    print("="*60)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    
    print(f"Loading base: {BASE_MODEL}")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    print(f"Loading adapter: {ADAPTER_DIR}")
    model = PeftModel.from_pretrained(base, str(ADAPTER_DIR))
    print("Merging weights...")
    merged = model.merge_and_unload()
    merged.eval()
    
    print(f"Saving to {MERGED_DIR}")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_DIR))
    AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True).save_pretrained(str(MERGED_DIR))
    print(f"[OK] Merged saved: {MERGED_DIR}")


def step_convert_gguf():
    print("\n" + "="*60)
    print("STEP 3: Convert merged model to GGUF Q4_K_M")
    print("="*60)
    
    # Convert to f16
    script = LLAMACPP_DIR / "convert_hf_to_gguf.py"
    if not script.exists():
        print(f"[ERROR] {script} not found")
        return False
    subprocess.run([sys.executable, str(script), str(MERGED_DIR),
                    "--outfile", str(F16_GGUF), "--outtype", "f16"], check=True)
    print(f"[OK] f16 GGUF: {F16_GGUF}  ({F16_GGUF.stat().st_size/1e9:.2f} GB)")
    
    # Quantize to Q4_K_M
    candidates = [
        Path("D:/AndroidProjects/llama-win-bin/llama-quantize.exe"),
        LLAMACPP_DIR / "build-windows" / "bin" / "Release" / "llama-quantize.exe",
    ]
    quantize_bin = next((p for p in candidates if p.exists()), None)
    if quantize_bin is None:
        print("[ERROR] llama-quantize.exe not found")
        return False
    subprocess.run([str(quantize_bin), str(F16_GGUF), str(Q4KM_GGUF), "Q4_K_M"], check=True)
    print(f"[OK] Q4_K_M: {Q4KM_GGUF}  ({Q4KM_GGUF.stat().st_size/1e6:.0f} MB)")
    return True


def step_push_phone():
    print("\n" + "="*60)
    print("STEP 4: Push model to phone & run benchmark")
    print("="*60)
    dst_phone = "/sdcard/Android/data/com.vintent.app/files/vidroidcall_v21_q4km.gguf"
    res = subprocess.run([
        "adb", "-s", "192.168.1.92:34363", "push",
        str(Q4KM_GGUF), dst_phone
    ], capture_output=True, text=True)
    print(res.stdout.strip() or res.stderr.strip())
    if res.returncode == 0:
        print(f"[OK] Model pushed → {dst_phone}")
    return res.returncode == 0


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-evaluate", action="store_true",
                    help="Bỏ qua bước evaluate (dùng khi đã có kết quả)")
    ap.add_argument("--skip-merge",    action="store_true",
                    help="Bỏ qua bước merge (dùng khi merged model đã có)")
    ap.add_argument("--skip-push",     action="store_true",
                    help="Bỏ qua bước push lên phone")
    args = ap.parse_args()

    t0 = time.time()

    if not args.skip_evaluate:
        good = step_evaluate()
        if not good:
            print("\n❌ E2E < 0.700 — Cần cải thiện thêm, dừng pipeline")
            return
        print("\n✅ E2E ≥ 0.700 — Tiến hành merge + push phone")
    else:
        print("[SKIP] Evaluate — dùng kết quả đã có (E2E=0.906)")

    if not args.skip_merge:
        step_merge()
    else:
        print(f"[SKIP] Merge — dùng {MERGED_DIR}")

    step_convert_gguf()

    if not args.skip_push:
        step_push_phone()

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed/60:.1f} min")


if __name__ == "__main__":
    main()