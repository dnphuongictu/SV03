"""Standalone evaluation for custom eval datasets.

Usage:
    python -X utf8 src/evaluate_custom.py \\
        --predictions results/p5_codeswitch_top5.jsonl \\
        --eval-path data/eval/codeswitch_queries.jsonl \\
        --output results/p5_codeswitch_top5_report.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import load_jsonl, normalize_phone, normalize_text
from validate import ToolValidator

_CONTACT_HONORIFICS = {
    "anh", "chi", "chị", "em", "co", "cô", "chu", "chú",
    "bac", "bác", "ong", "ông", "ba", "bà", "thay", "thầy", "ban", "bạn",
}


def _normalize_contact_name(text: str) -> str:
    cleaned = text.replace("_", " ").strip()
    parts = cleaned.split(None, 1)
    if len(parts) == 2 and parts[0].lower() in _CONTACT_HONORIFICS:
        return parts[1].strip()
    return cleaned


def values_match(name: str, expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and values_match(key, value, actual[key])
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            return False
        normalized_expected = sorted(normalize_text(item) for item in expected)
        normalized_actual = sorted(normalize_text(item) for item in actual)
        return normalized_expected == normalized_actual
    if isinstance(expected, bool) or isinstance(expected, int):
        return expected == actual
    if "phone" in name.lower():
        return normalize_phone(expected) == normalize_phone(actual)
    if name.lower() == "name":
        return (
            _normalize_contact_name(normalize_text(expected))
            == _normalize_contact_name(normalize_text(actual))
        )
    return normalize_text(expected) == normalize_text(actual)


def argument_score(expected: dict[str, Any], actual: dict[str, Any]) -> tuple[int, int]:
    correct = sum(
        1
        for name, value in expected.items()
        if name in actual and values_match(name, value, actual[name])
    )
    return correct, len(expected)


def evaluate_custom(eval_path: Path, predictions_path: Path) -> dict[str, Any]:
    """Evaluate predictions against a custom eval dataset."""
    examples = {row["id"]: row for row in load_jsonl(eval_path)}
    predictions = {row["id"]: row for row in load_jsonl(predictions_path)}
    validator = ToolValidator()

    counters = defaultdict(float)
    group_metrics: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    error_rows = []

    for example_id, example in examples.items():
        expected = example["expected"]
        wrapper = predictions.get(example_id, {})
        prediction = wrapper.get("prediction", wrapper)
        group = example.get("group", "unknown")
        counters["count"] += 1
        group_metrics[group]["count"] += 1

        expected_tool = expected.get("tool")
        predicted_tool = prediction.get("tool")
        tool_correct = expected_tool == predicted_tool
        if tool_correct:
            counters["tool_correct"] += 1
            group_metrics[group]["tool_correct"] += 1

        schema_errors = validator.validate(prediction)
        if not schema_errors:
            counters["schema_valid"] += 1
            group_metrics[group]["schema_valid"] += 1

        expected_arguments = expected.get("arguments", {})
        predicted_arguments = prediction.get("arguments", {})
        if not isinstance(predicted_arguments, dict):
            predicted_arguments = {}
        correct, total = argument_score(expected_arguments, predicted_arguments)
        counters["argument_correct"] += correct
        counters["argument_total"] += total

        exact_arguments = correct == total and set(predicted_arguments) >= set(expected_arguments)
        status_correct = (
            expected_tool is not None
            or predicted_tool is None
            or prediction.get("status") == expected.get("status")
        )
        confirmation_correct = (
            prediction.get("requires_confirmation")
            == expected.get("requires_confirmation")
        )
        end_to_end = (
            tool_correct
            and exact_arguments
            and status_correct
            and confirmation_correct
            and not schema_errors
        )
        if end_to_end:
            counters["end_to_end"] += 1
            group_metrics[group]["end_to_end"] += 1
        else:
            error_rows.append({
                "id": example_id,
                "query": example["query"],
                "expected": expected,
                "prediction": prediction,
                "schema_errors": schema_errors,
            })

    count = counters["count"]
    report = {
        "count": int(count),
        "tool_selection_accuracy": counters["tool_correct"] / count if count else 0,
        "schema_valid_rate": counters["schema_valid"] / count if count else 0,
        "soft_argument_accuracy": (
            counters["argument_correct"] / counters["argument_total"]
            if counters["argument_total"]
            else 1.0
        ),
        "end_to_end_task_success": counters["end_to_end"] / count if count else 0,
        "groups": {
            group: {
                "count": int(values["count"]),
                "tool_selection_accuracy": values["tool_correct"] / values["count"],
                "schema_valid_rate": values["schema_valid"] / values["count"],
                "end_to_end_task_success": values["end_to_end"] / values["count"],
            }
            for group, values in sorted(group_metrics.items())
        },
        "errors": error_rows,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--eval-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = evaluate_custom(args.eval_path, args.predictions)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")

    print(rendered)


if __name__ == "__main__":
    main()