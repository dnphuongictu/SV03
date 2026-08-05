"""
Leakage analysis: so sanh smoke32 vs train299.
Tinh similarity dua tren normalized character n-gram (unigram overlap).
"""
import json, unicodedata, re, io, sys
from pathlib import Path

out_stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).parent.parent

def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

def p(s=""):
    out_stream.write(str(s) + "\n"); out_stream.flush()

def normalize(text):
    # NFD + remove diacritics + lowercase + strip punctuation
    text = text.replace("đ", "d").replace("Đ", "D")
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()

def char_sim(a, b):
    """SequenceMatcher ratio on normalized text."""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

def token_jaccard(a, b):
    sa = set(normalize(a).split())
    sb = set(normalize(b).split())
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)

smoke = load_jsonl(ROOT / "data/eval/vi_smoke_test.jsonl")
train = load_jsonl(ROOT / "data/eval/vi_droidcall_v1.jsonl")

train_queries = [(ex["id"], ex["query"]) for ex in train]

p(f"Smoke set : {len(smoke)} samples")
p(f"Train set : {len(train)} samples")

thresholds_j = [1.0, 0.9, 0.8, 0.7]
thresholds_c = [1.0, 0.9, 0.8, 0.7]
counts_j = {t: 0 for t in thresholds_j}
counts_c = {t: 0 for t in thresholds_c}
details = []

for s in smoke:
    sq = s["query"]
    best_j = best_c = 0.0
    best_j_match = best_c_match = None
    for tid, tq in train_queries:
        j = token_jaccard(sq, tq)
        c = char_sim(sq, tq)
        if j > best_j: best_j = j; best_j_match = (tid, tq)
        if c > best_c: best_c = c; best_c_match = (tid, tq)
    details.append({
        "smoke_id": s["id"],
        "smoke_query": sq,
        "best_jaccard": round(best_j, 4),
        "best_jaccard_train_id": best_j_match[0],
        "best_jaccard_train_query": best_j_match[1],
        "best_charsim": round(best_c, 4),
        "best_charsim_train_id": best_c_match[0],
        "best_charsim_train_query": best_c_match[1],
    })
    for t in thresholds_j:
        if best_j >= t: counts_j[t] += 1
    for t in thresholds_c:
        if best_c >= t: counts_c[t] += 1

# Save first
out = ROOT / "results/leakage_analysis.json"
out.write_text(json.dumps({
    "smoke_count": len(smoke), "train_count": len(train),
    "jaccard_counts": {str(k): v for k, v in counts_j.items()},
    "charsim_counts": {str(k): v for k, v in counts_c.items()},
    "details": details,
}, ensure_ascii=False, indent=2), encoding="utf-8")

# Print summary
p("\n=== Leakage Summary ===")
p("Token Jaccard:")
for t in thresholds_j:
    label = "EXACT" if t == 1.0 else f">={t}"
    p(f"  {label:6s}: {counts_j[t]:3d}/{len(smoke)} ({100*counts_j[t]/len(smoke):.1f}%)")
p("Char SequenceMatcher ratio:")
for t in thresholds_c:
    label = "EXACT" if t == 1.0 else f">={t}"
    p(f"  {label:6s}: {counts_c[t]:3d}/{len(smoke)} ({100*counts_c[t]/len(smoke):.1f}%)")

p("\n=== High-similarity pairs (CharSim >= 0.8) ===")
high = [d for d in details if d["best_charsim"] >= 0.8]
for d in sorted(high, key=lambda x: -x["best_charsim"]):
    p(f"  [J={d['best_jaccard']:.2f} C={d['best_charsim']:.2f}] smoke: {d['smoke_query']!r}")
    p(f"    train ({d['best_charsim_train_id']}): {d['best_charsim_train_query']!r}")

p(f"\nSaved: {out}")
