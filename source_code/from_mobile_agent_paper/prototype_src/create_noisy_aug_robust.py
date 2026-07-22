"""
Generate noisy augmentation of train366 for robustness training (v_robust).

Creates 2 noisy copies of each sample:
  - light  : 20-30% tone drop, 10% modifier strip, 5% word-merge
  - medium : 45-55% tone drop, 25% modifier strip, 12% word-merge

Output: vi_droidcall_train_robust.jsonl
  = train366 (clean) + train366_light + train366_medium = 1098 samples

Usage:
    python src/create_noisy_aug_robust.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

SRC  = Path(__file__).resolve().parent
ROOT = SRC.parent
DATA = ROOT / "data" / "eval"

TRAIN366  = DATA / "vi_droidcall_train366_v7.jsonl"
OUT_FILE  = DATA / "vi_droidcall_train_robust.jsonl"

SEED = 42
random.seed(SEED)

# ---------------------------------------------------------------------------
# Vietnamese tone/modifier tables
# ---------------------------------------------------------------------------

# tone-strip: remove only the tone mark, keep the base vowel (with modifier if any)
TONE_STRIP = str.maketrans({
    'á': 'a', 'à': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
    'Á': 'A', 'À': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
    'ắ': 'ă', 'ằ': 'ă', 'ẳ': 'ă', 'ẵ': 'ă', 'ặ': 'ă',
    'Ắ': 'Ă', 'Ằ': 'Ă', 'Ẳ': 'Ă', 'Ẵ': 'Ă', 'Ặ': 'Ă',
    'ấ': 'â', 'ầ': 'â', 'ẩ': 'â', 'ẫ': 'â', 'ậ': 'â',
    'Ấ': 'Â', 'Ầ': 'Â', 'Ẩ': 'Â', 'Ẫ': 'Â', 'Ậ': 'Â',
    'é': 'e', 'è': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
    'É': 'E', 'È': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
    'ế': 'ê', 'ề': 'ê', 'ể': 'ê', 'ễ': 'ê', 'ệ': 'ê',
    'Ế': 'Ê', 'Ề': 'Ê', 'Ể': 'Ê', 'Ễ': 'Ê', 'Ệ': 'Ê',
    'í': 'i', 'ì': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
    'Í': 'I', 'Ì': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
    'ó': 'o', 'ò': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
    'Ó': 'O', 'Ò': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
    'ố': 'ô', 'ồ': 'ô', 'ổ': 'ô', 'ỗ': 'ô', 'ộ': 'ô',
    'Ố': 'Ô', 'Ồ': 'Ô', 'Ổ': 'Ô', 'Ỗ': 'Ô', 'Ộ': 'Ô',
    'ớ': 'ơ', 'ờ': 'ơ', 'ở': 'ơ', 'ỡ': 'ơ', 'ợ': 'ơ',
    'Ớ': 'Ơ', 'Ờ': 'Ơ', 'Ở': 'Ơ', 'Ỡ': 'Ơ', 'Ợ': 'Ơ',
    'ú': 'u', 'ù': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
    'Ú': 'U', 'Ù': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
    'ứ': 'ư', 'ừ': 'ư', 'ử': 'ư', 'ữ': 'ư', 'ự': 'ư',
    'Ứ': 'Ư', 'Ừ': 'Ư', 'Ử': 'Ư', 'Ữ': 'Ư', 'Ự': 'Ư',
    'ý': 'y', 'ỳ': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
    'Ý': 'Y', 'Ỳ': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y',
})

# modifier-strip: also remove vowel modifier (ă→a, â→a, ê→e, ô→o, ơ→o, ư→u, đ→d)
MODIFIER_STRIP = str.maketrans({
    'ă': 'a', 'Ă': 'A',
    'â': 'a', 'Â': 'A',
    'ê': 'e', 'Ê': 'E',
    'ô': 'o', 'Ô': 'O',
    'ơ': 'o', 'Ơ': 'O',
    'ư': 'u', 'Ư': 'U',
    'đ': 'd', 'Đ': 'D',
})

# Characters that have tones or modifiers (for per-character probability)
DIACRITIC_CHARS = set(TONE_STRIP.keys()) | set(MODIFIER_STRIP.keys())
# Also those with both tone + modifier combined (e.g. ắ, ấ, etc.)
TONED_MODIFIED  = set(TONE_STRIP.keys()) - set('aăâeêioôơuưy' + 'AĂÂEÊIOÔƠUƯY')


def strip_tone(ch: str) -> str:
    return ch.translate(TONE_STRIP)


def strip_modifier(ch: str) -> str:
    return ch.translate(MODIFIER_STRIP)


def add_noise(text: str, p_tone: float, p_modifier: float, p_merge: float, rng: random.Random) -> str:
    """
    Apply noise to a Vietnamese text string.
    - p_tone:     probability of stripping tone from a diacritic char
    - p_modifier: probability of also stripping the vowel modifier (applied AFTER tone)
    - p_merge:    probability of merging each space between two words into nothing
    """
    # Step 1: per-character tone + modifier drop
    result: list[str] = []
    for ch in text:
        if ch in DIACRITIC_CHARS and rng.random() < p_tone:
            ch = strip_tone(ch)
        # After potential tone strip, modifier strip
        if ch in MODIFIER_STRIP and rng.random() < p_modifier:
            ch = strip_modifier(ch)
        result.append(ch)
    noisy = ''.join(result)

    # Step 2: space merge (randomly drop spaces between tokens)
    if p_merge > 0:
        parts = noisy.split(' ')
        merged: list[str] = [parts[0]] if parts else []
        for part in parts[1:]:
            if rng.random() < p_merge:
                merged[-1] = merged[-1] + part   # merge with previous (no space)
            else:
                merged.append(part)
        noisy = ' '.join(merged)

    return noisy


def make_noisy_sample(sample: dict, noise_level: str, rng: random.Random) -> dict:
    """Return new sample dict with noisy query, keeping same expected output."""
    if noise_level == "light":
        q = add_noise(sample["query"], p_tone=0.25, p_modifier=0.10, p_merge=0.05, rng=rng)
    elif noise_level == "medium":
        q = add_noise(sample["query"], p_tone=0.50, p_modifier=0.25, p_merge=0.12, rng=rng)
    else:
        raise ValueError(f"Unknown noise_level: {noise_level}")

    new_id = f"{sample['id']}_noisy_{noise_level}"
    return {
        "id": new_id,
        "query": q,
        "expected": sample["expected"],
        "clean_query": sample["query"],
        "noise_level": noise_level,
    }


def main() -> None:
    if not TRAIN366.exists():
        print(f"ERROR: {TRAIN366} not found. Run create_v7_train.py first.", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(SEED)

    train366: list[dict] = []
    with TRAIN366.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                train366.append(json.loads(line))

    print(f"Loaded {len(train366)} samples from train366")

    # Build combined dataset: clean + light + medium
    all_samples: list[dict] = []

    # 1. Original clean samples
    all_samples.extend(train366)

    # 2. Light noisy variants
    light_samples = [make_noisy_sample(s, "light", rng) for s in train366]
    all_samples.extend(light_samples)

    # 3. Medium noisy variants
    medium_samples = [make_noisy_sample(s, "medium", rng) for s in train366]
    all_samples.extend(medium_samples)

    print(f"Total robust training samples: {len(all_samples)}")
    print(f"  clean : {len(train366)}")
    print(f"  light : {len(light_samples)}")
    print(f"  medium: {len(medium_samples)}")

    # Verify no duplicate IDs
    ids = [s["id"] for s in all_samples]
    assert len(ids) == len(set(ids)), "Duplicate IDs!"

    # Shuffle (so clean/noisy are interleaved during training)
    rng.shuffle(all_samples)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with OUT_FILE.open("w", encoding="utf-8") as f:
        for s in all_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"Saved -> {OUT_FILE}")

    # Verify a few examples (write to stderr as UTF-8)
    import io
    stderr_utf8 = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8") if hasattr(sys.stderr, "buffer") else sys.stderr
    for s in train366[:3]:
        light  = make_noisy_sample(s, "light",  random.Random(0))
        medium = make_noisy_sample(s, "medium", random.Random(0))
        stderr_utf8.write(f"  clean : {s['query']}\n")
        stderr_utf8.write(f"  light : {light['query']}\n")
        stderr_utf8.write(f"  medium: {medium['query']}\n\n")
    stderr_utf8.flush()


if __name__ == "__main__":
    main()
