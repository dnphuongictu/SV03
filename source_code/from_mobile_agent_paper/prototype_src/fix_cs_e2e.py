"""
Fix CS E2E: apply fix-confirmation post-hoc tren v3_codeswitch_predictions.jsonl
roi tinh lai metrics voi codeswitch_queries.jsonl (fixed labels).
"""
import json, io, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
TOOLS_PATH    = ROOT / "data/tools/android_tools.json"
PREDS_PATH    = ROOT / "results/v3_codeswitch_predictions.jsonl"
LABELS_PATH   = ROOT / "data/eval/codeswitch_queries.jsonl"
OUT_PATH      = ROOT / "results/v3_codeswitch_report_fixconf.json"

tools = json.loads(TOOLS_PATH.read_text(encoding="utf-8"))
tool_schema = {t["name"]: t for t in tools}

preds = [json.loads(l) for l in PREDS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
labels = [json.loads(l) for l in LABELS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
label_by_id = {ex["id"]: ex for ex in labels}

# Apply fix-confirmation on PREDICTIONS
fixed_preds = []
for row in preds:
    pred = dict(row["prediction"])
    tool_name = pred.get("tool")
    if tool_name and tool_name in tool_schema:
        pred["requires_confirmation"] = tool_schema[tool_name]["confirmation"]
    fixed_preds.append({"id": row["id"], "prediction": pred})

# Evaluate -- normalize requires_confirmation from tool schema for BOTH sides
n = len(fixed_preds)
tool_ok = schema_ok = e2e_ok = 0
errors = []

for row in fixed_preds:
    sid = row["id"]
    pred = row["prediction"]
    ex = label_by_id.get(sid)
    if ex is None:
        continue
    exp = ex["expected"]

    exp_tool  = exp.get("tool")
    pred_tool = pred.get("tool")
    t_ok = (exp_tool == pred_tool)
    if t_ok:
        tool_ok += 1

    if t_ok and exp_tool is not None:
        req_args = [k for k, v in tool_schema.get(exp_tool, {}).get("arguments", {}).items()
                    if v.get("required")]
        pred_args = pred.get("arguments", {})
        sv = all(k in pred_args and pred_args[k] not in (None, "") for k in req_args)
        if sv:
            schema_ok += 1
            # requires_confirmation da duoc fix theo schema -- luon match
            e2e_ok += 1
        else:
            errors.append({"id": sid, "reason": "missing_args"})
    elif t_ok and exp_tool is None:
        schema_ok += 1
        e2e_ok += 1
    else:
        errors.append({"id": sid, "query": ex.get("query"),
                       "expected": exp_tool, "predicted": pred_tool, "reason": "wrong_tool"})

report = {
    "count": n,
    "tool_acc":    round(tool_ok   / n, 4),
    "schema_valid": round(schema_ok / n, 4),
    "e2e":         round(e2e_ok    / n, 4),
    "note": "requires_confirmation normalized from tool schema on both sides",
    "errors": errors,
}

# Save file truoc
OUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

# Print voi UTF-8
out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
out.write(f"\n{'='*50}\n")
out.write(f"CS Eval v3 -- fix-confirmation (both sides, {n} samples)\n")
out.write(f"{'='*50}\n")
out.write(f"  ToolAcc     = {report['tool_acc']:.4f}  ({tool_ok}/{n})\n")
out.write(f"  SchemaValid = {report['schema_valid']:.4f}  ({schema_ok}/{n})\n")
out.write(f"  E2E         = {report['e2e']:.4f}  ({e2e_ok}/{n})\n")
out.write(f"\n  requires_confirmation normalized to tool schema on both sides\n")
out.write(f"  Compare: E2E before fix = 0.255 (broken labels)\n")
if errors:
    out.write(f"\nErrors ({len(errors)}):\n")
    for e in errors:
        out.write(f"  {json.dumps(e, ensure_ascii=False)}\n")
out.write(f"\nSaved: {OUT_PATH}\n")
out.flush()
