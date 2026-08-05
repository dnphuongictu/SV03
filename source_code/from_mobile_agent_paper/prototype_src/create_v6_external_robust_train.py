"""Create the v6 external-robust training JSONL.

The locked external test set is never included. This file combines the frozen
training split and clean targeted augmentations, including aug3.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

from common import ROOT, load_jsonl, write_jsonl
from validate import ToolValidator


EVAL_DIR = ROOT / "data" / "eval"
SOURCES = [
    EVAL_DIR / "vi_droidcall_train191_final.jsonl",
    EVAL_DIR / "vi_droidcall_targeted_aug_clean.jsonl",
    EVAL_DIR / "vi_droidcall_targeted_aug2_clean.jsonl",
    EVAL_DIR / "vi_droidcall_targeted_aug3_external_robust.jsonl",
]
EXTERNAL_PATH = EVAL_DIR / "vi_droidcall_external_test.jsonl"
OUT_PATH = EVAL_DIR / "vi_droidcall_train329_v6_external_robust.jsonl"


def _norm(text: str) -> str:
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def main() -> None:
    rows = []
    for path in SOURCES:
        rows.extend(load_jsonl(path))

    external_queries = {_norm(row["query"]) for row in load_jsonl(EXTERNAL_PATH)}
    normalized_queries = [_norm(row["query"]) for row in rows]

    assert len(rows) == 329, len(rows)
    assert len({row["id"] for row in rows}) == len(rows), "duplicate id"
    assert len(set(normalized_queries)) == len(rows), "duplicate normalized query"
    assert not (set(normalized_queries) & external_queries), "external query leakage"

    validator = ToolValidator()
    for row in rows:
        errors = validator.validate(row["expected"])
        assert not errors, (row["id"], errors)

    write_jsonl(OUT_PATH, rows)
    print(f"Wrote {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
