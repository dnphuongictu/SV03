"""
A2: McNemar exact test comparing per-example E2E correctness
between pairs of models on the same eval set.

Usage:
  python src/mcnemar_test.py results/rescored/v21_final_rescored.json \
                             results/rescored/v4_final_rescored.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def binom_pmf(k: int, n: int, p: float) -> float:
    """Exact binomial PMF using log to avoid overflow."""
    if n < 0 or k < 0 or k > n:
        return 0.0
    log_c = (
        sum(math.log(n - i) for i in range(k))
        - sum(math.log(i + 1) for i in range(k))
    )
    return math.exp(log_c + k * math.log(p) + (n - k) * math.log(1 - p))


def mcnemar_exact_pvalue(b: int, c: int) -> float:
    """
    Two-sided exact McNemar p-value (binomial with p=0.5, sum both tails).
    b = #(A correct, B wrong), c = #(A wrong, B correct)
    """
    n = b + c
    if n == 0:
        return 1.0
    # observed minority count
    observed = min(b, c)
    # p-value = P(X <= observed) + P(X >= n - observed) where X ~ Bin(n, 0.5)
    p = sum(binom_pmf(k, n, 0.5) for k in range(observed + 1))
    p = 2 * p
    return min(p, 1.0)


def load_per_example(path: Path) -> dict[str, bool]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row["id"]: row["end_to_end"] for row in data["per_example"]}


def compare(name_a: str, path_a: Path, name_b: str, path_b: Path) -> None:
    a = load_per_example(path_a)
    b = load_per_example(path_b)

    ids = sorted(set(a) & set(b))
    if not ids:
        print(f"No common IDs between {name_a} and {name_b}")
        return

    bc, cb, bb, cc_ = 0, 0, 0, 0
    discordant_ids = {"a_correct_b_wrong": [], "b_correct_a_wrong": []}
    for id_ in ids:
        ca, cb_ = a[id_], b[id_]
        if ca and cb_:
            bb += 1
        elif ca and not cb_:
            bc += 1
            discordant_ids["a_correct_b_wrong"].append(id_)
        elif not ca and cb_:
            cb += 1
            discordant_ids["b_correct_a_wrong"].append(id_)
        else:
            cc_ += 1

    n = len(ids)
    acc_a = sum(a[i] for i in ids) / n
    acc_b = sum(b[i] for i in ids) / n

    p = mcnemar_exact_pvalue(bc, cb)

    print(f"\n{'='*60}")
    print(f"McNemar Exact Test: {name_a}  vs  {name_b}")
    print(f"{'='*60}")
    print(f"  N = {n}")
    print(f"  {name_a} E2E = {acc_a:.4f}  ({int(acc_a*n)}/{n})")
    print(f"  {name_b} E2E = {acc_b:.4f}  ({int(acc_b*n)}/{n})")
    print(f"  Both correct (bb)   = {bb}")
    print(f"  Both wrong   (cc)   = {cc_}")
    print(f"  {name_a} only correct (b) = {bc}")
    print(f"  {name_b} only correct (c) = {cb}")
    print(f"  Discordant pairs b+c = {bc+cb}")
    print(f"  p-value (exact, two-sided) = {p:.4f}")
    if p < 0.05:
        print(f"  *** SIGNIFICANT at alpha=0.05 ***")
    else:
        print(f"  Not significant (p={p:.4f} > 0.05)")
        print(f"  => Cannot claim {name_b} improves over {name_a}")

    if discordant_ids["a_correct_b_wrong"]:
        print(f"\n  {name_a} correct / {name_b} wrong:")
        for id_ in discordant_ids["a_correct_b_wrong"]:
            print(f"    {id_}")
    if discordant_ids["b_correct_a_wrong"]:
        print(f"\n  {name_b} correct / {name_a} wrong:")
        for id_ in discordant_ids["b_correct_a_wrong"]:
            print(f"    {id_}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_a", type=Path)
    parser.add_argument("report_b", type=Path)
    parser.add_argument("--name-a", default=None)
    parser.add_argument("--name-b", default=None)
    args = parser.parse_args()

    name_a = args.name_a or args.report_a.stem
    name_b = args.name_b or args.report_b.stem
    compare(name_a, args.report_a, name_b, args.report_b)


if __name__ == "__main__":
    main()
