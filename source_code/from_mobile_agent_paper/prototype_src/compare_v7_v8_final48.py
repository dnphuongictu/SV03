"""Compare v7 vs v8 on final48 — McNemar + regression analysis."""
import json, io, sys, math
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA = Path(__file__).resolve().parent.parent / "data" / "eval"
RES  = Path(__file__).resolve().parent.parent / "results"

f48_gt  = {json.loads(l)["id"]: json.loads(l)
           for l in (DATA / "vi_droidcall_final48.jsonl").read_text("utf-8").splitlines() if l.strip()}
v7_pred = {json.loads(l)["id"]: json.loads(l)["prediction"]
           for l in (RES / "v7" / "final48_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}
v8_pred = {json.loads(l)["id"]: json.loads(l)["prediction"]
           for l in (RES / "v8" / "final48_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}


def e2e_ok(pred: dict, gt: dict) -> bool:
    if pred.get("tool") != gt["expected"].get("tool"):
        return False
    gt_args   = gt["expected"].get("arguments", {}) or {}
    pred_args = pred.get("arguments", {}) or {}
    for k, v in gt_args.items():
        pv = pred_args.get(k)
        if pv is None:
            return False
        if isinstance(v, str) and isinstance(pv, str):
            if v.lower() != pv.lower():
                return False
        elif v != pv:
            return False
    if gt["expected"].get("status") and pred.get("status") != gt["expected"].get("status"):
        return False
    return True


n11 = n10 = n01 = n00 = 0
lost   = []
gained = []

for eid, gt in f48_gt.items():
    v7ok = e2e_ok(v7_pred[eid], gt)
    v8ok = e2e_ok(v8_pred[eid], gt)
    if   v7ok and     v8ok: n11 += 1
    elif v7ok and not v8ok: n10 += 1; lost.append((eid, gt, v7_pred[eid], v8_pred[eid]))
    elif not v7ok and v8ok: n01 += 1; gained.append((eid, gt, v7_pred[eid], v8_pred[eid]))
    else:                   n00 += 1

print(f"v7+v8 both correct : {n11}")
print(f"v7 correct, v8 FAIL: {n10}  <- regression")
print(f"v7 FAIL, v8 correct: {n01}  <- improvement")
print(f"both FAIL          : {n00}")
print()

n_disc = n10 + n01
if n_disc > 0:
    z = (n10 - n01) / math.sqrt(n_disc)
    p_approx = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    print(f"McNemar: z={z:.2f}, p≈{p_approx:.3f}  ({'significant' if abs(z)>1.96 else 'NOT significant'})")
else:
    print("McNemar: no discordant pairs")

print()
print("REGRESSED (v7 correct → v8 wrong):")
for eid, gt, v7p, v8p in lost:
    gt_tool = gt["expected"].get("tool")
    print(f"  [{eid}]")
    print(f"    query : {gt['query']}")
    print(f"    gt    : {gt_tool}  args={json.dumps(gt['expected'].get('arguments',{}), ensure_ascii=False)}")
    print(f"    v7    : {v7p.get('tool')}  args={json.dumps(v7p.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8    : {v8p.get('tool')}  args={json.dumps(v8p.get('arguments',{}), ensure_ascii=False)}")

print()
print("GAINED (v7 wrong → v8 correct):")
for eid, gt, v7p, v8p in gained:
    gt_tool = gt["expected"].get("tool")
    print(f"  [{eid}]")
    print(f"    query : {gt['query']}")
    print(f"    gt    : {gt_tool}  args={json.dumps(gt['expected'].get('arguments',{}), ensure_ascii=False)}")
    print(f"    v7    : {v7p.get('tool')}  args={json.dumps(v7p.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8    : {v8p.get('tool')}  args={json.dumps(v8p.get('arguments',{}), ensure_ascii=False)}")
