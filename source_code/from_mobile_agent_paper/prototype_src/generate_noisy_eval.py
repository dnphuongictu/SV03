"""Generate noisy versions of the eval smoke test set for ASR robustness testing.

Output:
    data/eval/noisy_smoke_light.jsonl
    data/eval/noisy_smoke_medium.jsonl
    data/eval/noisy_smoke_heavy.jsonl

Usage:
    python -X utf8 src/generate_noisy_eval.py
"""
from __future__ import annotations

import json
import random
import unicodedata
from pathlib import Path
from typing import Any

random.seed(42)

ROOT = Path(__file__).resolve().parents[1]
EVAL_PATH = ROOT / "data" / "eval" / "vi_smoke_test.jsonl"
OUT_DIR = ROOT / "data" / "eval"

# ── Phonetic confusion pairs ────────────────────────────────────────────────
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

FILLERS = ["à", "ờ", "thì", "à mà", "ờ thì", "à ờ", "thì là", "à thì"]


def strip_vi_diacritics(text: str) -> str:
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def apply_phonetic_noise(text: str, rate: float) -> str:
    words = text.split()
    result = []
    for w in words:
        w_lower = w.lower()
        if w_lower in PHONETIC_MAP and random.random() < rate:
            replacement = random.choice(PHONETIC_MAP[w_lower])
            if w[0].isupper():
                replacement = replacement.title()
            result.append(replacement)
        else:
            result.append(w)
    return ' '.join(result)


def apply_typo_noise(text: str, rate: float) -> str:
    chars = list(text)
    n = len(chars)
    for i in range(n):
        if random.random() < rate:
            op = random.choice(['swap', 'delete'])
            if op == 'swap' and i + 1 < n:
                chars[i], chars[i + 1] = chars[i + 1], chars[i]
            elif op == 'delete':
                chars[i] = ''
    return ''.join(c for c in chars if c)


def apply_tone_removal(text: str, rate: float) -> str:
    words = text.split()
    result = []
    for w in words:
        if random.random() < rate:
            result.append(strip_vi_diacritics(w))
        else:
            result.append(w)
    return ' '.join(result)


def apply_word_merger(text: str, rate: float) -> str:
    words = text.split()
    if len(words) < 2:
        return text
    result = list(words)
    n_merges = max(1, int(len(words) * rate))
    for _ in range(n_merges):
        idx = random.randint(0, len(result) - 2)
        result[idx] = result[idx] + result[idx + 1]
        result.pop(idx + 1)
        if len(result) < 2:
            break
    return ' '.join(result)


def apply_asr_hallucination(text: str, rate: float) -> str:
    words = text.split()
    n_fillers = max(1, int(len(words) * rate * 0.5))
    for _ in range(n_fillers):
        idx = random.randint(0, len(words))
        words.insert(idx, random.choice(FILLERS))
    return ' '.join(words)


NOISE_CONFIGS: dict[str, dict[str, float]] = {
    "light": {"phonetic": 0.08, "typo": 0.02, "tone_removal": 0.15, "word_merger": 0.0, "asr_hallucination": 0.0},
    "medium": {"phonetic": 0.15, "typo": 0.05, "tone_removal": 0.30, "word_merger": 0.05, "asr_hallucination": 0.05},
    "heavy": {"phonetic": 0.25, "typo": 0.10, "tone_removal": 0.50, "word_merger": 0.10, "asr_hallucination": 0.10},
}


def apply_noise(text: str, config: dict[str, float]) -> str:
    if config.get("phonetic", 0) > 0:
        text = apply_phonetic_noise(text, config["phonetic"])
    if config.get("typo", 0) > 0:
        text = apply_typo_noise(text, config["typo"])
    if config.get("tone_removal", 0) > 0:
        text = apply_tone_removal(text, config["tone_removal"])
    if config.get("word_merger", 0) > 0:
        text = apply_word_merger(text, config["word_merger"])
    if config.get("asr_hallucination", 0) > 0:
        text = apply_asr_hallucination(text, config["asr_hallucination"])
    return text


def main() -> None:
    # Load eval data
    examples: list[dict[str, Any]] = []
    with EVAL_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                examples.append(json.loads(line))

    print(f"Loaded {len(examples)} eval examples from {EVAL_PATH}")

    # Generate noisy versions for each level
    for level, config in NOISE_CONFIGS.items():
        output_rows = []
        for ex in examples:
            noisy_query = apply_noise(ex["query"], config)
            row = {
                "id": ex["id"],
                "group": ex["group"],
                "query": noisy_query,
                "expected": ex["expected"],
                "clean_query": ex["query"],
                "noise_level": level,
            }
            output_rows.append(row)

        out_path = OUT_DIR / f"noisy_smoke_{level}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in output_rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        print(f"\n[{level}] {EVAL_PATH.stem} → noisy_smoke_{level}.jsonl ({len(output_rows)} samples)")
        for r in output_rows[:3]:
            print(f"  Clean: {r['clean_query']}")
            print(f"  Noisy: {r['query']}")


if __name__ == "__main__":
    main()