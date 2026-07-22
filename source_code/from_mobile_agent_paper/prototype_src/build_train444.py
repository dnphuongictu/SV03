"""Build vi_droidcall_train444_v9.jsonl = train408 + aug6 (36 samples)."""
import json, io, sys, unicodedata, re
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "eval"

train408 = [json.loads(l) for l in (DATA/"vi_droidcall_train408_v8.jsonl").read_text("utf-8").splitlines() if l.strip()]
aug6     = [json.loads(l) for l in (DATA/"vi_droidcall_targeted_aug6.jsonl").read_text("utf-8").splitlines() if l.strip()]
ext_test = [json.loads(l) for l in (DATA/"vi_droidcall_external_test.jsonl").read_text("utf-8").splitlines() if l.strip()]
final48  = [json.loads(l) for l in (DATA/"vi_droidcall_final48.jsonl").read_text("utf-8").splitlines() if l.strip()]

def norm(q: str) -> str:
    q = q.lower().strip()
    q = q.replace("đ","d").replace("Đ","D")
    q = "".join(c for c in unicodedata.normalize("NFD", q) if unicodedata.category(c) != "Mn")
    q = re.sub(r"\s+", " ", q)
    return q

ext_norms  = {norm(e["query"]) for e in ext_test}
f48_norms  = {norm(e["query"]) for e in final48}
t408_norms = {norm(e["query"]) for e in train408}

# Check aug6 overlap
overlaps = []
for s in aug6:
    nq = norm(s["query"])
    if nq in ext_norms:
        overlaps.append(f"  AUG6 vs EXT: [{s['id']}] {s['query']}")
    if nq in f48_norms:
        overlaps.append(f"  AUG6 vs F48: [{s['id']}] {s['query']}")
    if nq in t408_norms:
        overlaps.append(f"  AUG6 vs TRAIN408: [{s['id']}] {s['query']}")

if overlaps:
    print("OVERLAP DETECTED:")
    for o in overlaps: print(o)
    sys.exit(1)

# Check duplicate IDs in aug6
aug6_ids = [s["id"] for s in aug6]
if len(aug6_ids) != len(set(aug6_ids)):
    print("DUPLICATE IDs in aug6!")
    sys.exit(1)

train444 = train408 + aug6
assert len(train444) == 444, f"Expected 444, got {len(train444)}"

# Check all IDs unique
all_ids = [s["id"] for s in train444]
assert len(all_ids) == len(set(all_ids)), "Duplicate IDs in train444!"

out_path = DATA / "vi_droidcall_train444_v9.jsonl"
with out_path.open("w", encoding="utf-8") as f:
    for s in train444:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")

tools_used = {s["expected"].get("tool") for s in train444 if s["expected"].get("tool")}
neg_count  = sum(1 for s in train444 if s["expected"].get("tool") is None)
print(f"Train444 built: {len(train444)} samples, {len(tools_used)} tools, {neg_count} negatives")
print(f"Saved to: {out_path}")
print("No overlap with external test or final48 -- CLEAN")
