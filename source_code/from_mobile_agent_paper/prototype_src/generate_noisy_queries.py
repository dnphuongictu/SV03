"""Generate ASR-noisy versions of training queries for robustness testing.

Creates 3 noise levels (light/medium/heavy) for each query in vi_droidcall_v1.jsonl
to simulate real-world ASR errors.

Output: prototype/data/eval/noisy_queries.jsonl
        Each row has: id, clean_query, noisy_query, noise_level, noise_types_applied

Usage:
    python -X utf8 src/generate_noisy_queries.py
"""
from __future__ import annotations

import json
import random
import re
import unicodedata
from pathlib import Path
from typing import Any

random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
TRAIN_PATH = ROOT / "data" / "eval" / "vi_droidcall_v1.jsonl"
OUT_PATH = ROOT / "data" / "eval" / "noisy_queries.jsonl"

# ── Phonetic confusion pairs (Vietnamese homophone-like) ─────────────────────
PHONETIC_MAP: dict[str, list[str]] = {
    "gọi": ["gói", "gỏi", "gồi"],
    "đặt": ["đật", "đất", "đắt"],
    "báo": ["bào", "bảo", "bão"],
    "thức": ["thức", "thứ", "thừ"],
    "sáng": ["sáng", "sắng", "xáng"],
    "anh": ["anh", "an", "án"],
    "điện": ["điện", "biến", "diện"],
    "lúc": ["lúc", "lục", "lức"],
    "giờ": ["giờ", "dờ", "dơ"],
    "nhãn": ["nhãn", "nhạn", "nhan"],
    "tìm": ["tìm", "tím", "tim"],
    "số": ["số", "sỗ", "xố"],
    "mở": ["mở", "mỡ", "mơ"],
    "cài": ["cài", "cái", "cãi"],
    "gửi": ["gửi", "gỡi", "gưởi"],
    "chụp": ["chụp", "chúp", "chóp"],
    "quay": ["quay", "quảy", "quậy"],
    "tạo": ["tạo", "táo", "tảo"],
    "chọn": ["chọn", "chộn", "chón"],
    "thêm": ["thêm", "thềm", "thèm"],
}

# Vietnamese vowels & tone marks for substitution
VI_TONE_MARKS = {
    'a': 'áàảãạăắằẳẵặâấầẩẫậ',
    'e': 'éèẻẽẹêếềểễệ',
    'i': 'íìỉĩị',
    'o': 'óòỏõọôốồổỗộơớờởỡợ',
    'u': 'úùủũụưứừửữự',
    'y': 'ýỳỷỹỵ',
}

# Filler words for ASR hallucination
FILLERS = ["à", "ờ", "thì", "à mà", "ờ thì", "à ờ", "thì là", "à thì", "à ơi", "ủa"]


# ── helpers ──────────────────────────────────────────────────────────────────

def strip_vi_diacritics(text: str) -> str:
    """Remove Vietnamese diacritics from text."""
    # Normalize NFD (decompose)
    nfkd = unicodedata.normalize('NFKD', text)
    # Keep only ASCII
    result = ''.join(c for c in nfkd if not unicodedata.combining(c))
    return result


def apply_phonetic_noise(text: str, rate: float) -> str:
    """Replace words with phonetically similar ones at given rate."""
    words = text.split()
    result = []
    for w in words:
        w_lower = w.lower()
        if w_lower in PHONETIC_MAP and random.random() < rate:
            replacement = random.choice(PHONETIC_MAP[w_lower])
            # Preserve case
            if w[0].isupper():
                replacement = replacement.title()
            result.append(replacement)
        else:
            result.append(w)
    return ' '.join(result)


def apply_typo_noise(text: str, rate: float) -> str:
    """Introduce random typos: character swap, delete, substitute."""
    chars = list(text)
    n = len(chars)
    for i in range(n):
        if random.random() < rate:
            op = random.choice(['swap', 'delete', 'substitute'])
            if op == 'swap' and i + 1 < n:
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
            elif op == 'delete':
                chars[i] = ''
            elif op == 'substitute':
                # Replace with a nearby keyboard key (simplified)
                nearby = {
                    'a': 'as', 'b': 'bn', 'c': 'cv', 'd': 'df', 'e': 'er',
                    'g': 'gh', 'h': 'hj', 'i': 'io', 'k': 'kl', 'l': 'lk',
                    'm': 'mn', 'n': 'nm', 'o': 'op', 'p': 'po', 'q': 'qw',
                    'r': 'rt', 's': 'sd', 't': 'ty', 'u': 'ui', 'v': 'vb',
                    'x': 'xz', 'y': 'yu',
                }
                if chars[i].lower() in nearby:
                    chars[i] = random.choice(nearby[chars[i].lower()])
    return ''.join(c for c in chars if c)


