from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from common import EVAL_PATH, RESULTS_DIR, TOOLS_PATH, load_json, load_jsonl, write_jsonl
from constrained import make_grammar
from retrieve import BM25Retriever


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


def compact_tool(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool["description_vi"],
        "confirmation": tool["confirmation"],
        "arguments": tool["arguments"],
    }


def extract_json(text: str) -> dict[str, Any]:
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not match:
            return {
                "tool": None,
                "arguments": {},
                "requires_confirmation": False,
                "status": "rejected",
            }
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {
                "tool": None,
                "arguments": {},
                "requires_confirmation": False,
                "status": "rejected",
            }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True, help="GGUF model path")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--all-tools", action="store_true")
    parser.add_argument("--constrained", action="store_true",
                        help="Use llama.cpp grammar to constrain output to valid JSON schema")
    parser.add_argument("--fix-confirmation", action="store_true",
                        help="Override requires_confirmation with the tool schema value after generation")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--context", type=int, default=4096)
    args = parser.parse_args()

    try:
        from llama_cpp import Llama
    except ImportError as error:
        raise SystemExit(
            "Install llama-cpp-python before running the model baseline."
        ) from error

    tools = load_json(TOOLS_PATH)
    tool_by_name = {tool["name"]: tool for tool in tools}
    retriever = BM25Retriever(tools)
    examples = load_jsonl(EVAL_PATH)
    model = Llama(
        model_path=str(args.model),
        n_ctx=args.context,
        n_threads=args.threads,
        verbose=False,
    )

    rows = []
    for example in examples:
        if args.all_tools:
            selected = tools
        else:
            ranking = retriever.search(example["query"], top_k=args.top_k)
            selected = [tool_by_name[item["tool"]] for item in ranking]

        user_prompt = json.dumps(
            {
                "tools": [compact_tool(tool) for tool in selected],
                "user_query": example["query"],
            },
            ensure_ascii=False,
        )
        grammar = make_grammar([t["name"] for t in selected]) if args.constrained else None

        start = time.perf_counter()
        response = model.create_chat_completion(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=256,
            grammar=grammar,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        content = response["choices"][0]["message"]["content"]
        prediction = extract_json(content)

        # Post-process: override requires_confirmation from tool schema
        if args.fix_confirmation and prediction.get("tool") in tool_by_name:
            prediction["requires_confirmation"] = tool_by_name[prediction["tool"]]["confirmation"]

        rows.append(
            {
                "id": example["id"],
                "prediction": prediction,
                "raw_output": content,
                "latency_ms": round(elapsed_ms, 3),
                "prompt_tokens": response.get("usage", {}).get("prompt_tokens"),
                "completion_tokens": response.get("usage", {}).get("completion_tokens"),
                "retrieved_tools": [tool["name"] for tool in selected],
                "constrained": args.constrained,
            }
        )

    mode = "all" if args.all_tools else f"top_{args.top_k}"
    suffix = ("_constrained" if args.constrained else "") + ("_fixconf" if args.fix_confirmation else "")
    output_path = RESULTS_DIR / f"model_baseline_{mode}{suffix}.jsonl"
    write_jsonl(output_path, rows)
    print(f"Wrote {len(rows)} predictions to {output_path}")


if __name__ == "__main__":
    main()

