from __future__ import annotations

import argparse
import json
from typing import Any

from pathlib import Path


_DEFAULT_MODEL = "intfloat/multilingual-e5-small"


def _tool_passage(tool: dict[str, Any]) -> str:
    name = tool["name"].replace("_", " ")
    desc_vi = tool.get("description_vi", "")
    desc_en = tool.get("description_en", "")
    args = ", ".join(tool.get("arguments", {}).keys())
    return f"passage: {name}. {desc_vi}. {desc_en}. Parameters: {args}."


class DenseRetriever:
    """Dense retriever using multilingual sentence embeddings.

    Uses the "query: / passage: " prefix convention required by
    intfloat/multilingual-e5-* models.
    """

    def __init__(
        self,
        tools: list[dict[str, Any]],
        model_name: str = _DEFAULT_MODEL,
        revision: str | None = None,
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            raise SystemExit(
                "Install sentence-transformers before using DenseRetriever: "
                "pip install sentence-transformers"
            ) from e

        self.tools = tools
        self.model = SentenceTransformer(model_name, revision=revision)

        passages = [_tool_passage(t) for t in tools]
        self.embeddings = self.model.encode(
            passages,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        q_emb = self.model.encode(
            f"query: {query}",
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        # Cosine similarity = dot product (embeddings are unit-norm)
        scores = self.embeddings @ q_emb
        ranked = [
            {"tool": t["name"], "score": float(s)}
            for t, s in zip(self.tools, scores)
        ]
        ranked.sort(key=lambda x: (-x["score"], x["tool"]))
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


def evaluate_retrieval(top_k: int, retriever: DenseRetriever | None = None) -> dict[str, Any]:
    root = _get_root()
    tools_path = root / "data" / "tools" / "android_tools.json"
    eval_path = root / "data" / "eval" / "vi_smoke_test.jsonl"
    results_dir = root / "results"

    if retriever is None:
        retriever = DenseRetriever(_load_json(tools_path))
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
        "supported_examples": supported,
        "recall_at_k": hits / supported if supported else 0.0,
        "mrr_at_k": reciprocal_rank / supported if supported else 0.0,
        "rows": rows,
    }
    output = results_dir / f"dense_top_{top_k}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--model", type=str, default=_DEFAULT_MODEL)
    args = parser.parse_args()

    root = _get_root()
    tools_path = root / "data" / "tools" / "android_tools.json"
    retriever = DenseRetriever(_load_json(tools_path), model_name=args.model)
    report = evaluate_retrieval(args.top_k, retriever=retriever)
    print(
        f"Dense Recall@{args.top_k}: {report['recall_at_k']:.3f} | "
        f"MRR@{args.top_k}: {report['mrr_at_k']:.3f}"
    )


if __name__ == "__main__":
    main()
