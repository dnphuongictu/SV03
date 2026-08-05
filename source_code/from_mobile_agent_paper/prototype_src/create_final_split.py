"""Create the post-tuning train/final-test split.

test60 was inspected while targeted augmentation was designed, so it is a
development set. This script reserves 20% of the previously untouched
train239 pool for one final evaluation and removes those rows from training.
Candidates most similar to augmentation are kept in training.
"""

import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "eval"
SEED = 20260614
HOLDOUT_EXCLUDED_IDS = {
    # Ambiguous between creating an empty Word document and generating a report.
    "vdc_unsupported_023",
}


def load_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_jsonl(path, rows):
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def normalize(text):
    text = str(text).replace("đ", "d").replace("Đ", "D")
    text = "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def similarity(left, right):
    return SequenceMatcher(None, normalize(left), normalize(right)).ratio()


source = load_jsonl(EVAL_DIR / "vi_droidcall_train239.jsonl")
augmented = load_jsonl(EVAL_DIR / "vi_droidcall_targeted_aug_clean.jsonl")
augmented += load_jsonl(EVAL_DIR / "vi_droidcall_targeted_aug2_clean.jsonl")

def label_class(row):
    expected = row["expected"]
    return expected["tool"] or f"NULL:{expected['status']}"


by_class = defaultdict(list)
for row in source:
    by_class[label_class(row)].append(row)

rng = random.Random(SEED)
train_rows = []
final_rows = []

# Start with floor(20%) and at least one row per tool/status class.
targets = {
    label: max(1, int(len(rows) * 0.20))
    for label, rows in by_class.items()
}
while sum(targets.values()) < 48:
    label = max(
        by_class,
        key=lambda item: (
            len(by_class[item]) * 0.20 - targets[item],
            len(by_class[item]),
            item,
        ),
    )
    targets[label] += 1

for label in sorted(by_class):
    rows = by_class[label]
    target = targets[label]
    scored = []
    for row in rows:
        if row["id"] in HOLDOUT_EXCLUDED_IDS:
            continue
        max_aug_similarity = max(
            similarity(row["query"], aug["query"]) for aug in augmented
        )
        max_peer_similarity = max(
            (
                similarity(row["query"], peer["query"])
                for peer in source
                if peer["id"] != row["id"]
            ),
            default=0.0,
        )
        has_near_duplicate = max_peer_similarity >= 0.90
        scored.append(
            (has_near_duplicate, max_aug_similarity, max_peer_similarity, rng.random(), row)
        )

    # Reserve unique, least augmentation-like examples for final evaluation.
    scored.sort(key=lambda item: (item[0], item[1], item[2], item[3]))
    final_ids = {item[4]["id"] for item in scored[:target]}
    final_rows.extend(row for row in rows if row["id"] in final_ids)
    train_rows.extend(row for row in rows if row["id"] not in final_ids)

assert len(train_rows) == 191, len(train_rows)
assert len(final_rows) == 48, len(final_rows)
assert not ({row["id"] for row in train_rows} & {row["id"] for row in final_rows})

max_cross_similarity = max(
    similarity(train["query"], test["query"])
    for train in train_rows + augmented
    for test in final_rows
)
exact_train_queries = {normalize(row["query"]) for row in train_rows + augmented}
assert not any(normalize(row["query"]) in exact_train_queries for row in final_rows)

save_jsonl(EVAL_DIR / "vi_droidcall_train191_final.jsonl", train_rows)
save_jsonl(EVAL_DIR / "vi_droidcall_final48.jsonl", final_rows)

print(f"train={len(train_rows)}, final={len(final_rows)}")
print(f"maximum train/augmentation-to-final similarity={max_cross_similarity:.3f}")
for group in sorted({row["group"] for row in source}):
    train_count = sum(row["group"] == group for row in train_rows)
    final_count = sum(row["group"] == group for row in final_rows)
    print(f"{group}: train={train_count}, final={final_count}")
print(f"final classes={len(Counter(label_class(row) for row in final_rows))}")
