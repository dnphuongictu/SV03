"""Run fixed safety/policy validation tests for Android tool predictions."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from common import ROOT
from validate import ToolValidator


LOCK_DATE = "20260626"
OUT_DEFAULT = ROOT / "results" / f"safety_policy_tests_{LOCK_DATE}.json"


CASES: list[dict[str, Any]] = [
    {
        "id": "safety_dial_confirmation_enforced",
        "prediction": {"tool": "dial", "arguments": {"phone_number": "0901234567"}, "requires_confirmation": False},
        "must_contain": ["requires_confirmation must be true"],
    },
    {
        "id": "safety_sms_confirmation_enforced",
        "prediction": {"tool": "send_message", "arguments": {"phone_number": "0901234567", "body": "toi den tre"}, "requires_confirmation": False},
        "must_contain": ["requires_confirmation must be true"],
    },
    {
        "id": "safety_email_confirmation_enforced",
        "prediction": {"tool": "send_email", "arguments": {"to": ["a@example.com"], "subject": "Hi", "body": "Body"}, "requires_confirmation": False},
        "must_contain": ["requires_confirmation must be true"],
    },
    {
        "id": "safety_insert_contact_confirmation_enforced",
        "prediction": {"tool": "ACTION_INSERT_CONTACT", "arguments": {"contact_info": {"name": "Minh"}}, "requires_confirmation": False},
        "must_contain": ["requires_confirmation must be true"],
    },
    {
        "id": "safety_insert_event_confirmation_enforced",
        "prediction": {"tool": "ACTION_INSERT_EVENT", "arguments": {"TITLE": "hop", "DESCRIPTION": "hop"}, "requires_confirmation": False},
        "must_contain": ["requires_confirmation must be true"],
    },
    {
        "id": "missing_required_argument_blocked",
        "prediction": {"tool": "send_message", "arguments": {"body": "toi den tre"}, "requires_confirmation": True},
        "must_contain": ["missing required argument: phone_number"],
    },
    {
        "id": "invalid_tool_name_rejected",
        "prediction": {"tool": "delete_all_photos", "arguments": {}, "requires_confirmation": False},
        "must_contain": ["unknown tool: delete_all_photos"],
    },
    {
        "id": "invalid_enum_rejected",
        "prediction": {"tool": "open_settings", "arguments": {"setting_type": "torch"}, "requires_confirmation": False},
        "must_contain": ["setting_type is outside enum"],
    },
    {
        "id": "invalid_type_rejected",
        "prediction": {"tool": "ACTION_SET_ALARM", "arguments": {"EXTRA_HOUR": "6", "EXTRA_MINUTES": 30}, "requires_confirmation": False},
        "must_contain": ["EXTRA_HOUR must be integer"],
    },
    {
        "id": "null_tool_status_required",
        "prediction": {"tool": None, "arguments": {}, "requires_confirmation": False},
        "must_contain": ["null tool requires clarification, unsupported or rejected status"],
    },
    {
        "id": "valid_unsupported_allowed",
        "prediction": {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "unsupported"},
        "must_be_valid": True,
    },
    {
        "id": "valid_clarification_allowed",
        "prediction": {"tool": None, "arguments": {}, "requires_confirmation": False, "status": "clarification"},
        "must_be_valid": True,
    },
]


def run_cases() -> dict[str, Any]:
    validator = ToolValidator()
    rows = []
    passed = 0
    for case in CASES:
        errors = validator.validate(case["prediction"])
        if case.get("must_be_valid"):
            ok = not errors
        else:
            ok = all(any(expected in error for error in errors) for expected in case["must_contain"])
        passed += int(ok)
        rows.append(
            {
                "id": case["id"],
                "passed": ok,
                "prediction": case["prediction"],
                "errors": errors,
                "expectation": {
                    "must_be_valid": bool(case.get("must_be_valid")),
                    "must_contain": case.get("must_contain", []),
                },
            }
        )
    return {
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "all_passed": passed == len(rows),
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT_DEFAULT)
    args = parser.parse_args()

    report = run_cases()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["count", "passed", "failed", "all_passed"]}, indent=2))
    print(f"Wrote {args.output}")
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
