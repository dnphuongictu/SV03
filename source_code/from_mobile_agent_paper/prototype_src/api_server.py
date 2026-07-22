"""FastAPI server bọc toàn bộ VIntentAgent pipeline.

Usage (từ thư mục prototype/):
    # Transformers backend (mặc định, ~12s/query trên CPU):
    python -X utf8 src/api_server.py

    # GGUF backend (~2-4s/query trên CPU):
    python -X utf8 src/api_server.py --gguf ../../models/vidroidcall_q4km.gguf

    # Tuỳ chỉnh:
    python -X utf8 src/api_server.py --adapter "../../models/.../adapter (4)" --retriever hybrid

Endpoint:
    POST /predict
    Body: {"query": "Đặt báo thức 7 giờ sáng"}
    Response: {"tool": "ACTION_SET_ALARM", "arguments": {...}, "requires_confirmation": false,
               "retrieved_tools": [...], "latency_ms": 1234}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
DEFAULT_ADAPTER = ROOT.parent / "models" / "qwen2.5-0.5b-vidroidcall-lora" / "vidroidcall_lora_adapter (4)"
DEFAULT_GGUF = ROOT.parent / "models" / "vidroidcall_q4km.gguf"
BASE_MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

_CONTACT_HONORIFICS = {
    "anh", "chi", "chị", "em", "co", "cô", "chu", "chú",
    "bac", "bác", "ong", "ông", "ba", "bà", "thay", "thầy", "ban", "bạn",
}

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

Không tự bịa tham số. Hành động có confirmation=true phải đặt
requires_confirmation=true.
"""


def _normalize_contact_name(name: str) -> str:
    cleaned = name.replace("_", " ").strip()
    parts = cleaned.split(None, 1)
    if len(parts) == 2 and parts[0].lower() in _CONTACT_HONORIFICS:
        return parts[1].strip()
    return cleaned


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def post_process(prediction: dict, tool_by_name: dict, fix_confirmation: bool) -> dict:
    tool = prediction.get("tool")

    if tool == "open_settings":
        st = prediction.get("arguments", {}).get("setting_type", "")
        if st and st not in VALID_SETTINGS:
            prediction["arguments"]["setting_type"] = SETTING_MAP.get(st.lower(), st)

    if tool in {"get_contact_info", "make_phone_call"}:
        args_dict = prediction.get("arguments", {})
        if isinstance(args_dict, dict) and isinstance(args_dict.get("name"), str):
            args_dict["name"] = _normalize_contact_name(args_dict["name"])

    if fix_confirmation and tool in tool_by_name:
        prediction["requires_confirmation"] = tool_by_name[tool]["confirmation"]

    return prediction


# ── Global pipeline state ──────────────────────────────────────────────────────

