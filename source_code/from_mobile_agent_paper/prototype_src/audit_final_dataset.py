"""Audit the frozen post-hoc holdout and final Kaggle notebooks."""

import hashlib
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from validate import ToolValidator


ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "eval"
EXTERNAL_FILE = EVAL_DIR / "vi_droidcall_external_test.jsonl"
AUG3_FILE = EVAL_DIR / "vi_droidcall_targeted_aug3_external_robust.jsonl"
V6_TRAIN_FILE = EVAL_DIR / "vi_droidcall_train329_v6_external_robust.jsonl"

FILES = {
    "train": EVAL_DIR / "vi_droidcall_train191_final.jsonl",
    "holdout": EVAL_DIR / "vi_droidcall_final48.jsonl",
    "aug1": EVAL_DIR / "vi_droidcall_targeted_aug_clean.jsonl",
    "aug2": EVAL_DIR / "vi_droidcall_targeted_aug2_clean.jsonl",
}
EXPECTED_HASHES = {
    "train": "DD8D196F0FF512CF0A58356ED35D65CE91F290E4239B826C1E26DD29DC775C42",
    "holdout": "844D4A6FC824A0F08D26E871C0D5E65B978EF6912BA0C09BB57CC24E6EEB05FF",
    "aug1": "671466DC4D4796B2C2E11D7221780DB098A821E961F6847F6E387B3B92681F7A",
    "aug2": "CFE6C97599F0E5F88B36190C84FC90A088F1AD9A4FF972F2B7003C7A2D9FF37E",
}
NOTEBOOKS = [
    ROOT / "vidroidcall_v21_final_kaggle.ipynb",
    ROOT / "vidroidcall_v4_final_kaggle.ipynb",
    ROOT / "vidroidcall_v5_final_kaggle.ipynb",
]


def load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def normalize(text):
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


rows = {name: load_jsonl(path) for name, path in FILES.items()}
external_rows = load_jsonl(EXTERNAL_FILE)
aug3_rows = load_jsonl(AUG3_FILE)
v6_train_rows = load_jsonl(V6_TRAIN_FILE)
assert {name: len(data) for name, data in rows.items()} == {
    "train": 191,
    "holdout": 48,
    "aug1": 60,
    "aug2": 14,
}
assert len(external_rows) == 144
assert len(aug3_rows) == 64
assert len(v6_train_rows) == 329
for name, path in FILES.items():
    assert sha256(path) == EXPECTED_HASHES[name], f"Hash changed: {path}"

training = rows["train"] + rows["aug1"] + rows["aug2"]
assert len({row["id"] for row in training}) == len(training)
assert len({normalize(row["query"]) for row in training}) == len(training)
assert not ({row["id"] for row in training} & {row["id"] for row in rows["holdout"]})
assert not (
    {normalize(row["query"]) for row in training}
    & {normalize(row["query"]) for row in rows["holdout"]}
)

maximum_similarity = max(
    SequenceMatcher(None, normalize(train["query"]), normalize(test["query"])).ratio()
    for train in training
    for test in rows["holdout"]
)
assert maximum_similarity < 0.90, maximum_similarity
holdout_classes = {
    row["expected"]["tool"] or f"NULL:{row['expected']['status']}"
    for row in rows["holdout"]
}
source_classes = {
    row["expected"]["tool"] or f"NULL:{row['expected']['status']}"
    for row in rows["train"] + rows["holdout"]
}
assert holdout_classes == source_classes

tools = {
    tool["name"]: tool
    for tool in json.loads(
        (ROOT / "data" / "tools" / "android_tools.json").read_text(encoding="utf-8")
    )
}
for dataset in rows.values():
    for row in dataset:
        expected = row["expected"]
        tool = expected["tool"]
        assert isinstance(expected["arguments"], dict)
        if tool is None:
            assert expected["status"] in {"clarification", "unsupported"}
            assert expected["requires_confirmation"] is False
            continue
        assert tool in tools
        assert expected["requires_confirmation"] == tools[tool]["confirmation"]
        assert set(expected["arguments"]) <= set(tools[tool]["arguments"])

external_ids = {row["id"] for row in external_rows}
external_queries = {normalize(row["query"]) for row in external_rows}
training_queries = {normalize(row["query"]) for row in training}
holdout_queries = {normalize(row["query"]) for row in rows["holdout"]}
assert len(external_ids) == len(external_rows)
assert len(external_queries) == len(external_rows)
assert not (external_queries & training_queries)
assert not (external_queries & holdout_queries)

external_tools = Counter(row["expected"]["tool"] for row in external_rows)
assert len([tool for tool in external_tools if tool is not None]) == 24
assert external_tools[None] == 20

validator = ToolValidator()
for row in external_rows:
    expected = row["expected"]
    if expected["tool"] is None:
        assert expected["status"] in {"clarification", "unsupported", "rejected"}
    assert not validator.validate(expected), (row["id"], validator.validate(expected))

aug3_ids = {row["id"] for row in aug3_rows}
aug3_queries = {normalize(row["query"]) for row in aug3_rows}
assert len(aug3_ids) == len(aug3_rows)
assert len(aug3_queries) == len(aug3_rows)
assert not (aug3_queries & external_queries)
assert not (aug3_queries & training_queries)
assert not (aug3_queries & holdout_queries)
assert set(Counter(row["group"] for row in aug3_rows)) == {
    "alarm_calendar",
    "message_email",
    "negative_ambiguous",
    "settings_files",
}
for row in aug3_rows:
    expected = row["expected"]
    if expected["tool"] is None:
        assert expected["status"] in {"clarification", "unsupported", "rejected"}
    assert not validator.validate(expected), (row["id"], validator.validate(expected))

v6_train_ids = {row["id"] for row in v6_train_rows}
v6_train_queries = {normalize(row["query"]) for row in v6_train_rows}
assert len(v6_train_ids) == len(v6_train_rows)
assert len(v6_train_queries) == len(v6_train_rows)
assert not (v6_train_queries & external_queries)
for row in v6_train_rows:
    assert not validator.validate(row["expected"]), (row["id"], validator.validate(row["expected"]))

for notebook_path in NOTEBOOKS:
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    assert "vi_droidcall_train191_final.jsonl" in code
    assert "vi_droidcall_final48.jsonl" in code
    assert "set(pred_args) == set(exp_args)" in code
    assert "pred.get('status') == exp.get('status')" in code
    assert "assert_frozen_split(train_data, test_data" in code
    assert "assert subj_req is False" in code or "v21_final" in notebook_path.name
    assert "vi_droidcall_train239.jsonl" not in code
    assert "vi_droidcall_test60.jsonl" not in code

print("Final dataset audit passed.")
print(f"Training rows: {len(training)}; holdout rows: {len(rows['holdout'])}")
print(f"Maximum normalized CharSim: {maximum_similarity:.3f}")
print(f"Holdout tool/status classes: {len(holdout_classes)}")
print(f"Holdout groups: {dict(Counter(row['group'] for row in rows['holdout']))}")
print(f"External rows: {len(external_rows)}; tools: {len([tool for tool in external_tools if tool is not None])}")
print(f"Aug3 external-robust rows: {len(aug3_rows)}; groups: {dict(Counter(row['group'] for row in aug3_rows))}")
print(f"V6 external-robust train rows: {len(v6_train_rows)}")
