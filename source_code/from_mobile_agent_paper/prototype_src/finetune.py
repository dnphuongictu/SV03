"""Fine-tune Qwen2.5-0.5B-Instruct with LoRA on ViDroidCall v1.

Training data : prototype/data/eval/vi_droidcall_v1.jsonl  (210 samples)
Eval data     : prototype/data/eval/vi_smoke_test.jsonl    (32  samples, hold-out)
Output        : ../../models/qwen2.5-0.5b-vidroidcall-lora/

Usage (from prototype/ directory):
    python -X utf8 src/finetune.py
    python -X utf8 src/finetune.py --epochs 1
    python -X utf8 src/finetune.py --dry-run        # train on 20 examples, 1 epoch
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "eval"
TRAIN_PATH = DATA_DIR / "vi_droidcall_v1.jsonl"
EVAL_PATH = DATA_DIR / "vi_smoke_test.jsonl"
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
ADAPTER_DIR = ROOT.parent / "models" / "qwen2.5-0.5b-vidroidcall-lora"

BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

SYSTEM_PROMPT = """Bạn là bộ định tuyến công cụ Android chạy ngoại tuyến.
Chỉ trả về một JSON object, không giải thích.

Nếu yêu cầu đủ thông tin:
{"tool":"TOOL_NAME","arguments":{},"requires_confirmation":false}

Nếu thiếu thông tin:
{"tool":null,"arguments":{},"requires_confirmation":false,"status":"clarification","message":"..."}

Nếu không có công cụ phù hợp:
{"tool":null,"arguments":{},"requires_confirmation":false,"status":"unsupported"}

Không tự bịa tham số. Hành động có confirmation=true phải đặt
requires_confirmation=true.
"""


# ── helpers ────────────────────────────────────────────────────────────────────

def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def compact_tool(tool: dict) -> dict:
    return {
        "name": tool["name"],
        "description": tool["description_vi"],
        "confirmation": tool["confirmation"],
        "arguments": tool["arguments"],
    }


def build_messages(example: dict, selected_tools: list[dict]) -> list[dict]:
    user_content = json.dumps(
        {"tools": [compact_tool(t) for t in selected_tools], "user_query": example["query"]},
        ensure_ascii=False,
    )
    assistant_content = json.dumps(example["expected"], ensure_ascii=False)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
        {"role": "assistant", "content": assistant_content},
    ]


def prepare_dataset(examples: list[dict], tools: list[dict], top_k: int = 5) -> list[dict]:
    """Select tools per example (BM25 top-k, always include gold tool)."""
    sys.path.insert(0, str(Path(__file__).parent))
    from retrieve import BM25Retriever

    retriever = BM25Retriever(tools)
    tool_by_name = {t["name"]: t for t in tools}
    records = []
    for ex in examples:
        gold = ex["expected"].get("tool")
        ranking = retriever.search(ex["query"], top_k=top_k)
        names = [r["tool"] for r in ranking]
        # Ensure gold tool is always in context
        if gold and gold not in names:
            names = names[: top_k - 1] + [gold]
        selected = [tool_by_name[n] for n in names if n in tool_by_name]
        messages = build_messages(ex, selected)
        records.append({"messages": messages})
    return records


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-model", default=BASE_MODEL_ID)
    parser.add_argument("--train-path", type=Path, default=TRAIN_PATH,
                        help="Training JSONL path")
    parser.add_argument("--output", type=Path, default=ADAPTER_DIR)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=1,
                        help="per_device_train_batch_size (use 1 for CPU)")
    parser.add_argument("--grad-accum", type=int, default=4,
                        help="gradient_accumulation_steps")
    parser.add_argument("--max-seq-len", type=int, default=768)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--top-k", type=int, default=5,
                        help="BM25 top-k tools per training example")
    parser.add_argument("--dry-run", action="store_true",
                        help="Train on first 20 examples for 1 epoch (smoke test)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from last checkpoint in output dir if one exists")
    args = parser.parse_args()

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import LoraConfig
        from trl import SFTConfig, SFTTrainer
        from datasets import Dataset
    except ImportError as e:
        raise SystemExit(
            "Missing dependencies. Run: pip install transformers peft trl accelerate datasets"
        ) from e

    # ── load data ──────────────────────────────────────────────────────────────
    print("Loading training data …")
    tools = load_json(TOOLS_PATH)
    train_raw = load_jsonl(args.train_path)
    if args.dry_run:
        train_raw = train_raw[:20]
        args.epochs = 1
        print(f"[dry-run] Using {len(train_raw)} examples, 1 epoch")

    print(f"Preparing {len(train_raw)} training examples …")
    train_records = prepare_dataset(train_raw, tools, top_k=args.top_k)
    train_dataset = Dataset.from_list(train_records)

    # ── load tokenizer & model ─────────────────────────────────────────────────
    print(f"Loading tokenizer from {args.base_model} …")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading base model {args.base_model} …")
    t0 = time.perf_counter()
    import torch
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        dtype=torch.float32,  # CPU: always float32
    )
    print(f"Model loaded in {time.perf_counter() - t0:.1f}s")
    print(f"Parameters: {model.num_parameters() / 1e6:.1f}M")

    # ── LoRA config ────────────────────────────────────────────────────────────
    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable params (before LoRA): {trainable / 1e6:.1f}M")

    # ── training config ────────────────────────────────────────────────────────
    args.output.mkdir(parents=True, exist_ok=True)

    sft_config = SFTConfig(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.05,
        logging_steps=10,
        save_strategy="steps",
        save_steps=50,          # checkpoint every 50 optimizer steps → enables resume
        save_total_limit=3,     # keep latest 3 checkpoints
        fp16=False,
        bf16=False,
        max_length=args.max_seq_len,   # trl 1.5+ uses max_length (not max_seq_length)
        report_to="none",
        dataloader_pin_memory=False,
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_dataset,
        peft_config=lora_config,
        processing_class=tokenizer,
    )

    trainable_after = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Trainable params (after LoRA):  {trainable_after / 1e6:.1f}M")

    # ── train ──────────────────────────────────────────────────────────────────
    # Detect last checkpoint for resuming interrupted runs
    resume_ckpt = None
    if args.resume or (not args.dry_run):
        import glob as _glob
        ckpts = sorted(_glob.glob(str(args.output / "checkpoint-*")))
        if ckpts:
            resume_ckpt = ckpts[-1]
            print(f"Resuming from checkpoint: {resume_ckpt}")

    print(f"\nTraining {args.epochs} epoch(s) on {len(train_dataset)} examples …")
    if resume_ckpt is None:
        print("(CPU training — this may take a while)\n")
    t_start = time.perf_counter()
    trainer.train(resume_from_checkpoint=resume_ckpt)
    elapsed = time.perf_counter() - t_start
    print(f"\nTraining done in {elapsed / 60:.1f} min")

    # ── save ───────────────────────────────────────────────────────────────────
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    print(f"Adapter saved to {args.output}")

    # save training metadata for reproducibility
    meta = {
        "base_model": args.base_model,
        "train_examples": len(train_dataset),
        "epochs": args.epochs,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "lr": args.lr,
        "elapsed_min": round(elapsed / 60, 1),
    }
    (args.output / "training_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print("Done.")


if __name__ == "__main__":
    main()
