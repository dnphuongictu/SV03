"""Run a manually adjudicated, evidence-backed Android execution pilot.

The script does not press destructive buttons. The operator enters each locked
query in VIntentApp, observes the prediction/confirmation UI, launches only the
safe compose/picker activity, and answers a fixed rubric. ADB records device
metadata, screenshots, and the foreground activity after every step.

Usage from prototype/:
    python -X utf8 src/run_execution_pilot.py --validate-only
    python -X utf8 src/run_execution_pilot.py
    python -X utf8 src/run_execution_pilot.py --resume
    python -X utf8 src/run_execution_pilot.py --summarize
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from validate import ToolValidator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS = ROOT / "data" / "ondevice" / "execution_pilot_v1.json"
DEFAULT_OUTPUT = ROOT / "results" / "execution_pilot_v1_20260627"
APP_PACKAGE = "com.vintent.app"
MAIN_ACTIVITY = "com.vintent.app/.MainActivity"
MODEL_PATH = (
    "/sdcard/Android/data/com.vintent.app/files/"
    "vidroidcall_v21_q4km.gguf"
)
EXPECTED_PROTOCOL_ID = "vintent-execution-pilot-v1-20260627"


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def validate_protocol(protocol: dict[str, Any], tasks_path: Path) -> list[str]:
    errors: list[str] = []
    if protocol.get("protocol_id") != EXPECTED_PROTOCOL_ID:
        errors.append(
            f"protocol_id must be {EXPECTED_PROTOCOL_ID!r}, "
            f"got {protocol.get('protocol_id')!r}"
        )
    if protocol.get("status") != "locked_before_pilot_execution":
        errors.append("protocol status must be locked_before_pilot_execution")
    tasks = protocol.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        return errors + ["tasks must be a non-empty list"]

    ids = [task.get("id") for task in tasks]
    if len(set(ids)) != len(ids) or any(not task_id for task_id in ids):
        errors.append("task IDs must be present and unique")
    queries = [task.get("query") for task in tasks]
    if len(set(queries)) != len(queries) or any(not query for query in queries):
        errors.append("task queries must be present and unique")

    validator = ToolValidator(ROOT / "data" / "tools" / "android_tools.json")
    forbidden_tools = {
        "ACTION_SET_ALARM",
        "ACTION_SET_TIMER",
    }
    for task in tasks:
        task_id = task.get("id", "<missing>")
        expected = task.get("expected")
        if not isinstance(expected, dict):
            errors.append(f"{task_id}: expected must be an object")
            continue
        schema_errors = validator.validate(expected)
        errors.extend(f"{task_id}: {error}" for error in schema_errors)
        if expected.get("tool") in forbidden_tools:
            errors.append(f"{task_id}: side-effecting tool is forbidden in pilot")
        for field in ["target", "success_criteria", "forbidden_action"]:
            if not task.get(field):
                errors.append(f"{task_id}: missing {field}")

    if not tasks_path.is_file():
        errors.append(f"task file not found: {tasks_path}")
    return errors


def run_adb(
    device: str | None,
    *args: str,
    timeout: int = 30,
    binary: bool = False,
) -> str | bytes:
    cmd = ["adb"]
    if device:
        cmd.extend(["-s", device])
    cmd.extend(args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        timeout=timeout,
        text=not binary,
        encoding=None if binary else "utf-8",
        errors=None if binary else "replace",
    )
    if result.returncode != 0:
        stderr = (
            result.stderr.decode("utf-8", errors="replace")
            if binary
            else result.stderr
        )
        raise RuntimeError(f"ADB failed ({' '.join(cmd)}): {stderr.strip()}")
    if binary:
        return result.stdout
    return (result.stdout + result.stderr).strip()


def connected_devices() -> list[str]:
    output = str(run_adb(None, "devices", "-l"))
    devices = []
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def select_device(requested: str | None) -> str:
    devices = connected_devices()
    if requested:
        if requested not in devices:
            raise SystemExit(
                f"Device {requested!r} is not connected. Connected: {devices}"
            )
        return requested
    if len(devices) != 1:
        raise SystemExit(
            f"Expected exactly one connected Android device, got {devices}. "
            "Pass --device SERIAL."
        )
    return devices[0]


def shell_prop(device: str, name: str) -> str:
    return str(run_adb(device, "shell", "getprop", name)).strip()


def collect_environment(device: str) -> dict[str, Any]:
    package_dump = str(
        run_adb(device, "shell", "dumpsys", "package", APP_PACKAGE, timeout=30)
    )
    version_name = re.search(r"versionName=([^\s]+)", package_dump)
    version_code = re.search(r"versionCode=(\d+)", package_dump)
    model_stat = str(
        run_adb(
            device,
            "shell",
            f"stat -c '%s %Y' {MODEL_PATH} 2>/dev/null || echo MISSING",
        )
    ).strip()
    return {
        "adb_serial": device,
        "manufacturer": shell_prop(device, "ro.product.manufacturer"),
        "model": shell_prop(device, "ro.product.model"),
        "device": shell_prop(device, "ro.product.device"),
        "android_version": shell_prop(device, "ro.build.version.release"),
        "sdk": shell_prop(device, "ro.build.version.sdk"),
        "build_fingerprint": shell_prop(device, "ro.build.fingerprint"),
        "app_package": APP_PACKAGE,
        "app_version_name": version_name.group(1) if version_name else None,
        "app_version_code": int(version_code.group(1)) if version_code else None,
        "model_path": MODEL_PATH,
        "model_stat_size_mtime": model_stat,
        "retriever_top_k": 2,
    }


def launch_app(device: str) -> None:
    run_adb(device, "shell", "input", "keyevent", "KEYCODE_WAKEUP")
    run_adb(device, "shell", "wm", "dismiss-keyguard")
    run_adb(device, "shell", "am", "start", "-n", MAIN_ACTIVITY)
    time.sleep(2)


def prepare_v21_model(device: str, timeout: int = 300) -> dict[str, Any]:
    """Load v2.1 and set top-K=2 through the app's existing benchmark hook."""
    run_id = int(time.time()) % 1_000_000
    run_adb(device, "logcat", "-c")
    run_adb(
        device,
        "shell",
        "am",
        "start",
        "-n",
        MAIN_ACTIVITY,
        "--ei",
        "run_id",
        str(run_id),
        "--ei",
        "query_id",
        "25",
        "--ez",
        "warmup",
        "true",
        "--es",
        "model_path",
        MODEL_PATH,
        "--ei",
        "top_k",
        "2",
    )
    deadline = time.time() + timeout
    log = ""
    marker = f"BENCH_RAM run={run_id}"
    while time.time() < deadline:
        time.sleep(2)
        log = str(
            run_adb(
                device,
                "logcat",
                "-d",
                "-s",
                "VINTENT_BENCH:I",
                timeout=30,
            )
        )
        if marker in log:
            break
        if f"BENCH_ERROR run={run_id}" in log:
            break
    else:
        raise TimeoutError("Timed out while loading/warming the v2.1 model")

    result_line = next(
        (line for line in log.splitlines() if f"BENCH_RESULT run={run_id}" in line),
        "",
    )
    error_line = next(
        (line for line in log.splitlines() if f"BENCH_ERROR run={run_id}" in line),
        "",
    )
    if error_line or not result_line:
        raise RuntimeError(
            f"Model preparation failed: {error_line or 'missing BENCH_RESULT'}"
        )
    return {
        "run_id": run_id,
        "result_line": result_line.strip(),
        "prepared_at": datetime.now().isoformat(timespec="seconds"),
    }


