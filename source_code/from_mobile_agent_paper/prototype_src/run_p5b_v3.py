"""P5b — Robustness eval với adapter v3_cs (Qwen2.5-1.5B, augmented dataset).

Giống run_p5b_v21.py nhưng dùng v3_cs adapter và so sánh với v2.1 baseline.

Usage:
    cd prototype
    python -X utf8 src/run_p5b_v3.py
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
RESULTS_DIR = ROOT / "results"

ADAPTER_PATH = (ROOT.parent / "models" / "qwen2.5-1.5b-vidroidcall-lora"
                / "vidroidcall_lora_adapter_v3_cs")
BASE_MODEL   = "Qwen/Qwen2.5-1.5B-Instruct"
TOP_K        = 5
RETRIEVER    = "hybrid"

EVAL_SETS = [
    ("v3_noisy_light",   ROOT / "data" / "eval" / "noisy_smoke_light.jsonl"),
    ("v3_noisy_medium",  ROOT / "data" / "eval" / "noisy_smoke_medium.jsonl"),
    ("v3_noisy_heavy",   ROOT / "data" / "eval" / "noisy_smoke_heavy.jsonl"),
    ("v3_codeswitch",    ROOT / "data" / "eval" / "codeswitch_queries.jsonl"),
]

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

_HONORIFICS = {"anh","chi","chị","em","co","cô","chu","chú",
               "bac","bác","ong","ông","ba","bà","thay","thầy","ban","bạn"}

VALID_SETTINGS = {
    "wifi","bluetooth","mobile","sound","display","battery",
    "storage","security","location","accessibility","language",
    "developer","about","all",
}
SETTING_MAP = {
    "ble":"bluetooth","bt":"bluetooth","wi-fi":"wifi","wi_fi":"wifi",
    "wireless":"wifi","network":"mobile","cellular":"mobile","data":"mobile",
    "volume":"sound","audio":"sound","screen":"display","brightness":"display",
    "power":"battery","app":"storage","privacy":"security","gps":"location",
    "a11y":"accessibility","locale":"language","dev":"developer","info":"about",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

def write_jsonl(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8"
    )

def extract_json(text):
    stripped = text.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
        if not m:
            return {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "rejected"}
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "rejected"}

def normalize_contact(name):
    cleaned = name.replace("_", " ").strip()
    parts = cleaned.split(None, 1)
    if len(parts) == 2 and parts[0].lower() in _HONORIFICS:
        return parts[1].strip()
    return cleaned

def compute_report(examples, predictions, tool_by_name):
    n = len(examples)
    tool_ok = schema_ok = e2e_ok = 0
    arg_sum = 0.0
    errors = []
    groups: dict = {}

    for ex, pred in zip(examples, predictions):
        exp = ex["expected"]
        exp_tool  = exp.get("tool")
        pred_tool = pred.get("tool")
        g = ex.get("group", "other")
        groups.setdefault(g, {"count":0,"tool_selection_accuracy":0,"schema_valid_rate":0,"end_to_end_task_success":0})
        groups[g]["count"] += 1

        t_ok = (exp_tool == pred_tool)
        if t_ok:
            tool_ok += 1
            groups[g]["tool_selection_accuracy"] += 1

        if t_ok and exp_tool is not None:
            schema_def  = tool_by_name.get(exp_tool, {})
            req_args    = [k for k,v in schema_def.get("arguments",{}).items() if v.get("required")]
            pred_args   = pred.get("arguments", {})
            exp_args    = exp.get("arguments", {})
            sv = all(k in pred_args and pred_args[k] not in (None,"") for k in req_args)
            if sv:
                schema_ok += 1
                groups[g]["schema_valid_rate"] += 1
            if req_args:
                matched = sum(
                    1 for k in req_args
                    if str(pred_args.get(k,"")).lower().strip() and
                       str(exp_args.get(k,"")).lower().strip() and
                       (str(pred_args.get(k,"")).lower().strip() in str(exp_args.get(k,"")).lower().strip() or
                        str(exp_args.get(k,"")).lower().strip() in str(pred_args.get(k,"")).lower().strip())
                )
                arg_sum += matched / len(req_args)
            else:
                arg_sum += 1.0
            if sv:
                e2e_ok += 1
                groups[g]["end_to_end_task_success"] += 1
            else:
                errors.append({"id": ex.get("id"), "query": ex.get("query",""),
                               "expected_tool": exp_tool, "reason": "missing_args"})
        elif t_ok and exp_tool is None:
            schema_ok += 1; e2e_ok += 1; arg_sum += 1.0
            groups[g]["schema_valid_rate"] += 1
            groups[g]["end_to_end_task_success"] += 1
        else:
            errors.append({"id": ex.get("id"), "query": ex.get("query",""),
                           "expected_tool": exp_tool, "predicted_tool": pred_tool, "reason": "wrong_tool"})

    for g, gv in groups.items():
        c = gv["count"]
        gv["tool_selection_accuracy"]    = round(gv["tool_selection_accuracy"] / c, 4)
        gv["schema_valid_rate"]          = round(gv["schema_valid_rate"] / c, 4)
        gv["end_to_end_task_success"]    = round(gv["end_to_end_task_success"] / c, 4)

    return {
        "count": n,
        "tool_selection_accuracy": round(tool_ok / n, 4),
        "schema_valid_rate":       round(schema_ok / n, 4),
        "soft_argument_accuracy":  round(arg_sum / n, 4),
        "end_to_end_task_success": round(e2e_ok / n, 4),
        "groups": groups,
        "errors": errors,
    }


def run_condition(label, eval_path, model, tokenizer, tool_by_name, retriever):
    import torch
    examples = load_jsonl(eval_path)
    print(f"\n{'='*60}")
    print(f"Condition: {label}  ({len(examples)} samples)")
    print(f"{'='*60}")

    predictions = []
    pred_rows   = []
    for i, ex in enumerate(examples, 1):
        ranking  = retriever.search(ex["query"], top_k=TOP_K)
        selected = [tool_by_name[r["tool"]] for r in ranking if r["tool"] in tool_by_name]

        user_content = json.dumps(
            {"tools": [{"name": t["name"], "description": t["description_vi"],
                        "confirmation": t["confirmation"], "arguments": t["arguments"]}
                       for t in selected],
             "user_query": ex["query"]},
            ensure_ascii=False,
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_content}]
        text   = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = tokenizer(text, return_tensors="pt")

        t0 = time.perf_counter()
        with torch.no_grad():
            out_ids = model.generate(**inputs, max_new_tokens=256, do_sample=False,
                                     pad_token_id=tokenizer.pad_token_id)
        elapsed = (time.perf_counter() - t0) * 1000

        new_ids = out_ids[0][inputs["input_ids"].shape[1]:]
        content = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
        pred    = extract_json(content)

        if pred.get("tool") == "open_settings":
            st = pred.get("arguments", {}).get("setting_type", "")
            if st and st not in VALID_SETTINGS:
                pred["arguments"]["setting_type"] = SETTING_MAP.get(st.lower(), st)
        if pred.get("tool") in {"get_contact_info", "make_phone_call"}:
            args_d = pred.get("arguments", {})
            if isinstance(args_d.get("name"), str):
                args_d["name"] = normalize_contact(args_d["name"])
        if pred.get("tool") in tool_by_name:
            pred["requires_confirmation"] = tool_by_name[pred["tool"]]["confirmation"]

        predictions.append(pred)
        pred_rows.append({"id": ex["id"], "prediction": pred, "raw_output": content,
                          "latency_ms": round(elapsed, 1),
                          "retrieved_tools": [t["name"] for t in selected]})
        print(f"  [{i:2d}/{len(examples)}] {ex['id']}: tool={pred.get('tool')} ({elapsed:.0f}ms)")

    jsonl_path = RESULTS_DIR / f"{label}.jsonl"
    write_jsonl(jsonl_path, pred_rows)

    report = compute_report(examples, predictions, tool_by_name)
    report_path = RESULTS_DIR / f"{label}_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n  ToolAcc={report['tool_selection_accuracy']:.3f}  "
          f"SchemaValid={report['schema_valid_rate']:.3f}  "
          f"E2E={report['end_to_end_task_success']:.3f}")
    print(f"  Saved: {report_path}")
    return report


def main():
    import sys
    sys.path.insert(0, str(ROOT / "src"))

    print("Loading tools…")
    tools        = load_json(TOOLS_PATH)
    tool_by_name = {t["name"]: t for t in tools}

    print(f"Building {RETRIEVER} retriever…")
    from hybrid_retriever import HybridRetriever
    retriever = HybridRetriever(tools)

    print(f"\nLoading tokenizer from {BASE_MODEL}…")
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
    import torch

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"Loading base model {BASE_MODEL}…")
    base = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL, trust_remote_code=True,
        torch_dtype=torch.bfloat16, low_cpu_mem_usage=True,
    )

    print(f"Loading LoRA adapter {ADAPTER_PATH}…")
    model = PeftModel.from_pretrained(base, str(ADAPTER_PATH.resolve()))
    model = model.merge_and_unload()
    model.eval()
    print("Model ready.\n")

    summary = {}
    for label, eval_path in EVAL_SETS:
        if not eval_path.exists():
            print(f"SKIP: {eval_path} not found")
            continue
        report = run_condition(label, eval_path, model, tokenizer, tool_by_name, retriever)
        summary[label] = {
            "e2e":    report["end_to_end_task_success"],
            "tool":   report["tool_selection_accuracy"],
            "schema": report["schema_valid_rate"],
        }

    print(f"\n{'='*60}")
    print("P5b SUMMARY — v3_cs adapter")
    print(f"{'='*60}")
    print(f"{'Condition':<25} {'ToolAcc':>8} {'Schema':>8} {'E2E':>8}")
    print("-" * 55)
    for label, m in summary.items():
        short = label.replace("v3_", "")
        print(f"  {short:<23} {m['tool']:>8.3f} {m['schema']:>8.3f} {m['e2e']:>8.3f}")

    # So sánh với v2.1 baseline (P5b đã chạy)
    v21_baseline = {
        "noisy_light":  0.875, "noisy_medium": 0.625,
        "noisy_heavy":  0.500, "codeswitch":   0.362,
    }
    print(f"\n{'Condition':<25} {'v2.1 E2E':>9} {'v3 E2E':>8} {'Delta':>7}")
    print("-" * 55)
    for label, m in summary.items():
        short = label.replace("v3_", "")
        v21 = v21_baseline.get(short, 0)
        delta = m["e2e"] - v21
        print(f"  {short:<23} {v21:>9.3f} {m['e2e']:>8.3f} {delta:>+7.3f}")

    print(f"\nAll results saved to {RESULTS_DIR}/")


if __name__ == "__main__":
    main()
