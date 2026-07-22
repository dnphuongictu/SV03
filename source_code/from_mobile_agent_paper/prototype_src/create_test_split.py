"""
Tao held-out test set tu 299 training samples.
Chien luoc: stratified 80/20 theo group, loai exact duplicates khoi test.

Output:
  data/eval/vi_droidcall_train239.jsonl   (239 mau train moi)
  data/eval/vi_droidcall_test60.jsonl     (60 mau test held-out)
"""
import json, random, io, sys
from pathlib import Path
from collections import defaultdict
from difflib import SequenceMatcher
import unicodedata, re

ROOT = Path(__file__).parent.parent
SEED = 42

out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
def p(s=""): out.write(str(s) + "\n"); out.flush()

def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]

def save_jsonl(path, rows):
    Path(path).write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows),
        encoding="utf-8"
    )

def normalize(text):
    text = text.replace("đ", "d").replace("Đ", "D")
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()

def char_sim(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()

# Load
train_all = load_jsonl(ROOT / "data/eval/vi_droidcall_v1.jsonl")
smoke32   = load_jsonl(ROOT / "data/eval/vi_smoke_test.jsonl")
smoke_queries = {normalize(ex["query"]) for ex in smoke32}

random.seed(SEED)

# Group by group
by_group = defaultdict(list)
for ex in train_all:
    by_group[ex["group"]].append(ex)

# Target: 20% test per group (min 4 per group)
test_rows, train_rows = [], []

p("=== Split plan ===")
for group, examples in sorted(by_group.items()):
    random.shuffle(examples)
    n_test = max(4, round(len(examples) * 0.20))
    # Pick test samples that are NOT near-duplicates of smoke32
    # (to ensure test set is cleanly separated from smoke32 too)
    candidates_test, candidates_train = [], []
    for ex in examples:
        nq = normalize(ex["query"])
        in_smoke = any(char_sim(ex["query"], sq) >= 0.9
                       for sq in [s["query"] for s in smoke32])
        if in_smoke:
            candidates_train.append(ex)
        else:
            candidates_test.append(ex)

    # Take n_test from non-smoke candidates for test
    selected_test = candidates_test[:n_test]
    remaining = candidates_test[n_test:] + candidates_train

    test_rows.extend(selected_test)
    train_rows.extend(remaining)
    p(f"  {group}: {len(examples)} total -> {len(selected_test)} test, {len(remaining)} train")

p(f"\nTotal: {len(test_rows)} test, {len(train_rows)} train (sum={len(test_rows)+len(train_rows)})")

# Verify no exact overlap between test and train
test_ids = {ex["id"] for ex in test_rows}
train_ids = {ex["id"] for ex in train_rows}
assert not test_ids & train_ids, "Overlap detected!"

# Check similarity between test and remaining train
high_sim_pairs = []
for t in test_rows:
    for tr in train_rows:
        s = char_sim(t["query"], tr["query"])
        if s >= 0.9:
            high_sim_pairs.append((t["id"], tr["id"], round(s, 3)))

if high_sim_pairs:
    p(f"\nWarning: {len(high_sim_pairs)} test-train pairs with CharSim >= 0.9:")
    for tid, trid, s in high_sim_pairs[:10]:
        p(f"  test={tid} train={trid} sim={s}")
else:
    p("\nNo high-similarity (>=0.9) test-train pairs found.")

# Check test vs smoke32
test_smoke_overlap = []
for t in test_rows:
    for s in smoke32:
        sim = char_sim(t["query"], s["query"])
        if sim >= 0.8:
            test_smoke_overlap.append((t["id"], s["id"], round(sim, 3)))
if test_smoke_overlap:
    p(f"\nTest-Smoke overlap (CharSim>=0.8): {len(test_smoke_overlap)} pairs")
else:
    p("No test-smoke32 overlap.")

# Save
out_train = ROOT / "data/eval/vi_droidcall_train239.jsonl"
out_test  = ROOT / "data/eval/vi_droidcall_test60.jsonl"
save_jsonl(out_train, train_rows)
save_jsonl(out_test, test_rows)

p(f"\nSaved:")
p(f"  {out_train} ({len(train_rows)} rows)")
p(f"  {out_test}  ({len(test_rows)} rows)")

# Group distribution check
from collections import Counter
p("\nTest set group distribution:")
for g, n in sorted(Counter(ex["group"] for ex in test_rows).items()):
    p(f"  {g}: {n}")
