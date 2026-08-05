"""
A1: Analyze v7 errors on extTest144 — categorize failures and suggest aug5 samples.

Usage:
    python src/analyze_v7_errors.py

Output: prints categorized failure list and aug5 suggestions.
"""
from __future__ import annotations

import io, json, sys
from pathlib import Path
from collections import Counter

# Fix stdout/stderr encoding for Windows terminal
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "eval"
RESULTS = ROOT / "results"

PRED_FILE = RESULTS / "v7" / "external_hybrid_k5_predictions.jsonl"
GT_FILE   = DATA / "vi_droidcall_external_test.jsonl"


def normalize_args(args: dict) -> dict:
    """Lowercase string values for lenient comparison."""
    return {k: v.lower() if isinstance(v, str) else v for k, v in args.items()}


def args_match(pred_args: dict, gt_args: dict) -> bool:
    """Strict exact match on required args (ignoring extra optional args in pred)."""
    for k, v in gt_args.items():
        if k not in pred_args:
            return False
        pv = pred_args[k]
        # allow case-insensitive string match
        if isinstance(v, str) and isinstance(pv, str):
            if v.lower() != pv.lower():
                return False
        elif v != pv:
            return False
    return True


def main() -> None:
    preds = [json.loads(l) for l in PRED_FILE.read_text("utf-8").splitlines() if l.strip()]
    gts   = [json.loads(l) for l in GT_FILE.read_text("utf-8").splitlines() if l.strip()]

    assert len(preds) == len(gts), f"Length mismatch: {len(preds)} vs {len(gts)}"

    # Build id -> gt map
    gt_map = {ex["id"]: ex for ex in gts}

    print(f"Analyzing {len(preds)} v7 predictions on extTest144\n")

    # Error categories
    E_TOOL_NEG    = "tool_error_negative"    # should be null but predicted a tool
    E_TOOL_POS    = "tool_error_positive"    # wrong tool predicted (true tool != null)
    E_ARGS_EXTRA  = "args_extra_optional"    # correct tool, extra optional args hallucinated
    E_ARGS_WRONG  = "args_wrong"             # correct tool, required arg wrong value
    E_ARGS_MISS   = "args_missing"           # correct tool, required arg missing
    E_CONFIRM     = "confirmation_wrong"     # correct tool+args, wrong requires_confirmation
    E_STATUS      = "status_wrong"           # null tool but wrong status field

    failures: list[dict] = []
    tool_errors: Counter = Counter()
    arg_errors:  Counter = Counter()
    correct = 0

    for pred_ex in preds:
        eid  = pred_ex["id"]
        gt   = gt_map[eid]
        pred = pred_ex["prediction"]

        gt_tool   = gt["expected"].get("tool")
        gt_args   = gt["expected"].get("arguments", {})
        gt_conf   = gt["expected"].get("requires_confirmation")
        gt_status = gt["expected"].get("status")

        pred_tool   = pred.get("tool")
        pred_args   = pred.get("arguments", {}) or {}
        pred_conf   = pred.get("requires_confirmation")
        pred_status = pred.get("status")

        # Check correctness
        tool_ok    = (gt_tool == pred_tool)
        if gt_tool is None:
            args_ok    = True
            status_ok  = (gt_status == pred_status)
            conf_ok    = True  # no confirmation check for null-tool
        else:
            args_ok    = args_match(pred_args, gt_args)
            status_ok  = True
            conf_ok    = (gt_conf == pred_conf) if gt_conf is not None else True

        e2e_ok = tool_ok and args_ok and status_ok and conf_ok
        if e2e_ok:
            correct += 1
            continue

        # Categorize error
        error_type = []
        if not tool_ok:
            if gt_tool is None:
                error_type.append(E_TOOL_NEG)
                tool_errors["SHOULD_NULL -> " + str(pred_tool)] += 1
            else:
                error_type.append(E_TOOL_POS)
                tool_errors[str(gt_tool) + " -> " + str(pred_tool)] += 1
        else:
            # tool correct
            if not args_ok:
                # figure out sub-type
                missing_req = [k for k in gt_args if k not in pred_args]
                wrong_val   = [k for k in gt_args if k in pred_args and
                               (pred_args[k].lower() if isinstance(pred_args[k], str) else pred_args[k]) !=
                               (gt_args[k].lower() if isinstance(gt_args[k], str) else gt_args[k])]
                extra_only  = not missing_req and not wrong_val  # extra optional keys only
                if extra_only:
                    error_type.append(E_ARGS_EXTRA)
                    # find extra keys
                    extras = [k for k in pred_args if k not in gt_args]
                    for e in extras:
                        arg_errors["EXTRA:" + e + " in " + str(pred_tool)] += 1
                elif missing_req:
                    error_type.append(E_ARGS_MISS)
                    for m in missing_req:
                        arg_errors["MISS:" + m + " in " + str(pred_tool)] += 1
                else:
                    error_type.append(E_ARGS_WRONG)
                    for w in wrong_val:
                        arg_errors["WRONG:" + w + " in " + str(pred_tool)] += 1
            if not conf_ok:
                error_type.append(E_CONFIRM)
            if not status_ok:
                error_type.append(E_STATUS)

        failures.append({
            "id": eid,
            "query": gt["query"],
            "gt_tool": gt_tool,
            "pred_tool": pred_tool,
            "gt_args": gt_args,
            "pred_args": pred_args,
            "gt_conf": gt_conf,
            "pred_conf": pred_conf,
            "error_type": error_type,
        })

    e2e = correct / len(preds)
    print(f"E2E = {correct}/{len(preds)} = {e2e:.4f}  (paper reports 0.674, check matches)\n")

    # Summarize by error type
    type_counts: Counter = Counter()
    for f in failures:
        for t in f["error_type"]:
            type_counts[t] += 1
    print("Error type breakdown:")
    for et, cnt in type_counts.most_common():
        print(f"  {et:35s}: {cnt}")
    print()

    # Tool errors
    print("Tool-level errors (top 15):")
    for k, cnt in tool_errors.most_common(15):
        print(f"  {cnt:3d}x  {k}")
    print()

    # Arg errors
    print("Arg-level errors (top 15):")
    for k, cnt in arg_errors.most_common(15):
        print(f"  {cnt:3d}x  {k}")
    print()

    # Full failure list
    print("=" * 90)
    print("ALL FAILURES:")
    print("=" * 90)
    for f in failures:
        print(f"\n[{f['id']}]  err={f['error_type']}")
        print(f"  query    : {f['query']}")
        print(f"  gt_tool  : {f['gt_tool']}   pred_tool: {f['pred_tool']}")
        if f["gt_args"] or f["pred_args"]:
            print(f"  gt_args  : {json.dumps(f['gt_args'], ensure_ascii=False)}")
            print(f"  pred_args: {json.dumps(f['pred_args'], ensure_ascii=False)}")
        if f.get("gt_conf") is not None:
            print(f"  confirm  : gt={f['gt_conf']} pred={f['pred_conf']}")

    # Aug5 suggestions
    print("\n" + "=" * 90)
    print("AUG5 SUGGESTIONS (patterns for new training samples):")
    print("=" * 90)

    # Group tool errors by pattern
    neg_failures = [f for f in failures if E_TOOL_NEG in f["error_type"]]
    pos_failures = [f for f in failures if E_TOOL_POS in f["error_type"]]
    extra_failures = [f for f in failures if E_ARGS_EXTRA in f["error_type"] and E_TOOL_POS not in f["error_type"]]
    wrong_failures = [f for f in failures if E_ARGS_WRONG in f["error_type"] and E_TOOL_POS not in f["error_type"]]

    print(f"\nNegative rejection failures: {len(neg_failures)}")
    for f in neg_failures:
        print(f"  [{f['id']}] pred={f['pred_tool']}  q={f['query']}")

    print(f"\nTool selection errors: {len(pos_failures)}")
    for f in pos_failures:
        print(f"  [{f['id']}] {f['gt_tool']} -> {f['pred_tool']}  q={f['query']}")

    print(f"\nOptional arg hallucination: {len(extra_failures)}")
    for f in extra_failures:
        extra = [k for k in f["pred_args"] if k not in f["gt_args"]]
        print(f"  [{f['id']}] tool={f['gt_tool']}  extra={extra}  q={f['query']}")

    print(f"\nWrong arg value: {len(wrong_failures)}")
    for f in wrong_failures:
        print(f"  [{f['id']}] tool={f['gt_tool']}  q={f['query']}")
        for k in f["gt_args"]:
            if k in f["pred_args"]:
                pv = f["pred_args"][k]
                gv = f["gt_args"][k]
                if (pv.lower() if isinstance(pv,str) else pv) != (gv.lower() if isinstance(gv,str) else gv):
                    print(f"      {k}: gt={gv!r} pred={pv!r}")


if __name__ == "__main__":
    main()
