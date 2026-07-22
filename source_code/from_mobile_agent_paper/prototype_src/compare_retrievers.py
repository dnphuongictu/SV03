"""Compare BM25, Dense, and Hybrid retrievers across multiple k values.

Usage (from prototype/ directory):
    python -X utf8 src/compare_retrievers.py
    python -X utf8 src/compare_retrievers.py --ks 1 3 5 8
"""
from __future__ import annotations

import argparse
import time
from typing import Any

from common import load_json, TOOLS_PATH
from retrieve import BM25Retriever
from retrieve import evaluate_retrieval as bm25_eval
from dense_retriever import DenseRetriever
from dense_retriever import evaluate_retrieval as dense_eval
from hybrid_retriever import HybridRetriever
from hybrid_retriever import evaluate_retrieval as hybrid_eval


def _latency_ms(retriever: Any, query: str, top_k: int, runs: int = 20) -> float:
    for _ in range(3):  # warm-up
        retriever.search(query, top_k=top_k)
    start = time.perf_counter()
    for _ in range(runs):
        retriever.search(query, top_k=top_k)
    return (time.perf_counter() - start) / runs * 1000


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ks", type=int, nargs="+", default=[1, 3, 5, 8])
    parser.add_argument("--alpha", type=float, default=0.5)
    args = parser.parse_args()

    tools = load_json(TOOLS_PATH)

    print("Loading models …")
    bm25 = BM25Retriever(tools)
    dense = DenseRetriever(tools)
    hybrid = HybridRetriever(tools, alpha=args.alpha)
    print("Done.\n")

    _SAMPLE = "Đặt báo thức lúc 7 giờ sáng mai"

    lat_bm25 = _latency_ms(bm25, _SAMPLE, top_k=5)
    lat_dense = _latency_ms(dense, _SAMPLE, top_k=5)
    lat_hybrid = _latency_ms(hybrid, _SAMPLE, top_k=5)

    header = f"{'Retriever':<24} {'@k':>3}  {'Recall':>7}  {'MRR':>7}"
    print(header)
    print("-" * len(header))

    for k in args.ks:
        rb = bm25_eval(k)
        rd = dense_eval(k, retriever=dense)
        rh = hybrid_eval(k, retriever=hybrid)
        for label, report in [("BM25", rb), (f"Dense(e5-small)", rd), (f"Hybrid(a={args.alpha})", rh)]:
            print(
                f"{label:<24} {k:>3}  {report['recall_at_k']:>7.3f}  {report['mrr_at_k']:>7.3f}"
            )
        print()

    print(f"\nLatency per query (top-5, {_SAMPLE!r}):")
    print(f"  BM25   : {lat_bm25:.1f} ms")
    print(f"  Dense  : {lat_dense:.1f} ms")
    print(f"  Hybrid : {lat_hybrid:.1f} ms")


if __name__ == "__main__":
    main()
