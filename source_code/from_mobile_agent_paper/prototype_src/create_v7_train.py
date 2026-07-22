"""Build v7 training set: train329 + aug4 = ~366 samples.

Sources:
  train329 (329): vi_droidcall_train329_v6_external_robust.jsonl
  aug4    ( 37):  vi_droidcall_targeted_aug4_v7.jsonl
"""
from __future__ import annotations

from pathlib import Path
from common import ROOT, load_jsonl, write_jsonl
import re
import unicodedata

TRAIN329 = ROOT / "data" / "eval" / "vi_droidcall_train329_v6_external_robust.jsonl"
AUG4     = ROOT / "data" / "eval" / "vi_droidcall_targeted_aug4_v7.jsonl"
EXTERNAL = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"
OUT      = ROOT / "data" / "eval" / "vi_droidcall_train366_v7.jsonl"

EXPECTED_TOTAL = 329 + 37  # = 366


def _norm(text):
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def main():
    train329 = load_jsonl(TRAIN329)
    aug4     = load_jsonl(AUG4)
    external = load_jsonl(EXTERNAL)

    rows = train329 + aug4
    assert len(rows) == EXPECTED_TOTAL, f"Expected {EXPECTED_TOTAL} got {len(rows)}"

    # No duplicate IDs
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"Duplicate IDs: {[x for x in ids if ids.count(x)>1]}"

    # No overlap with external test
    ext_norms = {_norm(r["query"]) for r in external}
    for r in rows:
        nq = _norm(r["query"])
        assert nq not in ext_norms, f"External overlap: {r['id']}"

    # No "rejected" status
    for r in rows:
        s = r.get("expected", {}).get("status")
        assert s != "rejected", f"Invalid status 'rejected' in {r['id']}"

    # Count unique tools
    tools = {r["expected"]["tool"] for r in rows if r.get("expected", {}).get("tool")}
    print(f"v7 train set: {len(rows)} samples, {len(tools)} unique tools")
    print(f"  train329: {len(train329)}")
    print(f"  aug4:     {len(aug4)}")

    write_jsonl(OUT, rows)
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
