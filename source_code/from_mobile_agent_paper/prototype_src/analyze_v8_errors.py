"""Analyze v8 errors on extTest144 + final48 regressions → suggest aug6."""
import json, io, sys
from pathlib import Path
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT    = Path(__file__).resolve().parent.parent
DATA    = ROOT / "data" / "eval"
RESULTS = ROOT / "results"

# --- load ---
ext_gt  = {json.loads(l)["id"]: json.loads(l) for l in (DATA/"vi_droidcall_external_test.jsonl").read_text("utf-8").splitlines() if l.strip()}
f48_gt  = {json.loads(l)["id"]: json.loads(l) for l in (DATA/"vi_droidcall_final48.jsonl").read_text("utf-8").splitlines() if l.strip()}
v8_ext  = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in (RESULTS/"v8"/"external_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}
v7_ext  = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in (RESULTS/"v7"/"external_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}
v8_f48  = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in (RESULTS/"v8"/"final48_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}
v7_f48  = {json.loads(l)["id"]: json.loads(l)["prediction"] for l in (RESULTS/"v7"/"final48_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}


def args_match(pred_args: dict, gt_args: dict) -> bool:
    for k, v in gt_args.items():
        pv = pred_args.get(k)
        if pv is None: return False
        if isinstance(v, str) and isinstance(pv, str):
            if v.lower() != pv.lower(): return False
        elif v != pv: return False
    return True

def e2e_ok(pred: dict, gt: dict) -> bool:
    if pred.get("tool") != gt["expected"].get("tool"): return False
    if not args_match(pred.get("arguments") or {}, gt["expected"].get("arguments") or {}): return False
    if gt["expected"].get("status") and pred.get("status") != gt["expected"].get("status"): return False
    return True


# ── EXTERNAL144 analysis ──────────────────────────────────────────────────────
print("=" * 80)
print("v8 failures on extTest144 (NEW failures not in v7, and persistent failures)")
print("=" * 80)

v8_fail = [eid for eid, gt in ext_gt.items() if not e2e_ok(v8_ext[eid], gt)]
v7_fail = {eid for eid, gt in ext_gt.items() if not e2e_ok(v7_ext[eid], gt)}

fixed    = [eid for eid in v7_fail if eid not in v8_fail]
new_fail = [eid for eid in v8_fail if eid not in v7_fail]
persist  = [eid for eid in v8_fail if eid in v7_fail]

print(f"\nv7 failures: {len(v7_fail)}, v8 failures: {len(v8_fail)}")
print(f"Fixed by v8: {len(fixed)}, New in v8: {len(new_fail)}, Persistent: {len(persist)}")

print(f"\n--- FIXED by aug5 ({len(fixed)}) ---")
for eid in sorted(fixed):
    gt = ext_gt[eid]; q = gt["query"]
    print(f"  [{eid}] {gt['expected'].get('tool')}  q={q}")

print(f"\n--- NEW failures in v8 ({len(new_fail)}) ---")
for eid in sorted(new_fail):
    gt = ext_gt[eid]
    p  = v8_ext[eid]
    print(f"  [{eid}]")
    print(f"    q  : {gt['query']}")
    print(f"    gt : {gt['expected'].get('tool')}  args={json.dumps(gt['expected'].get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8 : {p.get('tool')}  args={json.dumps(p.get('arguments',{}), ensure_ascii=False)}")

print(f"\n--- PERSISTENT failures ({len(persist)}) [still wrong in v8] ---")
tool_err: Counter = Counter()
arg_err:  Counter = Counter()
for eid in sorted(persist):
    gt   = ext_gt[eid]
    pred = v8_ext[eid]
    gt_tool = gt["expected"].get("tool")
    pd_tool = pred.get("tool")
    gt_args = gt["expected"].get("arguments", {}) or {}
    pd_args = pred.get("arguments", {}) or {}
    if gt_tool != pd_tool:
        tool_err[f"{gt_tool} -> {pd_tool}"] += 1
    else:
        for k, v in gt_args.items():
            pv = pd_args.get(k)
            if pv is None: arg_err[f"MISS:{k} in {gt_tool}"] += 1
            elif (pv.lower() if isinstance(pv,str) else pv) != (v.lower() if isinstance(v,str) else v):
                arg_err[f"WRONG:{k} in {gt_tool}"] += 1

print("\nPersistent tool errors:")
for k, c in tool_err.most_common(): print(f"  {c}x {k}")
print("Persistent arg errors:")
for k, c in arg_err.most_common(): print(f"  {c}x {k}")


# ── FINAL48 regressions ───────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("v8 regressions on final48 (v7 correct → v8 wrong)")
print("=" * 80)
reg = [(eid, f48_gt[eid], v7_f48[eid], v8_f48[eid])
       for eid in f48_gt
       if e2e_ok(v7_f48[eid], f48_gt[eid]) and not e2e_ok(v8_f48[eid], f48_gt[eid])]
for eid, gt, v7p, v8p in reg:
    print(f"\n  [{eid}]  q={gt['query']}")
    print(f"    gt: {gt['expected'].get('tool')}  args={json.dumps(gt['expected'].get('arguments',{}), ensure_ascii=False)}")
    print(f"    v7: {v7p.get('tool')}  args={json.dumps(v7p.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8: {v8p.get('tool')}  args={json.dumps(v8p.get('arguments',{}), ensure_ascii=False)}")

# ── AUG6 priority ─────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("AUG6 PRIORITY PATTERNS")
print("=" * 80)
print("""
1. send_message WITH explicit subject (vdc_sms_007): aug5 over-suppressed subject field
   Fix: add 3+ examples where user says 'tiêu đề X nội dung Y' → keep subject
2. 'Google X' / 'Bing X' explicit engine → web_search (vdc_web_003, ext_web_003/005)
   Fix: add web_search examples with explicit engine keyword in query
3. ACTION_GET_CONTENT email pick (vdc_pick_007): confused with send_email context
4. SHOW_ALARMS disambiguation: 'kiểm tra alarm' → ACTION_SHOW_ALARMS (not ringtone)
5. search_location vs get_contact_info: 'tìm địa chỉ nhà X' → get_contact_info key=address
6. Persistent arg errors: EXTRA_DAYS weekday, phone number spacing, contact_uri prefix
""")
