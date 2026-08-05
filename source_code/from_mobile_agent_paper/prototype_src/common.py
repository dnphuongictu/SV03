from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
TOOLS_PATH = ROOT / "data" / "tools" / "android_tools.json"
EVAL_PATH = ROOT / "data" / "eval" / "vi_smoke_test.jsonl"
RESULTS_DIR = ROOT / "results"


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def strip_accents(text: str) -> str:
    # "đ/Đ" (U+0111/U+0110) is a base character with stroke, not decomposed
    # by NFD, so it must be replaced explicitly before NFD normalization.
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def normalize_text(value: Any) -> str:
    text = strip_accents(str(value)).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_@.+/*:-]+", normalize_text(text))


def normalize_phone(value: Any) -> str:
    return re.sub(r"\D", "", str(value))

