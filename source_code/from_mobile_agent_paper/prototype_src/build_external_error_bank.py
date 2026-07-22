"""Build an error bank from the external hybrid_k5 report."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from common import ROOT, load_jsonl


REPORT_PATH = ROOT / "results" / "external" / "hybrid_k5_external_report.json"
EVAL_PATH = ROOT / "data" / "eval" / "vi_droidcall_external_test.jsonl"
CSV_PATH = ROOT / "results" / "external" / "error_bank_hybrid_k5.csv"
SUMMARY_PATH = ROOT / "results" / "external" / "error_summary_hybrid_k5.md"


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def classify_error(per_example: dict[str, Any], schema_errors: list[str]) -> str:
    if not per_example.get("tool_correct", False):
        return "tool_wrong"
    if schema_errors:
        return "schema_fail"
    if not per_example.get("arguments_exact", False):
        return "argument_exact_fail"
    if not per_example.get("status_correct", False):
        return "status_fail"
    if not per_example.get("confirmation_correct", False):
        return "confirmation_fail"
    return "other"


def make_note(error_type: str, expected: dict[str, Any], prediction: dict[str, Any]) -> str:
    expected_tool = expected.get("tool")
    predicted_tool = prediction.get("tool")
    if error_type == "tool_wrong":
        return f"expected {expected_tool}, predicted {predicted_tool}"
    if error_type == "argument_exact_fail":
        expected_args = expected.get("arguments", {})
        predicted_args = prediction.get("arguments", {})
        missing = sorted(set(expected_args) - set(predicted_args))
        extra = sorted(set(predicted_args) - set(expected_args))
        changed = sorted(
            key
            for key in set(expected_args) & set(predicted_args)
            if expected_args[key] != predicted_args[key]
        )
        parts = []
        if missing:
            parts.append(f"missing={missing}")
        if extra:
            parts.append(f"extra={extra}")
        if changed:
            parts.append(f"changed={changed}")
        return "; ".join(parts) or "argument mismatch"
    if error_type == "schema_fail":
        return "schema validation failed"
    if error_type == "status_fail":
        return f"expected status {expected.get('status')}, predicted {prediction.get('status')}"
    if error_type == "confirmation_fail":
        return (
            f"expected confirmation {expected.get('requires_confirmation')}, "
            f"predicted {prediction.get('requires_confirmation')}"
        )
    return "unclassified"


def main() -> None:
    if not REPORT_PATH.exists():
        raise FileNotFoundError(f"Missing report: {REPORT_PATH}")

    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    per_example = {row["id"]: row for row in report["per_example"]}
    eval_by_id = {row["id"]: row for row in load_jsonl(EVAL_PATH)}

    rows = []
    for error in report["errors"]:
        example_metrics = per_example[error["id"]]
        expected = error["expected"]
        prediction = error["prediction"]
        schema_errors = error.get("schema_errors", [])
        error_type = classify_error(example_metrics, schema_errors)
        rows.append(
            {
                "id": error["id"],
                "group": eval_by_id.get(error["id"], {}).get("group", "unknown"),
                "query": error["query"],
                "expected_tool": expected.get("tool") or f"NULL:{expected.get('status')}",
                "predicted_tool": prediction.get("tool") or f"NULL:{prediction.get('status')}",
                "error_type": error_type,
                "expected": _json(expected),
                "prediction": _json(prediction),
                "schema_errors": " | ".join(schema_errors),
                "note": make_note(error_type, expected, prediction),
            }
        )

    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_type = Counter(row["error_type"] for row in rows)
    by_group = Counter(row["group"] for row in rows)
    by_expected = Counter(row["expected_tool"] for row in rows)

    lines = [
        "# External Hybrid K5 Error Summary",
        "",
        f"Source report: `{REPORT_PATH.relative_to(ROOT)}`",
        f"Total errors: `{len(rows)}` / `{report['count']}`",
        "",
        "## Error Types",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in by_type.most_common())
    lines.extend(["", "## Error Groups", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in by_group.most_common())
    lines.extend(["", "## Most Failed Expected Tools/Statuses", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in by_expected.most_common(15))
    lines.extend(
        [
            "",
            "## Priority Fix Areas",
            "",
            "- `message_email`: preserve exact SMS/email body, subject, and recipient fields.",
            "- `alarm_calendar`: parse relative/colloquial time, repeat days, and avoid extra labels.",
            "- `settings_files`: distinguish open/get/create document and ringtone/settings intents.",
            "- `negative_ambiguous`: predict null tool with the correct status.",
            "",
            f"CSV: `{CSV_PATH.relative_to(ROOT)}`",
            "",
        ]
    )
    SUMMARY_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
