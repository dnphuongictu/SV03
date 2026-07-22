from __future__ import annotations

import argparse
import math
from collections import Counter
from typing import Any

import json
import re
import unicodedata
from pathlib import Path


def _strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _normalize_text(value: Any) -> str:
    text = _strip_accents(str(value)).lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_@.+/*:-]+", _normalize_text(text))


class BM25Retriever:
    def __init__(self, tools: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.tools = tools
        self.k1 = k1
        self.b = b
        self.documents = [
            _tokenize(
                " ".join(
                    [
                        tool["name"].replace("_", " "),
                        tool.get("description_vi", ""),
                        tool.get("description_en", ""),
                        " ".join(tool.get("arguments", {}).keys()),
                    ]
                )
            )
            for tool in tools
        ]
        self.lengths = [len(document) for document in self.documents]
        self.average_length = sum(self.lengths) / max(len(self.lengths), 1)
        self.term_frequencies = [Counter(document) for document in self.documents]
        document_frequency = Counter()
        for document in self.documents:
            document_frequency.update(set(document))
        count = len(self.documents)
        self.idf = {
            term: math.log(1 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_terms = _tokenize(query)
        ranked = []
        for index, frequencies in enumerate(self.term_frequencies):
            score = 0.0
            length = self.lengths[index]
            for term in query_terms:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                numerator = frequency * (self.k1 + 1)
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / max(self.average_length, 1)
                )
                score += self.idf.get(term, 0.0) * numerator / denominator
            ranked.append(
                {
                    "tool": self.tools[index]["name"],
                    # Preserve full precision so hybrid normalization exactly
                    # matches the successful fresh-locked Kaggle v3 notebook.
                    "score": float(score),
                }
            )
        ranked.sort(key=lambda item: (-item["score"], item["tool"]))
        return ranked[:top_k]


def _get_root() -> Path:
    return Path(__file__).resolve().parents[1]

def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def _load_jsonl(path: Path) -> list[dict[str, Any]]:
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


def evaluate_retrieval(top_k: int) -> dict[str, Any]:
    root = _get_root()
    tools_path = root / "data" / "tools" / "android_tools.json"
    eval_path = root / "data" / "eval" / "vi_smoke_test.jsonl"
    results_dir = root / "results"

    retriever = BM25Retriever(_load_json(tools_path))
    examples = _load_jsonl(eval_path)
    rows = []
    supported = 0
    hits = 0
    reciprocal_rank = 0.0

    for example in examples:
        expected_tool = example["expected"].get("tool")
        ranking = retriever.search(example["query"], top_k=top_k)
        rank = next(
            (
                index
                for index, item in enumerate(ranking, start=1)
                if item["tool"] == expected_tool
            ),
            None,
        )
        if expected_tool is not None:
            supported += 1
            if rank is not None:
                hits += 1
                reciprocal_rank += 1 / rank
        rows.append(
            {
                "id": example["id"],
                "query": example["query"],
                "expected_tool": expected_tool,
                "ranking": ranking,
                "rank": rank,
            }
        )

    results_dir.mkdir(parents=True, exist_ok=True)
    output = results_dir / f"bm25_top_{top_k}.json"
    report = {
        "top_k": top_k,
        "supported_examples": supported,
        "recall_at_k": hits / supported if supported else 0.0,
        "mrr_at_k": reciprocal_rank / supported if supported else 0.0,
        "rows": rows,
    }

    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    report = evaluate_retrieval(args.top_k)
    print(
        f"Recall@{args.top_k}: {report['recall_at_k']:.3f} | "
        f"MRR@{args.top_k}: {report['mrr_at_k']:.3f}"
    )


if __name__ == "__main__":
    main()