def foreground_activity(device: str) -> str | None:
    output = str(
        run_adb(
            device,
            "shell",
            "dumpsys",
            "activity",
            "activities",
            timeout=30,
        )
    )
    patterns = [
        r"mResumedActivity:.*? ([\w.]+/[\w.$]+)",
        r"topResumedActivity=.*? ([\w.]+/[\w.$]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output)
        if match:
            return match.group(1)
    return None


def capture_screenshot(device: str, path: Path) -> None:
    data = run_adb(device, "exec-out", "screencap", "-p", binary=True)
    if not isinstance(data, bytes) or not data.startswith(b"\x89PNG"):
        raise RuntimeError("ADB screencap did not return a PNG")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def ask_choice(prompt: str, choices: set[str]) -> str:
    choices_display = "/".join(sorted(choices))
    while True:
        value = input(f"{prompt} [{choices_display}]: ").strip().lower()
        if value in choices:
            return value
        print(f"Please enter one of: {choices_display}")


def ask_bool(prompt: str, *, allow_na: bool = False) -> bool | None:
    choices = {"y", "n"}
    if allow_na:
        choices.add("na")
    answer = ask_choice(prompt, choices)
    if answer == "na":
        return None
    return answer == "y"


def evaluate_task(task: dict[str, Any], record: dict[str, Any]) -> bool:
    expected = task["expected"]
    supported = expected.get("tool") is not None
    if supported:
        required = [
            record.get("tool_correct"),
            record.get("arguments_correct"),
            record.get("confirmation_correct"),
            record.get("launch_success"),
            record.get("semantic_success"),
        ]
    else:
        required = [
            record.get("tool_correct"),
            record.get("status_correct"),
            record.get("execute_disabled"),
            record.get("no_external_launch"),
        ]
    return all(value is True for value in required)


def run_task(
    *,
    device: str,
    task: dict[str, Any],
    evidence_dir: Path,
) -> dict[str, Any]:
    expected = task["expected"]
    supported = expected.get("tool") is not None
    print("\n" + "=" * 78)
    print(f"{task['id']}  |  {task['group']}")
    print(f"QUERY : {task['query']}")
    print(
        "EXPECT:",
        json.dumps(expected, ensure_ascii=False, separators=(",", ":")),
    )
    print(f"TARGET: {task['target']}")
    print(f"PASS  : {task['success_criteria']}")
    print(f"SAFETY: {task['forbidden_action']}")
    print("-" * 78)
    print("1. Return to VIntentApp and ensure the On-device switch is ON.")
    print("2. Enter the query exactly as shown, then tap Send.")
    input("Press Enter here when the prediction result is visible... ")

    before_path = evidence_dir / f"{task['id']}_prediction.png"
    capture_screenshot(device, before_path)
    prediction_activity = foreground_activity(device)

    predicted_tool = input(
        "Predicted tool shown by the app (enter 'null' if none): "
    ).strip()
    predicted_status = None
    if predicted_tool.lower() == "null":
        predicted_tool = None
        predicted_status = input(
            "Predicted status (clarification/unsupported/rejected/other): "
        ).strip()

    record: dict[str, Any] = {
        "id": task["id"],
        "group": task["group"],
        "query": task["query"],
        "expected": expected,
        "predicted_tool_observed": predicted_tool,
        "predicted_status_observed": predicted_status,
        "prediction_screenshot": str(before_path),
        "prediction_foreground_activity": prediction_activity,
        "adjudicated_at": datetime.now().isoformat(timespec="seconds"),
    }
    record["tool_correct"] = predicted_tool == expected.get("tool")

    if supported:
        record["arguments_correct"] = ask_bool(
            "Are all required arguments and visible values correct?"
        )
        if not record["tool_correct"]:
            print(
                "The tool is wrong. Do not execute an unrelated action. "
                "This task will fail safely without opening another app."
            )
            record["confirmation_correct"] = False
            record["launch_success"] = False
            record["semantic_success"] = False
        else:
            expects_confirmation = bool(expected.get("requires_confirmation"))
            if expects_confirmation:
                print("Tap Execute once. A confirmation dialog must appear.")
                input("Press Enter when the confirmation dialog is visible... ")
                confirm_path = evidence_dir / f"{task['id']}_confirmation.png"
                capture_screenshot(device, confirm_path)
                record["confirmation_screenshot"] = str(confirm_path)
                record["confirmation_correct"] = ask_bool(
                    "Did the correct confirmation dialog appear before launch?"
                )
                if record["confirmation_correct"]:
                    print(
                        "Tap the positive confirmation button to open the target."
                    )
                else:
                    print(
                        "Cancel the unexpected dialog. Do not continue execution; "
                        "this task will fail safely."
                    )
            else:
                record["confirmation_correct"] = ask_bool(
                    "Is execution available without an unnecessary confirmation?"
                )
                if record["confirmation_correct"]:
                    print("Tap Execute to open the target activity.")
                else:
                    print(
                        "Do not execute from an incorrect UI state; "
                        "this task will fail safely."
                    )

            if record["confirmation_correct"]:
                input(
                    "Press Enter when the target activity is visible "
                    "(do not Call/Send/Save/Create/Capture)... "
                )
                after_path = evidence_dir / f"{task['id']}_target.png"
                capture_screenshot(device, after_path)
                record["target_screenshot"] = str(after_path)
                record["target_foreground_activity"] = foreground_activity(device)
                record["launch_success"] = ask_bool(
                    "Did an appropriate target activity open without an error?"
                )
                record["semantic_success"] = ask_bool(
                    "Does the target satisfy this criterion: "
                    f"{task['success_criteria']}"
                )
            else:
                record["launch_success"] = False
                record["semantic_success"] = False

        print("Press Back on the phone until VIntentApp is visible again.")
        input("Press Enter when you are back in VIntentApp... ")
    else:
        record["status_correct"] = predicted_status == expected.get("status")
        record["execute_disabled"] = ask_bool(
            "Is the Execute button disabled/unavailable?"
        )
        record["no_external_launch"] = ask_bool(
            "Did the app avoid launching any external activity?"
        )

    record["notes"] = input("Optional adjudication note: ").strip()
    record["full_execution_success"] = evaluate_task(task, record)
    print(
        "RESULT:",
        "PASS" if record["full_execution_success"] else "FAIL",
    )
    return record


def wilson(successes: int, total: int, z: float = 1.96) -> list[float]:
    if total == 0:
        return [0.0, 0.0]
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    margin = (
        z
        * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total)
        / denominator
    )
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def summarize(protocol: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    task_by_id = {task["id"]: task for task in protocol["tasks"]}
    completed = [record for record in records if record["id"] in task_by_id]
    passed = sum(bool(record.get("full_execution_success")) for record in completed)
    supported = [
        record
        for record in completed
        if task_by_id[record["id"]]["expected"].get("tool") is not None
    ]
    negative = [
        record
        for record in completed
        if task_by_id[record["id"]]["expected"].get("tool") is None
    ]
    prediction_correct = sum(
        bool(record.get("tool_correct"))
        and (
            bool(record.get("arguments_correct"))
            if task_by_id[record["id"]]["expected"].get("tool") is not None
            else bool(record.get("status_correct"))
        )
        for record in completed
    )
    launch_success = sum(bool(record.get("launch_success")) for record in supported)
    semantic_success = sum(
        bool(record.get("semantic_success")) for record in supported
    )
    safety_success = sum(
        bool(record.get("execute_disabled"))
        and bool(record.get("no_external_launch"))
        and bool(record.get("tool_correct"))
        and bool(record.get("status_correct"))
        for record in negative
    )

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in completed:
        groups[record["group"]].append(record)
    per_group = {}
    for group, rows in sorted(groups.items()):
        ok = sum(bool(row.get("full_execution_success")) for row in rows)
        per_group[group] = {
            "n": len(rows),
            "successes": ok,
            "execution_accuracy": ok / len(rows),
        }

    return {
        "planned_tasks": len(protocol["tasks"]),
        "completed_tasks": len(completed),
        "complete": len(completed) == len(protocol["tasks"]),
        "full_execution_successes": passed,
        "execution_accuracy": passed / len(completed) if completed else 0.0,
        "execution_accuracy_wilson_95": wilson(passed, len(completed)),
        "prediction_successes": prediction_correct,
        "prediction_accuracy": (
            prediction_correct / len(completed) if completed else 0.0
        ),
        "supported_tasks": len(supported),
        "activity_launch_successes": launch_success,
        "activity_launch_rate": (
            launch_success / len(supported) if supported else 0.0
        ),
        "semantic_successes": semantic_success,
        "semantic_success_rate": (
            semantic_success / len(supported) if supported else 0.0
        ),
        "negative_tasks": len(negative),
        "negative_safety_successes": safety_success,
        "negative_safety_rate": (
            safety_success / len(negative) if negative else 0.0
        ),
        "per_group": per_group,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    ci = summary["execution_accuracy_wilson_95"]
    lines = [
        "# Android execution pilot",
        "",
        f"- Protocol: `{report['protocol_id']}`",
        f"- Protocol SHA-256: `{report['protocol_sha256']}`",
        f"- Device: `{report['environment'].get('manufacturer')} "
        f"{report['environment'].get('model')}`",
        f"- Android: `{report['environment'].get('android_version')}`",
        f"- Model: `{report['environment'].get('model_path')}`",
        f"- Completed: `{summary['completed_tasks']}/{summary['planned_tasks']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        (
            f"| Full ExecutionAcc | "
            f"{summary['execution_accuracy']:.3f} "
            f"({summary['full_execution_successes']}/"
            f"{summary['completed_tasks']}) |"
        ),
        (
            f"| Wilson 95% CI | "
            f"[{ci[0]:.3f}, {ci[1]:.3f}] |"
        ),
        (
            f"| Prediction accuracy | "
            f"{summary['prediction_accuracy']:.3f} |"
        ),
        (
            f"| Target activity launch rate | "
            f"{summary['activity_launch_rate']:.3f} |"
        ),
        (
            f"| Semantic target success rate | "
            f"{summary['semantic_success_rate']:.3f} |"
        ),
        (
            f"| Negative/safety success rate | "
            f"{summary['negative_safety_rate']:.3f} |"
        ),
        "",
        "## Per-task adjudication",
        "",
        "| ID | Group | Tool | Full success | Notes |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for record in report["records"]:
        expected_tool = record["expected"].get("tool") or (
            "NULL:" + str(record["expected"].get("status"))
        )
        notes = str(record.get("notes", "")).replace("|", "\\|")
        lines.append(
            f"| {record['id']} | {record['group']} | {expected_tool} | "
            f"{'PASS' if record.get('full_execution_success') else 'FAIL'} | "
            f"{notes} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation guard",
            "",
            (
                "This is a single-device, manually adjudicated pilot. It "
                "supports feasibility of end-to-end Android Intent execution "
                "but is not a population-level user study."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def save_state(
    *,
    output_dir: Path,
    protocol: dict[str, Any],
    protocol_hash: str,
    environment: dict[str, Any],
    model_preparation: dict[str, Any] | None,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    report = {
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_hash,
        "started_or_updated_at": datetime.now().isoformat(timespec="seconds"),
        "environment": environment,
        "model_preparation": model_preparation,
        "summary": summarize(protocol, records),
        "records": records,
    }
    write_json(output_dir / "pilot_report.json", report)
    (output_dir / "RUN_SUMMARY.md").write_text(
        render_markdown(report),
        encoding="utf-8",
    )
    return report


def main() -> None:
    configure_console()
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--task-id", default=None)
    parser.add_argument(
        "--skip-model-prepare",
        action="store_true",
        help="Skip the v2.1/top-K=2 warmup only if it was done in this app session.",
    )
    args = parser.parse_args()

    tasks_path = args.tasks.resolve()
    protocol = load_json(tasks_path)
    protocol_hash = sha256_file(tasks_path)
    errors = validate_protocol(protocol, tasks_path)
    if errors:
        raise SystemExit(
            "Protocol validation failed:\n- " + "\n- ".join(errors)
        )
    print(f"Protocol OK: {protocol['protocol_id']}")
    print(f"Tasks      : {len(protocol['tasks'])}")
    print(f"SHA-256   : {protocol_hash}")
    if args.validate_only:
        return

    output_dir = args.output_dir.resolve()
    report_path = output_dir / "pilot_report.json"
    if args.summarize:
        if not report_path.is_file():
            raise SystemExit(f"No pilot report found: {report_path}")
        previous = load_json(report_path)
        previous["summary"] = summarize(protocol, previous.get("records", []))
        write_json(report_path, previous)
        (output_dir / "RUN_SUMMARY.md").write_text(
            render_markdown(previous),
            encoding="utf-8",
        )
        print(json.dumps(previous["summary"], ensure_ascii=False, indent=2))
        return

    if report_path.exists() and not args.resume:
        raise SystemExit(
            f"{report_path} already exists. Use --resume to continue safely."
        )

    device = select_device(args.device)
    environment = collect_environment(device)
    print(
        f"Device      : {environment['manufacturer']} "
        f"{environment['model']} (Android {environment['android_version']})"
    )
    print(f"Model file  : {environment['model_stat_size_mtime']}")
    if environment["model_stat_size_mtime"] == "MISSING":
        raise SystemExit(f"Required model is missing on device: {MODEL_PATH}")

    previous = load_json(report_path) if report_path.exists() else {}
    if previous and previous.get("protocol_sha256") != protocol_hash:
        raise SystemExit(
            "Cannot resume: task protocol hash differs from the existing report."
        )
    records = list(previous.get("records", []))
    completed_ids = {record["id"] for record in records}

    launch_app(device)
    model_preparation = previous.get("model_preparation")
    if not args.skip_model_prepare:
        print("Preparing v2.1 Q4_K_M with BM25 top-K=2 (one warmup query)...")
        model_preparation = prepare_v21_model(device)
        print("Model preparation OK.")

    tasks = protocol["tasks"]
    if args.task_id:
        tasks = [task for task in tasks if task["id"] == args.task_id]
        if not tasks:
            raise SystemExit(f"Unknown task ID: {args.task_id}")

    print("\nSAFETY RULE: never press Call, Send, Save, Create, or Capture.")
    print("The script saves after every adjudicated task and supports --resume.")

    for task in tasks:
        if task["id"] in completed_ids:
            print(f"SKIP completed: {task['id']}")
            continue
        record = run_task(
            device=device,
            task=task,
            evidence_dir=output_dir / "evidence",
        )
        records.append(record)
        save_state(
            output_dir=output_dir,
            protocol=protocol,
            protocol_hash=protocol_hash,
            environment=environment,
            model_preparation=model_preparation,
            records=records,
        )
        print(f"Saved progress: {len(records)}/{len(protocol['tasks'])}")

    final_report = save_state(
        output_dir=output_dir,
        protocol=protocol,
        protocol_hash=protocol_hash,
        environment=environment,
        model_preparation=model_preparation,
        records=records,
    )
    print("\n" + json.dumps(final_report["summary"], ensure_ascii=False, indent=2))
    print(f"Report: {output_dir / 'pilot_report.json'}")
    print(f"Paper summary: {output_dir / 'RUN_SUMMARY.md'}")


if __name__ == "__main__":
    main()
