"""Generate paper-ready analysis tables for fresh locked predictions."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import ROOT, load_jsonl
from evaluate import argument_score, evaluate, values_match
from validate import ToolValidator


LOCK_DATE = "20260626"
EVAL_PATH = ROOT / "data" / "eval" / f"vi_droidcall_fresh_test_locked_{LOCK_DATE}.jsonl"
RESULT_DIR = ROOT / "results" / f"fresh_test_locked_{LOCK_DATE}"
PRED_PATH = RESULT_DIR / "v8_hybrid_k5_predictions.jsonl"
OUT_JSON = RESULT_DIR / "fresh_analysis.json"
OUT_MD = RESULT_DIR / "fresh_analysis_tables.md"
OUT_ERRORS = RESULT_DIR / "fresh_errors.csv"


def prediction_map(path: Path) -> dict[str, dict[str, Any]]:
    rows = load_jsonl(path)
    return {row["id"]: row.get("prediction", row) for row in rows}


def classify_error(expected: dict[str, Any], prediction: dict[str, Any], schema_errors: list[str], exact_args: bool, status_correct: bool, confirmation_correct: bool) -> str:
    if expected.get("tool") != prediction.get("tool"):
        if expected.get("tool") is None:
            return "unsafe_or_unwanted_tool_for_null_request"
        if prediction.get("tool") is None:
            return "null_instead_of_tool"
        return "wrong_tool"
    if schema_errors:
        return "schema_invalid"
    if not exact_args:
        return "argument_mismatch"
    if not status_correct:
        return "null_status_mismatch"
    if not confirmation_correct:
        return "confirmation_mismatch"
    return "unknown_e2e_failure"


def pct(value: float) -> str:
    return f"{value:.3f}"


def render_table(title: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return f"## {title}\n\nNo rows.\n"
    lines = [f"## {title}", "", "| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    lines.append("")
    return "\n".join(lines)


def analyze(pred_path: Path) -> dict[str, Any]:
    examples = load_jsonl(EVAL_PATH)
    preds = prediction_map(pred_path)
    validator = ToolValidator()

    if len(preds) != len(examples):
        missing = sorted({row["id"] for row in examples} - set(preds))
        raise SystemExit(
            f"Prediction file is incomplete: predictions={len(preds)}, eval={len(examples)}, missing={len(missing)}. "
            "Import a complete Kaggle run first."
        )

    report = evaluate(eval_path=EVAL_PATH, predictions_path=pred_path)
    buckets: dict[str, Counter] = defaultdict(Counter)
    errors = []
    confusion = Counter()
    error_types = Counter()
    field_stats = Counter()

    def add(bucket: Counter, key: str, value: int | float = 1) -> None:
        bucket[key] += value

    for ex in examples:
        pred = preds[ex["id"]]
        exp = ex["expected"]
        expected_tool = exp.get("tool")
        predicted_tool = pred.get("tool")
        tool_key = expected_tool or f"NULL:{exp.get('status')}"
        group_key = ex.get("group", "unknown")
        schema_errors = validator.validate(pred)
        predicted_args = pred.get("arguments", {})
        if not isinstance(predicted_args, dict):
            predicted_args = {}

        correct_args, total_args = argument_score(exp.get("arguments", {}), predicted_args)
        exact_args = (
            correct_args == total_args
            and set(predicted_args.keys()) == set(exp.get("arguments", {}).keys())
        )
        status_correct = True if expected_tool is not None else (
            predicted_tool is None and pred.get("status") == exp.get("status")
        )
        confirmation_correct = pred.get("requires_confirmation") == exp.get("requires_confirmation")
        tool_correct = expected_tool == predicted_tool
        e2e = tool_correct and exact_args and status_correct and confirmation_correct and not schema_errors

        for bucket_name in [f"tool::{tool_key}", f"group::{group_key}"]:
            bucket = buckets[bucket_name]
            add(bucket, "count")
            add(bucket, "tool_correct", int(tool_correct))
            add(bucket, "schema_valid", int(not schema_errors))
            add(bucket, "argument_exact", int(exact_args))
            add(bucket, "confirmation_correct", int(confirmation_correct))
            add(bucket, "status_correct", int(status_correct))
            add(bucket, "end_to_end", int(e2e))

        confusion[(str(expected_tool), str(predicted_tool))] += 1
        field_stats["argument_fields_total"] += total_args
        field_stats["argument_fields_correct"] += correct_args
        field_stats["required_examples"] += int(expected_tool is not None)
        field_stats["null_examples"] += int(expected_tool is None)
        field_stats["null_status_correct"] += int(expected_tool is None and status_correct)
        field_stats["confirmation_correct"] += int(confirmation_correct)
        field_stats["confirmation_total"] += 1

        for name, expected_value in exp.get("arguments", {}).items():
            field_stats[f"field::{name}::total"] += 1
            field_stats[f"field::{name}::correct"] += int(
                name in predicted_args and values_match(name, expected_value, predicted_args[name])
            )

        if not e2e:
            error_type = classify_error(exp, pred, schema_errors, exact_args, status_correct, confirmation_correct)
            error_types[error_type] += 1
            errors.append(
                {
                    "id": ex["id"],
                    "group": group_key,
                    "expected_tool": expected_tool or "",
                    "predicted_tool": predicted_tool or "",
                    "error_type": error_type,
                    "query": ex["query"],
                    "expected": json.dumps(exp, ensure_ascii=False, sort_keys=True),
                    "prediction": json.dumps(pred, ensure_ascii=False, sort_keys=True),
                    "schema_errors": "; ".join(schema_errors),
                }
            )

    def summarize_bucket(name: str, bucket: Counter) -> dict[str, Any]:
        n = bucket["count"]
        return {
            "name": name,
            "count": int(n),
            "tool_acc": bucket["tool_correct"] / n if n else 0.0,
            "schema_valid": bucket["schema_valid"] / n if n else 0.0,
            "arg_exact": bucket["argument_exact"] / n if n else 0.0,
            "confirmation_acc": bucket["confirmation_correct"] / n if n else 0.0,
            "status_acc": bucket["status_correct"] / n if n else 0.0,
            "e2e": bucket["end_to_end"] / n if n else 0.0,
        }

    per_tool = [
        summarize_bucket(name.removeprefix("tool::"), bucket)
        for name, bucket in buckets.items()
        if name.startswith("tool::")
    ]
    per_group = [
        summarize_bucket(name.removeprefix("group::"), bucket)
        for name, bucket in buckets.items()
        if name.startswith("group::")
    ]
    per_tool.sort(key=lambda row: (row["name"].startswith("NULL:"), row["name"]))
    per_group.sort(key=lambda row: row["name"])

    field_rows = []
    for key, total in sorted(field_stats.items()):
        if not key.startswith("field::") or not key.endswith("::total"):
            continue
        field = key.split("::")[1]
        correct = field_stats[f"field::{field}::correct"]
        field_rows.append({"field": field, "count": int(total), "accuracy": correct / total if total else 0.0})

    analysis = {
        "report": {
            "count": report["count"],
            "tool_selection_accuracy": report["tool_selection_accuracy"],
            "schema_valid_rate": report["schema_valid_rate"],
            "soft_argument_accuracy": report["soft_argument_accuracy"],
            "end_to_end_task_success": report["end_to_end_task_success"],
            "end_to_end_ci_95": report["end_to_end_ci_95"],
        },
        "field_level": {
            "argument_field_accuracy": (
                field_stats["argument_fields_correct"] / field_stats["argument_fields_total"]
                if field_stats["argument_fields_total"]
                else 1.0
            ),
            "confirmation_accuracy": field_stats["confirmation_correct"] / field_stats["confirmation_total"],
            "null_status_accuracy": (
                field_stats["null_status_correct"] / field_stats["null_examples"]
                if field_stats["null_examples"]
                else 1.0
            ),
            "fields": field_rows,
        },
        "per_tool": per_tool,
        "per_group": per_group,
        "error_types": dict(error_types),
        "confusion": [
            {"expected": exp, "predicted": pred, "count": count}
            for (exp, pred), count in sorted(confusion.items(), key=lambda item: (-item[1], item[0]))
        ],
        "errors": errors,
    }
    return analysis


def write_outputs(analysis: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    tool_rows = [
        {
            "name": row["name"],
            "N": row["count"],
            "ToolAcc": pct(row["tool_acc"]),
            "Schema": pct(row["schema_valid"]),
            "ArgExact": pct(row["arg_exact"]),
            "Confirm": pct(row["confirmation_acc"]),
            "E2E": pct(row["e2e"]),
        }
        for row in analysis["per_tool"]
    ]
    group_rows = [
        {
            "name": row["name"],
            "N": row["count"],
            "ToolAcc": pct(row["tool_acc"]),
            "Schema": pct(row["schema_valid"]),
            "ArgExact": pct(row["arg_exact"]),
            "Confirm": pct(row["confirmation_acc"]),
            "E2E": pct(row["e2e"]),
        }
        for row in analysis["per_group"]
    ]
    field_rows = [
        {"field": row["field"], "N": row["count"], "Accuracy": pct(row["accuracy"])}
        for row in analysis["field_level"]["fields"]
    ]
    error_rows = [
        {"error_type": key, "count": value}
        for key, value in sorted(analysis["error_types"].items(), key=lambda item: (-item[1], item[0]))
    ]

    md = []
    r = analysis["report"]
    f = analysis["field_level"]
    md.append("# Fresh Locked Analysis\n")
    md.append(
        "\n".join(
            [
                f"- N: {r['count']}",
                f"- ToolAcc: {pct(r['tool_selection_accuracy'])}",
                f"- SchemaValid: {pct(r['schema_valid_rate'])}",
                f"- SoftArgAcc: {pct(r['soft_argument_accuracy'])}",
                f"- E2E: {pct(r['end_to_end_task_success'])} {r['end_to_end_ci_95']}",
                f"- Argument field accuracy: {pct(f['argument_field_accuracy'])}",
                f"- Confirmation accuracy: {pct(f['confirmation_accuracy'])}",
                f"- Null status accuracy: {pct(f['null_status_accuracy'])}",
            ]
        )
    )
    md.append("")
    md.append(render_table("Per Group", group_rows, ["name", "N", "ToolAcc", "Schema", "ArgExact", "Confirm", "E2E"]))
    md.append(render_table("Per Tool", tool_rows, ["name", "N", "ToolAcc", "Schema", "ArgExact", "Confirm", "E2E"]))
    md.append(render_table("Fields", field_rows, ["field", "N", "Accuracy"]))
    md.append(render_table("Error Types", error_rows, ["error_type", "count"]))
    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    with OUT_ERRORS.open("w", encoding="utf-8", newline="") as handle:
        fields = ["id", "group", "expected_tool", "predicted_tool", "error_type", "query", "expected", "prediction", "schema_errors"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(analysis["errors"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", type=Path, default=PRED_PATH)
    args = parser.parse_args()

    analysis = analyze(args.predictions)
    write_outputs(analysis)
    print(json.dumps(analysis["report"], ensure_ascii=False, indent=2))
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"Wrote {OUT_ERRORS}")


if __name__ == "__main__":
    main()
