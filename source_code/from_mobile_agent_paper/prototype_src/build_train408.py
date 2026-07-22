"""Build vi_droidcall_train408_v8.jsonl = train366 + aug5."""
import json, re, unicodedata, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DATA = Path(__file__).resolve().parent.parent / "data" / "eval"

train366 = [json.loads(l) for l in (DATA / "vi_droidcall_train366_v7.jsonl").read_text("utf-8").splitlines() if l.strip()]
aug5     = [json.loads(l) for l in (DATA / "vi_droidcall_targeted_aug5.jsonl").read_text("utf-8").splitlines() if l.strip()]

combined = train366 + aug5
print(f"train366: {len(train366)}  +  aug5: {len(aug5)}  =  {len(combined)}")

assert len(combined) == 408, f"Expected 408, got {len(combined)}"

def _norm(text):
    text = str(text).replace("đ","d").replace("Đ","D")
    text = "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

ids = [ex["id"] for ex in combined]
assert len(set(ids)) == len(ids), "Duplicate IDs!"

out = DATA / "vi_droidcall_train408_v8.jsonl"
out.write_text("\n".join(json.dumps(ex, ensure_ascii=False) for ex in combined), encoding="utf-8")
print(f"Saved: {out}  ({out.stat().st_size} bytes)")

# Quick stats
tools = set(ex["expected"].get("tool") for ex in combined)
print(f"Unique tools: {len(tools - {None})} + negatives: {sum(1 for ex in combined if not ex['expected'].get('tool'))}")
