"""Evaluate a fine-tuned HuggingFace model (base + LoRA adapter) on vi_smoke_test.

Outputs predictions in the same JSONL format as model_baseline.py so the
existing evaluate.py can be reused without modification.

Usage (from prototype/ directory):
    python -X utf8 src/evaluate_ft.py \\
        --adapter ../../models/qwen2.5-0.5b-vidroidcall-lora

Optional flags:
    --retriever bm25|dense|hybrid   (default: bm25)
    --top-k N                       (default: 5)
    --fix-confirmation              (override from tool schema, recommended)
    --output results/model_ft_top5.jsonl
"""
from __future__ import annotations

import argparse
import inspect
import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
EVAL_PATH = ROOT / "data" / "eval" / "vi_smoke_test.jsonl"
RESULTS_DIR = ROOT / "results"

BASE_MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

_CONTACT_HONORIFICS = {
    "anh", "chi", "chị", "em", "co", "cô", "chu", "chú",
    "bac", "bác", "ong", "ông", "ba", "bà", "thay", "thầy", "ban", "bạn",
}


def _normalize_contact_name(name: str) -> str:
    """Strip honorific prefix and underscores (e.g. 'anh_minh' → 'Minh')."""
    cleaned = name.replace("_", " ").strip()
    parts = cleaned.split(None, 1)
    if len(parts) == 2 and parts[0].lower() in _CONTACT_HONORIFICS:
        return parts[1].strip()
    return cleaned


VALID_SETTINGS = {
    "wifi", "bluetooth", "mobile", "sound", "display", "battery",
    "storage", "security", "location", "accessibility", "language",
    "developer", "about", "all",
}

SETTING_MAP = {
    "ble": "bluetooth", "blue_tooth": "bluetooth", "bt": "bluetooth",
    "wi-fi": "wifi", "wi_fi": "wifi", "wireless": "wifi",
    "network": "mobile", "cellular": "mobile", "data": "mobile",
    "volume": "sound", "audio": "sound",
    "screen": "display", "brightness": "display",
    "power": "battery",
    "app": "storage",
    "privacy": "security",
    "gps": "location",
    "a11y": "accessibility",
    "locale": "language",
    "dev": "developer",
    "info": "about",
}

SYSTEM_PROMPT = """Bạn là bộ định tuyến công cụ Android chạy ngoại tuyến.
Chỉ trả về một JSON object, không giải thích.

Nếu yêu cầu đủ thông tin:
{"tool":"TOOL_NAME","arguments":{},"requires_confirmation":false}

Nếu thiếu thông tin:
{"tool":null,"arguments":{},"requires_confirmation":false,"status":"clarification","message":"..."}

Nếu không có công cụ phù hợp:
{"tool":null,"arguments":{},"requires_confirmation":false,"status":"unsupported"}

Không tự bịa tham số. Hành động có confirmation=true phải đặt requires_confirmation=true.
"""

