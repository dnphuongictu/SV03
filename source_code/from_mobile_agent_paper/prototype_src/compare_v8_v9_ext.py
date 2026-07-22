"""So sánh v8 vs v9 trên external144 — xem aug6 tạo regression nào."""
import json, io, sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT    = Path(__file__).resolve().parent.parent
DATA    = ROOT / "data" / "eval"
RESULTS = ROOT / "results"

gt = {json.loads(l)["id"]: json.loads(l)
      for l in (DATA/"vi_droidcall_external_test.jsonl").read_text("utf-8").splitlines() if l.strip()}
v8 = {json.loads(l)["id"]: json.loads(l)["prediction"]
      for l in (RESULTS/"v8"/"external_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}
v9 = {json.loads(l)["id"]: json.loads(l)["prediction"]
      for l in (RESULTS/"v9"/"external_hybrid_k5_predictions.jsonl").read_text("utf-8").splitlines() if l.strip()}

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC))
from evaluate import evaluate as _evaluate_set

# Inline e2e_ok matching evaluate.py logic
from evaluate import values_match

def _e2e_ok(pred: dict, exp: dict) -> bool:
    if pred.get("tool") != exp.get("tool"): return False
    gt_args = exp.get("arguments") or {}
    pd_args = pred.get("arguments") or {}
    for k, v in gt_args.items():
        if not values_match(k, v, pd_args.get(k)): return False
    if exp.get("status") and pred.get("status") != exp.get("status"): return False
    return True

lost   = []  # v8 correct → v9 wrong
gained = []  # v8 wrong → v9 correct

for eid, gt_rec in gt.items():
    v8ok = _e2e_ok(v8[eid], gt_rec["expected"])
    v9ok = _e2e_ok(v9[eid], gt_rec["expected"])
    if v8ok and not v9ok:
        lost.append((eid, gt_rec, v8[eid], v9[eid]))
    elif not v8ok and v9ok:
        gained.append((eid, gt_rec, v8[eid], v9[eid]))

print(f"v8 correct → v9 FAIL (regression): {len(lost)}")
print(f"v8 FAIL → v9 correct (improvement): {len(gained)}")
print()

print("=== REGRESSION (v8 correct → v9 wrong) ===")
for eid, gt_rec, v8p, v9p in lost:
    exp = gt_rec["expected"]
    print(f"\n  [{eid}]  q={gt_rec['query']}")
    print(f"    gt : {exp.get('tool')}  args={json.dumps(exp.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8 : {v8p.get('tool')}  args={json.dumps(v8p.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v9 : {v9p.get('tool')}  args={json.dumps(v9p.get('arguments',{}), ensure_ascii=False)}")

print()
print("=== IMPROVEMENT (v8 wrong → v9 correct) ===")
for eid, gt_rec, v8p, v9p in gained:
    exp = gt_rec["expected"]
    print(f"\n  [{eid}]  q={gt_rec['query']}")
    print(f"    gt : {exp.get('tool')}  args={json.dumps(exp.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v8 : {v8p.get('tool')}  args={json.dumps(v8p.get('arguments',{}), ensure_ascii=False)}")
    print(f"    v9 : {v9p.get('tool')}  args={json.dumps(v9p.get('arguments',{}), ensure_ascii=False)}")
