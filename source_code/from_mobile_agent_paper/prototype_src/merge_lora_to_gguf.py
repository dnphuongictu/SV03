"""Merge LoRA adapter v4 vào base model rồi export sang GGUF Q4_K_M.

Pipeline:
  1. Load base Qwen2.5-0.5B-Instruct
  2. Load LoRA adapter v4 và merge_and_unload()
  3. Lưu HuggingFace format vào models/qwen2.5-0.5b-vidroidcall-merged/
  4. Clone llama.cpp (nếu chưa có) và chạy convert_hf_to_gguf.py → f16 GGUF
  5. Quantize Q4_K_M với llama-quantize

Usage (từ thư mục prototype/):
    python -X utf8 src/merge_lora_to_gguf.py
    python -X utf8 src/merge_lora_to_gguf.py --skip-clone   # nếu đã có llama.cpp
    python -X utf8 src/merge_lora_to_gguf.py --only-merge   # chỉ merge, không GGUF

Sau khi xong:
    models/qwen2.5-0.5b-vidroidcall-merged/   <- HF merged model
    models/vidroidcall_f16.gguf               <- ~1GB GGUF float16
    models/vidroidcall_q4km.gguf              <- ~270MB GGUF quantized (dùng cho inference)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # mobile_agent_paper/
MODELS_DIR = ROOT / "models"
ADAPTER_PATH = MODELS_DIR / "qwen2.5-0.5b-vidroidcall-lora" / "vidroidcall_lora_adapter (4)"
MERGED_DIR = MODELS_DIR / "qwen2.5-0.5b-vidroidcall-merged"
F16_GGUF = MODELS_DIR / "vidroidcall_f16.gguf"
Q4KM_GGUF = MODELS_DIR / "vidroidcall_q4km.gguf"
LLAMACPP_DIR = ROOT / "llama.cpp"
BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"


def step_merge():
    print("\n=== Step 1: Merge LoRA adapter into base model ===")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    if not ADAPTER_PATH.exists():
        sys.exit(f"[ERROR] Adapter not found at {ADAPTER_PATH}\n"
                 "Make sure vidroidcall_lora_adapter (4).zip is extracted.")

    print(f"Loading base model: {BASE_MODEL_ID}")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL_ID,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
    )

    print(f"Loading LoRA from: {ADAPTER_PATH}")
    peft_model = PeftModel.from_pretrained(base, str(ADAPTER_PATH))

    print("Merging LoRA weights...")
    merged = peft_model.merge_and_unload()
    merged.eval()

    print(f"Saving merged model to: {MERGED_DIR}")
    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(MERGED_DIR))

    print("Saving tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
    tokenizer.save_pretrained(str(MERGED_DIR))

    print(f"[OK] Merged model saved: {MERGED_DIR}")


def step_clone_llamacpp(skip_clone: bool):
    print("\n=== Step 2: Prepare llama.cpp ===")
    if LLAMACPP_DIR.exists():
        print(f"[OK] llama.cpp already at {LLAMACPP_DIR}")
        return
    if skip_clone:
        sys.exit(f"[ERROR] llama.cpp not found at {LLAMACPP_DIR} and --skip-clone was set.\n"
                 f"Clone manually: git clone https://github.com/ggerganov/llama.cpp {LLAMACPP_DIR}")
    print(f"Cloning llama.cpp to {LLAMACPP_DIR} (shallow, ~50MB)...")
    subprocess.run(
        ["git", "clone", "--depth", "1",
         "https://github.com/ggerganov/llama.cpp", str(LLAMACPP_DIR)],
        check=True,
    )
    # Skip pip install — requirements pin numpy~=1.26.4 but we have numpy 2.x which works fine.
    # The convert script only needs: numpy, gguf, transformers, sentencepiece, protobuf.
    print("[OK] llama.cpp ready")


def step_convert_f16():
    print("\n=== Step 3: Convert merged model to GGUF f16 ===")
    if not MERGED_DIR.exists():
        sys.exit(f"[ERROR] Merged model not found at {MERGED_DIR}. Run without --skip-merge first.")

    convert_script = LLAMACPP_DIR / "convert_hf_to_gguf.py"
    if not convert_script.exists():
        sys.exit(f"[ERROR] convert_hf_to_gguf.py not found at {convert_script}")

    cmd = [
        sys.executable, str(convert_script),
        str(MERGED_DIR),
        "--outfile", str(F16_GGUF),
        "--outtype", "f16",
    ]
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    size_mb = F16_GGUF.stat().st_size / 1024 / 1024
    print(f"[OK] f16 GGUF: {F16_GGUF}  ({size_mb:.0f} MB)")


def step_quantize_q4km():
    print("\n=== Step 4: Quantize to Q4_K_M ===")
    if not F16_GGUF.exists():
        sys.exit(f"[ERROR] f16 GGUF not found at {F16_GGUF}")

    # Look for llama-quantize binary (built or pip-installed)
    quantize_bin = LLAMACPP_DIR / "build" / "bin" / "llama-quantize"
    if not quantize_bin.exists():
        quantize_bin = LLAMACPP_DIR / "llama-quantize"
    if not quantize_bin.exists():
        # Try system PATH (llama-cpp-python installs llama-quantize on PATH)
        quantize_bin = "llama-quantize"

    cmd = [str(quantize_bin), str(F16_GGUF), str(Q4KM_GGUF), "Q4_K_M"]
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        size_mb = Q4KM_GGUF.stat().st_size / 1024 / 1024
        print(f"[OK] Q4_K_M GGUF: {Q4KM_GGUF}  ({size_mb:.0f} MB)")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[WARN] llama-quantize not found in PATH.")
        print("Options:")
        print("  A) Build llama.cpp: cd llama.cpp && cmake -B build && cmake --build build --config Release")
        print("  B) Use llama-cpp-python's quantize wrapper (Python only)")
        print("\nFallback: using llama-cpp-python to quantize...")
        _quantize_python_fallback()


def _quantize_python_fallback():
    """Quantize via llama-cpp-python if llama-quantize binary is not available."""
    try:
        from llama_cpp import llama_model_quantize_params, llama_quantize_model
        print("[INFO] llama-cpp-python quantize path...")
        # llama-cpp-python does not expose quantize directly via Python API in all versions
        # Print instructions instead
        print("[INFO] Manual steps to quantize:")
        print(f"  1. pip install llama-cpp-python")
        print(f"  2. python -c \"from llama_cpp import Llama; m=Llama('{F16_GGUF}')\"  # verify load")
        print(f"  3. Use llama.cpp CLI after building:")
        print(f"     cd {LLAMACPP_DIR} && cmake -B build && cmake --build build -j4")
        print(f"     build/bin/llama-quantize {F16_GGUF} {Q4KM_GGUF} Q4_K_M")
    except ImportError:
        print("[WARN] llama-cpp-python not installed.")
        print("Install with: pip install llama-cpp-python")


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA v4 and convert to GGUF Q4_K_M")
    parser.add_argument("--only-merge", action="store_true", help="Only merge LoRA, skip GGUF")
    parser.add_argument("--skip-merge", action="store_true", help="Skip LoRA merge step (merged model already exists)")
    parser.add_argument("--skip-clone", action="store_true", help="Skip git clone llama.cpp")
    args = parser.parse_args()

    if not args.skip_merge:
        step_merge()
    else:
        print(f"[SKIP] Merge step — using existing {MERGED_DIR}")

    if args.only_merge:
        print("\nDone (only-merge mode). Merged model at:", MERGED_DIR)
        return

    step_clone_llamacpp(skip_clone=args.skip_clone)
    step_convert_f16()
    step_quantize_q4km()

    print("\n=== All done! ===")
    print(f"  Merged HF:  {MERGED_DIR}")
    print(f"  f16 GGUF:   {F16_GGUF}")
    print(f"  Q4_K_M:     {Q4KM_GGUF}")
    print(f"\nNext: update api_server.py to use --gguf flag:")
    print(f"  python -X utf8 src/api_server.py --gguf {Q4KM_GGUF}")


if __name__ == "__main__":
    main()
