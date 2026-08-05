"""Adaptive topK analysis — choose K based on BM25 retrieval confidence.

This script:
1. Loads eval data and runs BM25 retriever
2. Computes score distribution
3. Proposes optimal thresholds
4. Estimates accuracy vs prompt length trade-off

Usage:
    python -X utf8 src/adaptive_topk.py --eval data/eval/vi_smoke_test.jsonl --results results
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

import sys

ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def analyze_scores(eval_path: Path, tools_path: Path) -> None:
    """Analyze BM25 score distribution across eval queries."""
    tools = json.loads(tools_path.read_text("utf-8"))
    sys.path.insert(0, str(ROOT / "src"))
    from retrieve import BM25Retriever

    retriever = BM25Retriever(tools)
    examples = load_jsonl(eval_path)

    print(f"Analyzing {len(examples)} queries with BM25 retriever ({len(tools)} tools)")
    print()

    # Collect scores for each query
    all_scores = []
    query_details = []

    for ex in examples:
        ranking = retriever.search(ex["query"], top_k=len(tools))
        scores = [r["score"] for r in ranking]
        top_score = scores[0] if scores else 0
        top3_avg = sum(scores[:3]) / min(3, len(scores)) if scores else 0
        score_drop = scores[0] - scores[1] if len(scores) > 1 else 0

        all_scores.append(top_score)
        query_details.append({
            "id": ex["id"],
            "query": ex["query"],
            "top_score": round(top_score, 4),
            "top3_avg": round(top3_avg, 4),
            "score_drop": round(score_drop, 4),
        })

    # Score distribution
    print("=== BM25 Top Score Distribution ===")
    bins = [(0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6),
            (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.0)]
    for lo, hi in bins:
        count = sum(1 for s in all_scores if lo <= s < hi)
        if count:
            print(f"  [{lo:.1f}, {hi:.1f}): {count} queries ({count/len(all_scores)*100:.1f}%)")

    print(f"\nMax score: {max(all_scores):.4f}")
    print(f"Min score: {min(all_scores):.4f}")
    print(f"Mean score: {sum(all_scores)/len(all_scores):.4f}")

    # Propose thresholds
    print("\n=== Proposed Adaptive topK Thresholds ===")
    thresholds = [
        ("high confidence", 0.7, 1),
        ("medium confidence", 0.4, 2),
        ("low confidence", 0.2, 3),
        ("very low confidence", 0.0, 5),
    ]

    print(f"\n{'Threshold':<25} {'min_score':<12} {'topK':<8} {'Queries':<10}")
    print("-" * 55)
    for label, min_score, top_k in thresholds:
        count = sum(1 for s in all_scores if s >= min_score)
        if top_k == 1:
            # Only top_score >= threshold
            actual_count = sum(1 for s in all_scores if s >= min_score)
            # But this is cumulative, so subtract previous
        print(f"{label:<25} {min_score:<12} {top_k:<8} {count:<10}")

    # Per-threshold assignment
    print("\n=== Adaptive K Assignment ===")
    assignments = []
    for s in all_scores:
        if s >= 0.7:
            assignments.append(1)
        elif s >= 0.4:
            assignments.append(2)
        elif s >= 0.2:
            assignments.append(3)
        else:
            assignments.append(5)

    k_counts = Counter(assignments)
    print(f"K=1: {k_counts[1]} queries (high confidence)")
    print(f"K=2: {k_counts[2]} queries (medium confidence)")
    print(f"K=3: {k_counts[3]} queries (low confidence)")
    print(f"K=5: {k_counts[5]} queries (very low confidence)")

    avg_k = sum(assignments) / len(assignments)
    print(f"\nAverage K: {avg_k:.2f}")
    print(f"Max K: {max(assignments)}")
    print(f"Min K: {min(assignments)}")

    # Estimate tokens saved vs fixed K=5
    # Each tool schema ~120 tokens
    tools_saved = sum(5 - k for k in assignments)
    tokens_saved_est = tools_saved * 120
    print(f"\n=== Prompt Length Estimation ===")
    print(f"Fixed K=5 total tools: {5 * len(all_scores)}")
    print(f"Adaptive K total tools: {sum(assignments)}")
    print(f"Tools saved: {tools_saved}")
    print(f"Estimated tokens saved: ~{tokens_saved_est}")
    print(f"Average prompt length reduction: {(5 - avg_k)/5*100:.1f}%")

    # Show top samples for each confidence tier
    print("\n=== Sample Queries Per Tier ===")
    for tier_label, min_score, max_score in [
        ("HIGH (score >= 0.7)", 0.7, 1.0),
        ("MEDIUM (0.4 <= score < 0.7)", 0.4, 0.7),
        ("LOW (0.2 <= score < 0.4)", 0.2, 0.4),
        ("VERY LOW (score < 0.2)", 0.0, 0.2),
    ]:
        samples = [q for q in query_details if min_score <= q["top_score"] < max_score]
        if samples:
            print(f"\n  [{tier_label}]")
            for s in samples[:3]:
                print(f"    {s['id']}: score={s['top_score']:.4f}")
                print(f"      Query: {s['query'][:60]}...")

    # Detailed listing
    print("\n\n=== Full Query Score Listing ===")
    print(f"{'ID':<25} {'Score':<10} {'Adaptive K':<12} {'Query'}")
    print("-" * 80)
    for qd in sorted(query_details, key=lambda x: x["top_score"]):
        s = qd["top_score"]
        if s >= 0.7:
            k = 1
        elif s >= 0.4:
            k = 2
        elif s >= 0.2:
            k = 3
        else:
            k = 5
        print(f"{qd['id']:<25} {s:<10.4f} {k:<12} {qd['query'][:40]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval", type=Path, default=ROOT / "data" / "eval" / "vi_smoke_test.jsonl")
    parser.add_argument("--tools", type=Path, default=ROOT / "data" / "tools" / "android_tools.json")
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    analyze_scores(args.eval, args.tools)

    # Save analysis
    out_path = args.results / "adaptive_topk_analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Quick summary
    summary = {
        "description": "Adaptive topK analysis based on BM25 retrieval confidence",
        "eval_file": str(args.eval),
        "thresholds": [
            {"label": "high", "min_score": 0.7, "topK": 1},
            {"label": "medium", "min_score": 0.4, "topK": 2},
            {"label": "low", "min_score": 0.2, "topK": 3},
            {"label": "very_low", "min_score": 0.0, "topK": 5},
        ],
    }
    args.results.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\nSummary saved to {out_path}")


if __name__ == "__main__":
    main()