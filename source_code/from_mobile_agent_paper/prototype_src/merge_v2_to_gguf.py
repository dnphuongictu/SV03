"""Merge LoRA adapter v2 (1.5B, r=16) vào base model rồi export GGUF Q4_K_M.

Usage (từ thư mục prototype/):
    python -X utf8 src/merge_v2_to_gguf.py
    python -X utf8 src/merge_v2_to_gguf.py --skip-merge   # nếu merged model đã có
    python -X utf8 src/merge_v2_to_gguf.py --only-merge
"""
from __future__ import annotations
import argparse, subprocess, sys
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[2]
MODELS_DIR  = ROOT / "models"
ADAPTER_DIR = MODELS_DIR / "qwen2.5-0.5b-vidroidcall-lora" / "vidroidcall_lora_adapter_v2"
MERGED_DIR  = MODELS_DIR / "qwen2.5-1.5b-vidroidcall-merged"
F16_GGUF    = MODELS_DIR / "vidroidcall_v2_f16.gguf"
Q4KM_GGUF   = MODELS_DIR / "vidroidcall_v2_q4km.gguf"
LLAMACPP_DIR = ROOT / "llama.cpp"
BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"


def step_merge():
    print("\n=== Step 1: Merge LoRA adapter v2 into 1.5B base ===")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print(f"Loading base: {BASE_MODEL_ID}")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )
    print(f"Loading adapter: {ADAPTER_DIR}")
    model = PeftModel.from_pretrained(base, str(ADAPTER_DIR.resolve()))
    print("Merging weights...")
    merged = model.merge_and_unload()
    merged.eval()

    print(f"Saving to {MERGED_DIR}")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_DIR))
    AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True).save_pretrained(str(MERGED_DIR))
    print(f"[OK] Merged saved: {MERGED_DIR}")


def step_convert_f16():
    print("\n=== Step 2: Convert merged model to GGUF f16 ===")
    script = LLAMACPP_DIR / "convert_hf_to_gguf.py"
    if not script.exists():
        sys.exit(f"[ERROR] {script} not found")
    subprocess.run([sys.executable, str(script),
                    str(MERGED_DIR), "--outfile", str(F16_GGUF), "--outtype", "f16"],
                   check=True)
    print(f"[OK] f16 GGUF: {F16_GGUF}  ({F16_GGUF.stat().st_size/1e9:.2f} GB)")


def step_quantize():
    print("\n=== Step 3: Quantize f16 → Q4_K_M ===")
    # Try pre-built binary first
    candidates = [
        Path("D:/AndroidProjects/llama-win-bin/llama-quantize.exe"),  # pre-built release b9585
        LLAMACPP_DIR / "build-windows" / "bin" / "Release" / "llama-quantize.exe",
        LLAMACPP_DIR / "build-windows" / "bin" / "llama-quantize.exe",
        LLAMACPP_DIR / "llama-quantize.exe",
    ]
    quantize_bin = next((p for p in candidates if p.exists()), None)

    if quantize_bin is None:
        print("[INFO] llama-quantize.exe not found — building for Windows...")
        build_dir = LLAMACPP_DIR / "build-windows"
        subprocess.run(["cmake", "-B", str(build_dir),
                        "-DLLAMA_BUILD_TESTS=OFF", "-DLLAMA_BUILD_EXAMPLES=OFF",
                        "-DLLAMA_BUILD_SERVER=OFF", "-DLLAMA_BUILD_TOOLS=OFF"],
                       cwd=str(LLAMACPP_DIR), check=True)
        subprocess.run(["cmake", "--build", str(build_dir),
                        "--config", "Release", "--target", "llama-quantize", "-j4"],
                       cwd=str(LLAMACPP_DIR), check=True)
        quantize_bin = build_dir / "bin" / "Release" / "llama-quantize.exe"
        if not quantize_bin.exists():
            quantize_bin = build_dir / "bin" / "llama-quantize.exe"

    cmd = [str(quantize_bin), str(F16_GGUF), str(Q4KM_GGUF), "Q4_K_M"]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[OK] Q4_K_M: {Q4KM_GGUF}  ({Q4KM_GGUF.stat().st_size/1e6:.0f} MB)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only-merge",  action="store_true")
    ap.add_argument("--skip-merge",  action="store_true")
    ap.add_argument("--only-convert", action="store_true")
    args = ap.parse_args()

    if not args.skip_merge:
        step_merge()
    else:
        print(f"[SKIP] Merge — using {MERGED_DIR}")

    if args.only_merge:
        return

    step_convert_f16()

    if not args.only_convert:
        step_quantize()

    print("\n=== Done ===")
    print(f"  Merged HF : {MERGED_DIR}")
    print(f"  f16 GGUF  : {F16_GGUF}")
    print(f"  Q4_K_M    : {Q4KM_GGUF}")
    print(f"\nPush to phone:")
    print(f"  adb push {Q4KM_GGUF} /sdcard/Android/data/com.vintent.app/files/vidroidcall_v2_q4km.gguf")


if __name__ == "__main__":
    main()
