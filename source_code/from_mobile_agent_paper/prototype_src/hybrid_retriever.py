from __future__ import annotations

import argparse
from typing import Any

from pathlib import Path
import json

from dense_retriever import DenseRetriever, _DEFAULT_MODEL
from retrieve import BM25Retriever


class HybridRetriever:
    """Combines BM25 and dense retrieval scores via min-max normalization.

    Both BM25 and dense scores are independently min-max normalised to [0, 1]
    on a per-query basis before being linearly combined:

        score = alpha * dense_norm + (1 - alpha) * bm25_norm

    Parameters
    ----------
    tools:
        List of tool dicts (same format as android_tools.json).
    alpha:
        Weight for the dense component. 0 = pure BM25, 1 = pure dense.
    model_name:
        HuggingFace model identifier for the dense encoder.
    """

    def __init__(
        self,
        tools: list[dict[str, Any]],
        alpha: float = 0.5,
        model_name: str = _DEFAULT_MODEL,
        revision: str | None = None,
    ) -> None:
        self.alpha = alpha
        self.tools = tools
        self.bm25 = BM25Retriever(tools)
        self.dense = DenseRetriever(tools, model_name=model_name, revision=revision)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        n = len(self.tools)

        bm25_results = self.bm25.search(query, top_k=n)
        dense_results = self.dense.search(query, top_k=n)

        bm25_map = {r["tool"]: r["score"] for r in bm25_results}
        dense_map = {r["tool"]: r["score"] for r in dense_results}

        # Min-max normalise BM25 scores (always non-negative)
        bm25_vals = list(bm25_map.values())
        bm25_min, bm25_max = min(bm25_vals), max(bm25_vals)
        bm25_range = max(bm25_max - bm25_min, 1e-9)

        # Min-max normalise dense scores (cosine similarities, typically 0.2–0.9)
        dense_vals = list(dense_map.values())
        dense_min, dense_max = min(dense_vals), max(dense_vals)
        dense_range = max(dense_max - dense_min, 1e-9)

        combined = []
        for tool_name in bm25_map:
            b_norm = (bm25_map[tool_name] - bm25_min) / bm25_range
            d_norm = (dense_map.get(tool_name, dense_min) - dense_min) / dense_range
            hybrid = self.alpha * d_norm + (1.0 - self.alpha) * b_norm
            combined.append({"tool": tool_name, "score": round(hybrid, 6)})

        combined.sort(key=lambda x: (-x["score"], x["tool"]))
        return combined[:top_k]

    def adaptive_search(self, query: str, max_k: int = 5, k_min: int = 2) -> tuple[list[dict], int]:
        """Search with adaptive K based on hybrid score confidence.

        Uses the score gap between rank-1 and rank-2 as confidence signal.
        A large gap means the top tool is unambiguously better than the rest.
        k_min=2 enforces a safe lower bound (K=1 is too risky for accuracy).

        Thresholds (calibrated on 32-sample smoke test, v2.1 adapter):
            gap >= 0.25 → K=2  (high confidence, 40% prompt saving vs K=5)
            gap >= 0.10 → K=3  (medium confidence, 40% saving)
            else        → K=max_k (low confidence, no reduction)
        """
        ranking = self.search(query, top_k=max_k)
        if len(ranking) >= 2:
            gap = ranking[0]["score"] - ranking[1]["score"]
        elif ranking:
            gap = 1.0  # single tool in index
        else:
            gap = 0.0

        if gap >= 0.25:
            k = 2
        elif gap >= 0.10:
            k = 3
        else:
            k = max_k

        k = max(k, k_min)
        return ranking[:k], k


def _get_root() -> Path:
    """Return project root (parent of src/)."""
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


def evaluate_retrieval(
    top_k: int,
    retriever: HybridRetriever | None = None,
    alpha: float = 0.5,
) -> dict[str, Any]:
    root = _get_root()
    tools_path = root / "data" / "tools" / "android_tools.json"
    eval_path = root / "data" / "eval" / "vi_smoke_test.jsonl"
    results_dir = root / "results"

    if retriever is None:
        retriever = HybridRetriever(_load_json(tools_path), alpha=alpha)
    examples = _load_jsonl(eval_path)
    rows = []
    supported = 0
    hits = 0
    reciprocal_rank = 0.0

    for example in examples:
        expected_tool = example["expected"].get("tool")
        ranking = retriever.search(example["query"], top_k=top_k)
        rank = next(
            (i for i, item in enumerate(ranking, start=1) if item["tool"] == expected_tool),
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
    report = {
        "top_k": top_k,
        "alpha": retriever.alpha,
        "supported_examples": supported,
        "recall_at_k": hits / supported if supported else 0.0,
        "mrr_at_k": reciprocal_rank / supported if supported else 0.0,
        "rows": rows,
    }
    output = results_dir / f"hybrid_top_{top_k}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--alpha", type=float, default=0.5)
    parser.add_argument("--model", type=str, default=_DEFAULT_MODEL)
    args = parser.parse_args()

    root = _get_root()
    tools_path = root / "data" / "tools" / "android_tools.json"
    retriever = HybridRetriever(_load_json(tools_path), alpha=args.alpha, model_name=args.model)
    report = evaluate_retrieval(args.top_k, retriever=retriever)
    print(
        f"Hybrid(alpha={args.alpha}) Recall@{args.top_k}: {report['recall_at_k']:.3f} | "
        f"MRR@{args.top_k}: {report['mrr_at_k']:.3f}"
    )


if __name__ == "__main__":
    main()