class Pipeline:
    def __init__(self):
        self.tools: list[dict] = []
        self.tool_by_name: dict = {}
        self.retriever = None
        self.tokenizer = None
        self.model = None          # Transformers model
        self.llm_gguf = None       # llama-cpp-python Llama instance
        self.use_gguf = False
        self.top_k = 5
        self.fix_confirmation = True
        self.max_new_tokens = 256

    def _load_retriever(self, retriever_name: str):
        sys.path.insert(0, str(Path(__file__).parent))
        if retriever_name == "bm25":
            from retrieve import BM25Retriever
            self.retriever = BM25Retriever(self.tools)
        elif retriever_name == "dense":
            from dense_retriever import DenseRetriever
            self.retriever = DenseRetriever(self.tools)
        elif retriever_name == "hybrid":
            from hybrid_retriever import HybridRetriever
            self.retriever = HybridRetriever(self.tools)

    def load(self, adapter_path: Path, retriever_name: str, top_k: int, fix_confirmation: bool):
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        print(f"Loading tools from {TOOLS_PATH}")
        self.tools = load_json(TOOLS_PATH)
        self.tool_by_name = {t["name"]: t for t in self.tools}
        self.top_k = top_k
        self.fix_confirmation = fix_confirmation
        self.use_gguf = False

        print(f"Building {retriever_name} retriever...")
        self._load_retriever(retriever_name)

        print(f"Loading tokenizer from {BASE_MODEL_ID}...")
        self.tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_ID, trust_remote_code=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        print(f"Loading base model...")
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_ID,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
        )
        print(f"Loading LoRA adapter from {adapter_path}...")
        peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))
        self.model = peft_model.merge_and_unload()
        self.model.eval()
        print("Pipeline ready (Transformers backend).\n")

    def load_gguf(self, gguf_path: Path, retriever_name: str, top_k: int, fix_confirmation: bool,
                  n_ctx: int = 2048, n_threads: int = 8):
        from llama_cpp import Llama

        print(f"Loading tools from {TOOLS_PATH}")
        self.tools = load_json(TOOLS_PATH)
        self.tool_by_name = {t["name"]: t for t in self.tools}
        self.top_k = top_k
        self.fix_confirmation = fix_confirmation
        self.use_gguf = True

        print(f"Building {retriever_name} retriever...")
        self._load_retriever(retriever_name)

        print(f"Loading GGUF model from {gguf_path} (n_ctx={n_ctx}, n_threads={n_threads})...")
        self.llm_gguf = Llama(
            model_path=str(gguf_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            verbose=False,
        )
        print("Pipeline ready (GGUF/llama-cpp backend).\n")

    def _build_prompt(self, query: str) -> tuple[list[dict], list[dict]]:
        ranking = self.retriever.search(query, top_k=self.top_k)
        selected = [self.tool_by_name[r["tool"]] for r in ranking if r["tool"] in self.tool_by_name]
        user_content = json.dumps(
            {"tools": [compact_tool(t) for t in selected], "user_query": query},
            ensure_ascii=False,
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]
        return messages, selected

    def predict(self, query: str) -> dict:
        messages, selected = self._build_prompt(query)

        if self.use_gguf:
            return self._predict_gguf(messages, selected)
        else:
            return self._predict_transformers(messages, selected)

    def _predict_transformers(self, messages: list[dict], selected: list[dict]) -> dict:
        import torch

        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(text, return_tensors="pt")

        t0 = time.perf_counter()
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id,
            )
        latency_ms = (time.perf_counter() - t0) * 1000

        new_ids = output_ids[0][inputs["input_ids"].shape[1]:]
        raw_output = self.tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        prediction = extract_json(raw_output)
        prediction = post_process(prediction, self.tool_by_name, self.fix_confirmation)
        return {
            **prediction,
            "retrieved_tools": [t["name"] for t in selected],
            "latency_ms": round(latency_ms, 1),
            "raw_output": raw_output,
        }

    def _predict_gguf(self, messages: list[dict], selected: list[dict]) -> dict:
        t0 = time.perf_counter()
        response = self.llm_gguf.create_chat_completion(
            messages=messages,
            max_tokens=self.max_new_tokens,
            temperature=0.0,
        )
        latency_ms = (time.perf_counter() - t0) * 1000

        raw_output = response["choices"][0]["message"]["content"].strip()
        prediction = extract_json(raw_output)
        prediction = post_process(prediction, self.tool_by_name, self.fix_confirmation)
        return {
            **prediction,
            "retrieved_tools": [t["name"] for t in selected],
            "latency_ms": round(latency_ms, 1),
            "raw_output": raw_output,
        }


pipeline = Pipeline()

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(title="VIntentAgent API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    query: str


class PredictResponse(BaseModel):
    tool: Optional[str] = None
    arguments: dict = {}
    requires_confirmation: bool = False
    status: Optional[str] = None
    message: Optional[str] = None
    retrieved_tools: list[str] = []
    latency_ms: float = 0.0
    raw_output: str = ""


@app.get("/health")
def health():
    loaded = (pipeline.model is not None) or (pipeline.llm_gguf is not None)
    backend = "gguf" if pipeline.use_gguf else "transformers"
    return {"status": "ok", "model_loaded": loaded, "backend": backend}


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    if pipeline.model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Empty query")
    result = pipeline.predict(req.query)
    return result


# ── CLI entrypoint ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="VIntentAgent API Server")
    # GGUF backend (fast)
    parser.add_argument("--gguf", type=Path, default=None,
                        help="Path to .gguf model file. Uses llama-cpp-python backend (~2-4s/query).")
    parser.add_argument("--n-threads", type=int, default=8, help="CPU threads for GGUF inference")
    parser.add_argument("--n-ctx", type=int, default=2048, help="Context length for GGUF inference")
    # Transformers backend
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER,
                        help="LoRA adapter path (Transformers backend, ~12s/query)")
    # Shared
    parser.add_argument("--retriever", choices=["bm25", "dense", "hybrid"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--no-fix-confirmation", action="store_true")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.gguf is not None:
        gguf_path = args.gguf if args.gguf.is_absolute() else Path.cwd() / args.gguf
        if not gguf_path.exists():
            parser.error(f"GGUF file not found: {gguf_path}\n"
                         f"Run: python -X utf8 src/merge_lora_to_gguf.py")
        pipeline.load_gguf(
            gguf_path=gguf_path,
            retriever_name=args.retriever,
            top_k=args.top_k,
            fix_confirmation=not args.no_fix_confirmation,
            n_ctx=args.n_ctx,
            n_threads=args.n_threads,
        )
    else:
        pipeline.load(
            adapter_path=args.adapter,
            retriever_name=args.retriever,
            top_k=args.top_k,
            fix_confirmation=not args.no_fix_confirmation,
        )

    print(f"Starting server at http://{args.host}:{args.port}")
    print(f"Test: curl -X POST http://localhost:{args.port}/predict -H 'Content-Type: application/json' -d '{{\"query\":\"Đặt báo thức 7 giờ sáng\"}}'")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