ROBUST_PROMPT_SUFFIX = """
Ưu tiên độ chính xác tham số:
- Không thêm argument nếu người dùng không nói rõ.
- Với báo thức/lịch, giữ đúng giờ, phút, ngày lặp và chỉ thêm nhãn khi có nội dung nhắc.
- Với SMS/email, giữ nguyên người nhận, subject và body; không tóm tắt hoặc tự viết lại body.
- Phân biệt mở tài liệu lâu dài (ACTION_OPEN_DOCUMENT), lấy nội dung tạm thời (ACTION_GET_CONTENT), và tạo file mới (ACTION_CREATE_DOCUMENT).
- ACTION_IMAGE_CAPTURE dùng khi chụp ảnh ngay lập tức; INTENT_ACTION_STILL_IMAGE_CAMERA dùng khi mở ứng dụng camera.
- Loại bỏ khoảng trắng trong số điện thoại: "028 3823 4567" → "02838234567".
- Nếu thiếu người nhận, số điện thoại, email, nội dung, thời gian hoặc đối tượng cụ thể thì dùng tool null với status "clarification".
- Nếu yêu cầu nằm ngoài danh sách công cụ thì dùng tool null với status "unsupported".
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


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_resume_jsonl(path: Path) -> list[dict]:
    """Load streamed rows, repairing only a truncated final line."""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows = []
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if index != len(lines) - 1:
                raise
            print(f"Resume: discarding truncated final line in {path}")
            write_jsonl(path, rows)
    return rows


def compact_tool(tool: dict) -> dict:
    return {
        "name": tool["name"],
        "description": tool["description_vi"],
        "confirmation": tool["confirmation"],
        "arguments": tool["arguments"],
    }


def extract_json(text: str) -> dict:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            return {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "rejected"}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "rejected"}


def build_retriever(
    name: str,
    tools: list[dict],
    alpha: float = 0.5,
    dense_revision: str | None = None,
):
    sys.path.insert(0, str(Path(__file__).parent))
    if name == "bm25":
        from retrieve import BM25Retriever
        return BM25Retriever(tools)
    elif name == "dense":
        from dense_retriever import DenseRetriever
        return DenseRetriever(tools, revision=dense_revision)
    elif name == "hybrid":
        from hybrid_retriever import HybridRetriever
        return HybridRetriever(tools, alpha=alpha, revision=dense_revision)
    else:
        raise ValueError(f"Unknown retriever: {name}")


def make_peft_compatible_adapter(adapter_path: Path, work_dir: Path) -> Path:
    """Copy and sanitize a newer LoRA config for the installed PEFT version."""
    from peft import LoraConfig

    config_path = adapter_path / "adapter_config.json"
    raw_config = load_json(config_path)
    allowed = set(inspect.signature(LoraConfig.__init__).parameters) - {"self"}
    allowed |= {"peft_type", "task_type"}
    removed = sorted(set(raw_config) - allowed)
    if not removed:
        return adapter_path

    compatible_path = work_dir / "_adapter_peft_compat"
    if compatible_path.exists():
        shutil.rmtree(compatible_path)
    shutil.copytree(adapter_path, compatible_path)
    compatible_config = {key: value for key, value in raw_config.items() if key in allowed}
    (compatible_path / "adapter_config.json").write_text(
        json.dumps(compatible_config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"PEFT compatibility: removed adapter config keys: {removed}")
    return compatible_path


# ── main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", type=Path, required=False, default=None,
                        help="Path to LoRA adapter directory (omit for zero-shot baseline)")
    parser.add_argument("--base-model", default=BASE_MODEL_ID)
    parser.add_argument("--base-revision", default=None)
    parser.add_argument("--dense-revision", default=None)
    parser.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="bm25")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--alpha", type=float, default=0.5,
                        help="BM25/dense interpolation weight for hybrid retriever (default=0.5)")
    parser.add_argument("--fix-confirmation", action="store_true",
                        help="Override requires_confirmation from tool schema")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--robust-prompt", action="store_true",
                        help="Append external-robust guidance to the system prompt")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--eval-path", type=Path, default=None,
                        help="Path to eval JSONL (default: data/eval/vi_smoke_test.jsonl)")
    parser.add_argument(
        "--retrieval-reference",
        type=Path,
        default=None,
        help=(
            "Optional JSONL whose retrieved_tools must match exactly. Matching "
            "rankings are cached and reused for inference."
        ),
    )
    parser.add_argument("--stream-output", action="store_true",
                        help="Write each prediction immediately instead of only at the end.")
    parser.add_argument("--resume", action="store_true",
                        help="Keep valid rows already in --output and skip their IDs.")
    parser.add_argument("--require-cuda", action="store_true",
                        help="Fail immediately instead of silently running slow CPU inference.")
    parser.add_argument(
        "--confirmation-only-postprocessing",
        action="store_true",
        help=(
            "Match the successful fresh-locked Kaggle v3 protocol: after JSON "
            "extraction, apply only the optional schema confirmation override."
        ),
    )
    parser.add_argument(
        "--protocol-id",
        default=None,
        help="Embed a protocol identifier in every row and enforce it when resuming.",
    )
    args = parser.parse_args()

    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if args.adapter is not None:
            from peft import PeftModel
    except ImportError as e:
        raise SystemExit("Run: pip install transformers peft") from e

    # ── load retriever & data ──────────────────────────────────────────────────
    tools = load_json(TOOLS_PATH)
    tool_by_name = {t["name"]: t for t in tools}
    eval_path = args.eval_path if args.eval_path else EVAL_PATH
    examples = load_jsonl(eval_path)
    if args.output is None:
        suffix = f"_ft_{args.retriever}_top{args.top_k}"
        if args.fix_confirmation:
            suffix += "_fixconf"
        args.output = RESULTS_DIR / f"model{suffix}.jsonl"

    rows: list[dict] = []
    completed_ids: set[str] = set()
    if args.resume and args.output.exists():
        rows = load_resume_jsonl(args.output)
        completed_ids = {str(row.get("id")) for row in rows if row.get("id") is not None}
        if len(completed_ids) != len(rows):
            raise SystemExit(
                f"Cannot resume {args.output}: duplicate or missing prediction IDs."
            )
        if args.protocol_id is not None:
            existing_protocols = {row.get("protocol_id") for row in rows}
            if existing_protocols != {args.protocol_id}:
                raise SystemExit(
                    f"Cannot resume {args.output}: protocol IDs "
                    f"{sorted(map(str, existing_protocols))} do not match "
                    f"{args.protocol_id!r}. Start a clean output or attach a "
                    "partial file produced by this exact package."
                )
        print(f"Resume: found {len(rows)} completed predictions in {args.output}")
        expected_ids = {str(example["id"]) for example in examples}
        extra_ids = completed_ids - expected_ids
        if extra_ids:
            raise SystemExit(
                f"Cannot resume {args.output}: unexpected IDs "
                f"{sorted(extra_ids)}."
            )
        if completed_ids == expected_ids:
            print("Resume: all predictions are already complete; no model load needed.")
            return

    print(f"Building {args.retriever} retriever (alpha={args.alpha}) …")
    retriever = build_retriever(
        args.retriever,
        tools,
        alpha=args.alpha,
        dense_revision=args.dense_revision,
    )
    precomputed_rankings: dict[str, list[dict]] = {}
    if args.retrieval_reference is not None:
        reference_rows = load_jsonl(args.retrieval_reference)
        reference = {
            str(row["id"]): row.get("retrieved_tools")
            for row in reference_rows
        }
        expected_ids = {str(example["id"]) for example in examples}
        if set(reference) != expected_ids:
            raise SystemExit(
                f"Retrieval reference IDs do not match the eval set: "
                f"{args.retrieval_reference}"
            )
        mismatches = []
        for example in examples:
            ranking = retriever.search(example["query"], top_k=args.top_k)
            actual_tools = [row["tool"] for row in ranking]
            expected_tools = reference[str(example["id"])]
            if actual_tools != expected_tools:
                mismatches.append(
                    {
                        "id": example["id"],
                        "expected": expected_tools,
                        "actual": actual_tools,
                    }
                )
            precomputed_rankings[str(example["id"])] = ranking
        if mismatches:
            raise SystemExit(
                "Frozen retrieval check failed before model loading. First "
                f"mismatches: {mismatches[:3]}"
            )
        print(
            f"Verified frozen retrieved-tools rankings: "
            f"{len(precomputed_rankings)}/{len(examples)}"
        )

    # ── load model + adapter ───────────────────────────────────────────────────
    # Load tokenizer from base model — adapter tokenizer_config may have version
    # incompatibilities when saved on a different transformers version (e.g. Colab).
    print(f"Loading tokenizer from {args.base_model} …")
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        revision=args.base_revision,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading base model {args.base_model} …")
    import torch
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if args.require_cuda and device.type != "cuda":
        raise SystemExit(
            "CUDA is unavailable. Enable a Kaggle GPU accelerator before running; "
            "CPU inference is too slow for this evaluation."
        )
    dtype = torch.float16 if device.type == "cuda" else torch.float32
    print(f"Using device={device}, torch_dtype={dtype}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        revision=args.base_revision,
        trust_remote_code=True,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )
    if args.adapter is not None:
        compatible_adapter = make_peft_compatible_adapter(
            args.adapter.resolve(),
            args.output.parent,
        )
        adapter_path = str(compatible_adapter)
        print(f"Loading LoRA adapter from {adapter_path} …")
        model = PeftModel.from_pretrained(base_model, adapter_path)
        model = model.merge_and_unload()  # merge for faster inference
    else:
        print("No adapter — running zero-shot with base model.")
        model = base_model
    model.to(device)
    model.eval()
    print("Model ready.\n")

    # ── run inference ──────────────────────────────────────────────────────────
    stream_handle = None
    if args.stream_output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        stream_mode = "a" if args.resume and args.output.exists() else "w"
        stream_handle = args.output.open(stream_mode, encoding="utf-8")

    try:
        for i, example in enumerate(examples, 1):
            if example["id"] in completed_ids:
                print(
                    f"[{i:3d}/{len(examples)}] {example['id']}: already complete, skipping",
                    flush=True,
                )
                continue
            ranking = precomputed_rankings.get(str(example["id"]))
            if ranking is None:
                ranking = retriever.search(example["query"], top_k=args.top_k)
            selected = [tool_by_name[r["tool"]] for r in ranking if r["tool"] in tool_by_name]

            user_content = json.dumps(
                {"tools": [compact_tool(t) for t in selected], "user_query": example["query"]},
                ensure_ascii=False,
            )
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT + (ROBUST_PROMPT_SUFFIX if args.robust_prompt else ""),
                },
                {"role": "user", "content": user_content},
            ]
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = tokenizer(text, return_tensors="pt")
            inputs = {key: value.to(device) for key, value in inputs.items()}

            t0 = time.perf_counter()
            import torch
            with torch.no_grad():
                output_ids = model.generate(
                    **inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,          # greedy (temperature=0 equivalent)
                    pad_token_id=tokenizer.pad_token_id,
                )
            elapsed_ms = (time.perf_counter() - t0) * 1000

            # Decode only the newly generated tokens
            new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
            content = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
            prediction = extract_json(content)

            if not args.confirmation_only_postprocessing:
                if prediction.get("tool") == "open_settings":
                    st = prediction.get("arguments", {}).get("setting_type", "")
                    if st and st not in VALID_SETTINGS:
                        prediction["arguments"]["setting_type"] = SETTING_MAP.get(st.lower(), st)

                if prediction.get("tool") in {"get_contact_info", "make_phone_call"}:
                    args_dict = prediction.get("arguments", {})
                    if isinstance(args_dict, dict) and isinstance(args_dict.get("name"), str):
                        args_dict["name"] = _normalize_contact_name(args_dict["name"])

            if args.fix_confirmation and prediction.get("tool") in tool_by_name:
                prediction["requires_confirmation"] = tool_by_name[prediction["tool"]]["confirmation"]

            row = {
                "id": example["id"],
                "prediction": prediction,
                "raw_output": content,
                "latency_ms": round(elapsed_ms, 3),
                "retrieved_tools": [t["name"] for t in selected],
                "retriever": args.retriever,
                "protocol_id": args.protocol_id,
            }
            rows.append(row)
            if stream_handle:
                stream_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                stream_handle.flush()
            print(f"[{i:3d}/{len(examples)}] {example['id']}: tool={prediction.get('tool')} ({elapsed_ms:.0f}ms)", flush=True)
    finally:
        if stream_handle:
            stream_handle.close()

    # ── save predictions ───────────────────────────────────────────────────────
    if not args.stream_output:
        write_jsonl(args.output, rows)
    print(f"\nWrote {len(rows)} predictions to {args.output}")
    print(f"Run: python -X utf8 src/evaluate.py {args.output} --output {args.output.with_suffix('').name}_report.json")


if __name__ == "__main__":
    main()
