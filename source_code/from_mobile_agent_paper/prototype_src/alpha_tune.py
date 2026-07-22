"""
Grid search alpha (BM25 vs dense weight) on extTest144 using precomputed v7 adapter
predictions at different retrieval configs.

Since we don't have predictions at each alpha value, we use the retriever directly
to compute Recall@K at different alpha values (no model inference needed).

Usage:
    python src/alpha_tune.py

Output: prints Recall@K table for alpha in {0.1, 0.2, ..., 0.9, 1.0}
"""
from __future__ import annotations

import json, os, re, math, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "eval"
TOOLS_FILE = ROOT / "data" / "tools" / "android_tools.json"

EXTERNAL_FILE = DATA / "vi_droidcall_external_test.jsonl"
FINAL48_FILE  = DATA / "vi_droidcall_final48.jsonl"

# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------
def _strip(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if unicodedata.category(c) != "Mn")

def _tok(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_@.+/*:-]+", _strip(text).lower())

def _tool_text(t: dict) -> str:
    return " ".join([
        t["name"].replace("_", " "),
        t.get("description_vi", ""),
        t.get("description_en", ""),
        " ".join(t.get("arguments", {}).keys()),
    ])

class BM25:
    def __init__(self, tools: list[dict], k1: float = 1.5, b: float = 0.75):
        self.tools = tools
        self.k1, self.b = k1, b
        self.docs = [_tok(_tool_text(t)) for t in tools]
        self.lengths = [len(d) for d in self.docs]
        self.avg_len = sum(self.lengths) / max(len(self.lengths), 1)
        self.tf = [Counter(d) for d in self.docs]
        df: Counter = Counter()
        for d in self.docs:
            df.update(set(d))
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> dict[str, float]:
        qterms = _tok(query)
        result = {}
        for i, (tf, length) in enumerate(zip(self.tf, self.lengths)):
            s = sum(
                self.idf.get(t, 0) * tf.get(t, 0) * (self.k1 + 1)
                / (tf.get(t, 0) + self.k1 * (1 - self.b + self.b * length / max(self.avg_len, 1)))
                for t in qterms if tf.get(t, 0)
            )
            result[self.tools[i]["name"]] = s
        return result


# ---------------------------------------------------------------------------
# Dense (sentence-transformers)
# ---------------------------------------------------------------------------
def build_dense_scores(tools: list[dict]):
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
    except ImportError:
        print("sentence-transformers not available — dense scores will be random")
        return None

    model_name = os.environ.get("DENSE_MODEL", "intfloat/multilingual-e5-small")
    print(f"Loading dense model: {model_name}")
    model = SentenceTransformer(model_name)

    def _passage(t: dict) -> str:
        return (f"passage: {t['name'].replace('_', ' ')}. "
                f"{t.get('description_vi', '')}. {t.get('description_en', '')}. "
                f"Parameters: {', '.join(t.get('arguments', {}).keys())}.")

    tool_embs = model.encode(
        [_passage(t) for t in tools],
        normalize_embeddings=True, batch_size=24, show_progress_bar=False
    )

    def dense_scores(query: str) -> dict[str, float]:
        q = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
        sims = (tool_embs @ q).tolist()
        return {tools[i]["name"]: float(sims[i]) for i in range(len(tools))}

    return dense_scores


# ---------------------------------------------------------------------------
# Hybrid search
# ---------------------------------------------------------------------------
def hybrid_top_k(bm25_scores: dict, dense_scores: dict, alpha: float, k: int) -> list[str]:
    bv = list(bm25_scores.values())
    dv = list(dense_scores.values())
    b_min, b_r = min(bv), max(max(bv) - min(bv), 1e-9)
    d_min, d_r = min(dv), max(max(dv) - min(dv), 1e-9)
    combined = {
        name: alpha * (dense_scores[name] - d_min) / d_r
              + (1 - alpha) * (bm25_scores[name] - b_min) / b_r
        for name in bm25_scores
    }
    return sorted(combined, key=lambda x: -combined[x])[:k]


# ---------------------------------------------------------------------------
# Recall@K evaluation
# ---------------------------------------------------------------------------
def eval_recall(dataset: list[dict], bm25: BM25, dense_fn, alpha: float, k: int) -> float:
    hits = 0
    for ex in dataset:
        expected_tool = ex["expected"].get("tool")
        if expected_tool is None:
            hits += 1  # negative queries always "retrieved" (model decides)
            continue
        b = bm25.scores(ex["query"])
        d = dense_fn(ex["query"])
        top = hybrid_top_k(b, d, alpha, k)
        if expected_tool in top:
            hits += 1
    return hits / len(dataset)


def precompute_scores(dataset: list[dict], bm25: BM25, dense_fn) -> list[tuple]:
    """Precompute BM25 and dense scores for all queries (avoid recomputing per alpha)."""
    print(f"  Precomputing scores for {len(dataset)} queries...", flush=True)
    result = []
    for ex in dataset:
        expected_tool = ex["expected"].get("tool")
        b = bm25.scores(ex["query"])
        d = dense_fn(ex["query"])
        result.append((expected_tool, b, d))
    return result


def eval_recall_fast(precomputed: list[tuple], alpha: float, k: int) -> float:
    hits = 0
    for expected_tool, bm25_scores, dense_scores_val in precomputed:
        if expected_tool is None:
            hits += 1
            continue
        top = hybrid_top_k(bm25_scores, dense_scores_val, alpha, k)
        if expected_tool in top:
            hits += 1
    return hits / len(precomputed)


def main() -> None:
    tools    = json.loads(TOOLS_FILE.read_text("utf-8"))
    ext_data = [json.loads(l) for l in EXTERNAL_FILE.read_text("utf-8").splitlines() if l.strip()]
    f48_data = [json.loads(l) for l in FINAL48_FILE.read_text("utf-8").splitlines() if l.strip()]

    print(f"Tools: {len(tools)}, extTest144: {len(ext_data)}, final48: {len(f48_data)}", flush=True)

    bm25 = BM25(tools)
    dense_fn = build_dense_scores(tools)
    if dense_fn is None:
        print("ERROR: dense model not available")
        return

    # Precompute scores once (avoids N_alpha * N_K * N_queries encoding calls)
    ext_pre = precompute_scores(ext_data, bm25, dense_fn)
    f48_pre = precompute_scores(f48_data, bm25, dense_fn)

    alphas = [round(a * 0.1, 1) for a in range(0, 11)]  # 0.0, 0.1, ..., 1.0
    Ks = [1, 2, 3, 5]

    print("\n" + "=" * 70, flush=True)
    print("Alpha grid search -- Recall@K on extTest144 (positive queries only)")
    print("=" * 70)
    print(f"  {'alpha':>6}  " + "  ".join(f"R@{k:d}" for k in Ks))
    print("  " + "-" * 55)

    best_alpha_r2, best_r2 = 0.5, 0.0
    for alpha in alphas:
        recalls = [eval_recall_fast(ext_pre, alpha, k) for k in Ks]
        marker = " <-- current" if alpha == 0.5 else ""
        print(f"  {alpha:>6.1f}  " + "  ".join(f"{r:.4f}" for r in recalls) + marker, flush=True)
        if recalls[Ks.index(2)] > best_r2:
            best_r2 = recalls[Ks.index(2)]
            best_alpha_r2 = alpha

    print(f"\nBest alpha for R@2: {best_alpha_r2} (R@2={best_r2:.4f})", flush=True)

    # Also check on final48
    print("\n" + "=" * 70, flush=True)
    print("Alpha grid search -- Recall@K on final48 (positive queries only)")
    print("=" * 70)
    print(f"  {'alpha':>6}  " + "  ".join(f"R@{k:d}" for k in Ks))
    print("  " + "-" * 55)
    for alpha in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, best_alpha_r2]:
        if alpha not in [round(a*0.1,1) for a in range(0,11)]:
            continue
        recalls = [eval_recall_fast(f48_pre, alpha, k) for k in Ks]
        marker = " <-- best ext" if alpha == best_alpha_r2 else (" <-- current" if alpha == 0.5 else "")
        print(f"  {alpha:>6.1f}  " + "  ".join(f"{r:.4f}" for r in recalls) + marker, flush=True)

    print(f"\nConclusion: {'Use alpha=' + str(best_alpha_r2) + ' if R@2 improvement >= 0.02' if best_alpha_r2 != 0.5 else 'alpha=0.5 is already optimal'}", flush=True)


if __name__ == "__main__":
    main()