def apply_tone_removal(text: str, rate: float) -> str:
    """Remove tone marks from some words."""
    words = text.split()
    result = []
    for w in words:
        if random.random() < rate:
            result.append(strip_vi_diacritics(w))
        else:
            result.append(w)
    return ' '.join(result)


def apply_word_merger(text: str, rate: float) -> str:
    """Merge adjacent words by removing spaces."""
    words = text.split()
    if len(words) < 2:
        return text
    result = list(words)
    # Pick random pairs to merge
    n_merges = max(1, int(len(words) * rate))
    for _ in range(n_merges):
        idx = random.randint(0, len(result) - 2)
        result[idx] = result[idx] + result[idx + 1]
        result.pop(idx + 1)
        if len(result) < 2:
            break
    return ' '.join(result)


def apply_asr_hallucination(text: str, rate: float) -> str:
    """Insert filler words at random positions."""
    words = text.split()
    n_fillers = max(1, int(len(words) * rate * 0.5))
    for _ in range(n_fillers):
        idx = random.randint(0, len(words))
        filler = random.choice(FILLERS)
        words.insert(idx, filler)
    return ' '.join(words)


# ── noise levels ─────────────────────────────────────────────────────────────

NOISE_CONFIGS: dict[str, dict[str, float]] = {
    "light": {
        "phonetic": 0.08,
        "typo": 0.02,
        "tone_removal": 0.15,
        "word_merger": 0.0,
        "asr_hallucination": 0.0,
    },
    "medium": {
        "phonetic": 0.15,
        "typo": 0.05,
        "tone_removal": 0.30,
        "word_merger": 0.05,
        "asr_hallucination": 0.05,
    },
    "heavy": {
        "phonetic": 0.25,
        "typo": 0.10,
        "tone_removal": 0.50,
        "word_merger": 0.10,
        "asr_hallucination": 0.10,
    },
}


def apply_noise(text: str, config: dict[str, float]) -> tuple[str, list[str]]:
    """Apply noise according to config, return (noisy_text, types_applied)."""
    types_applied = []
    if config.get("phonetic", 0) > 0:
        text = apply_phonetic_noise(text, config["phonetic"])
        types_applied.append("phonetic")
    if config.get("typo", 0) > 0:
        text = apply_typo_noise(text, config["typo"])
        types_applied.append("typo")
    if config.get("tone_removal", 0) > 0:
        text = apply_tone_removal(text, config["tone_removal"])
        types_applied.append("tone_removal")
    if config.get("word_merger", 0) > 0:
        text = apply_word_merger(text, config["word_merger"])
        types_applied.append("word_merger")
    if config.get("asr_hallucination", 0) > 0:
        text = apply_asr_hallucination(text, config["asr_hallucination"])
        types_applied.append("asr_hallucination")
    return text, types_applied


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    # Load training data
    rows: list[dict[str, Any]] = []
    with TRAIN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))

    print(f"Loaded {len(rows)} training queries from {TRAIN_PATH}")

    # Generate noisy versions
    output_rows: list[dict[str, Any]] = []
    for row in rows:
        clean_query = row["query"]
        clean_id = row["id"]

        for noise_level, config in NOISE_CONFIGS.items():
            noisy_query, types_applied = apply_noise(clean_query, config)
            output_rows.append({
                "id": f"{clean_id}_noisy_{noise_level}",
                "clean_id": clean_id,
                "clean_query": clean_query,
                "noisy_query": noisy_query,
                "noise_level": noise_level,
                "noise_types_applied": types_applied,
                "expected": row["expected"],
                "group": row.get("group", "unknown"),
            })

    # Write output
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        for r in output_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Summary
    print(f"\nWrote {len(output_rows)} noisy queries to {OUT_PATH}")
    for level in ["light", "medium", "heavy"]:
        count = sum(1 for r in output_rows if r["noise_level"] == level)
        print(f"  {level}: {count} samples")

    # Show examples
    print("\n--- Examples ---")
    for level in ["light", "medium", "heavy"]:
        sample = next(r for r in output_rows if r["noise_level"] == level)
        print(f"\n[{level}] Clean: {sample['clean_query']}")
        print(f"       Noisy: {sample['noisy_query']}")
        print(f"       Types: {sample['noise_types_applied']}")


if __name__ == "__main__":
    main()