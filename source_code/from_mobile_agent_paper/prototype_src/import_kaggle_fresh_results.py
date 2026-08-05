"""Import Kaggle fresh-test outputs with integrity checks.

Expected Kaggle files:
  - v8_hybrid_k5_predictions.jsonl
  - main_report.json (optional; this script recomputes canonical report locally)
  - RUN_SUMMARY.md (optional)

Example:
  python -X utf8 src/import_kaggle_fresh_results.py --input-dir C:\\Users\\ADMIN\\Downloads\\fresh_test_locked_20260626
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import time
from pathlib import Path
from typing import Any

from common import ROOT, load_jsonl
from evaluate import evaluate


LOCK_DATE = "20260626"
EXPECTED_EVAL_SHA256 = "051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4"
EVAL_PATH = ROOT / "data" / "eval" / f"vi_droidcall_fresh_test_locked_{LOCK_DATE}.jsonl"
RESULT_DIR = ROOT / "results" / f"fresh_test_locked_{LOCK_DATE}"
PRED_NAME = "v8_hybrid_k5_predictions.jsonl"
REPORT_NAME = "main_report.json"
SUMMARY_NAME = "RUN_SUMMARY.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def backup_if_present(path: Path) -> Path | None:
    if not path.exists():
        return None
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = path.with_name(f"{path.stem}.backup_{stamp}{path.suffix}")
    shutil.copy2(path, backup)
    return backup


def locate_file(input_dir: Path, name: str) -> Path | None:
    direct = input_dir / name
    if direct.exists():
        return direct
    matches = sorted(input_dir.rglob(name)) if input_dir.exists() else []
    return matches[0] if matches else None


def validate_predictions(pred_path: Path, allow_partial: bool) -> dict[str, Any]:
    eval_rows = load_jsonl(EVAL_PATH)
    pred_rows = load_jsonl(pred_path)
    eval_ids = [row["id"] for row in eval_rows]
    pred_ids = [row["id"] for row in pred_rows]
    missing = sorted(set(eval_ids) - set(pred_ids))
    extra = sorted(set(pred_ids) - set(eval_ids))
    duplicate = sorted({id_ for id_ in pred_ids if pred_ids.count(id_) > 1})

    complete = not missing and not extra and not duplicate and len(pred_rows) == len(eval_rows)
    if not complete and not allow_partial:
        raise SystemExit(
            "Prediction file is not complete. "
            f"rows={len(pred_rows)}/{len(eval_rows)}, "
            f"missing={len(missing)}, extra={len(extra)}, duplicate={len(duplicate)}. "
            "Use --allow-partial only for debugging, not paper reporting."
        )

    return {
        "eval_count": len(eval_rows),
        "prediction_count": len(pred_rows),
        "complete": complete,
        "missing_ids": missing,
        "extra_ids": extra,
        "duplicate_ids": duplicate,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()

    if sha256(EVAL_PATH) != EXPECTED_EVAL_SHA256:
        raise SystemExit(f"Local eval split hash mismatch: {EVAL_PATH}")

    pred_src = locate_file(args.input_dir, PRED_NAME)
    if pred_src is None:
        raise SystemExit(f"Could not find {PRED_NAME} under {args.input_dir}")

    validation = validate_predictions(pred_src, allow_partial=args.allow_partial)

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    pred_dst = RESULT_DIR / PRED_NAME
    report_dst = RESULT_DIR / REPORT_NAME
    summary_dst = RESULT_DIR / SUMMARY_NAME

    backups = {}
    for dst in [pred_dst, report_dst, summary_dst]:
        backup = backup_if_present(dst)
        if backup:
            backups[dst.name] = str(backup.relative_to(ROOT))

    shutil.copy2(pred_src, pred_dst)

    # Recompute locally so the paper uses the repo evaluator as source of truth.
    report = evaluate(eval_path=EVAL_PATH, predictions_path=pred_dst)
    report_dst.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    kaggle_report_src = locate_file(args.input_dir, REPORT_NAME)
    kaggle_summary_src = locate_file(args.input_dir, SUMMARY_NAME)
    if kaggle_report_src:
        shutil.copy2(kaggle_report_src, RESULT_DIR / "kaggle_main_report.json")
    if kaggle_summary_src:
        shutil.copy2(kaggle_summary_src, summary_dst)

    manifest = {
        "imported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_dir": str(args.input_dir),
        "eval_path": str(EVAL_PATH.relative_to(ROOT)),
        "eval_sha256": sha256(EVAL_PATH),
        "predictions": str(pred_dst.relative_to(ROOT)),
        "predictions_sha256": sha256(pred_dst),
        "local_report": str(report_dst.relative_to(ROOT)),
        "validation": validation,
        "backups": backups,
        "metrics": {
            "count": report["count"],
            "tool_selection_accuracy": report["tool_selection_accuracy"],
            "schema_valid_rate": report["schema_valid_rate"],
            "soft_argument_accuracy": report["soft_argument_accuracy"],
            "end_to_end_task_success": report["end_to_end_task_success"],
            "end_to_end_ci_95": report["end_to_end_ci_95"],
        },
    }
    (RESULT_DIR / "import_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest["metrics"], ensure_ascii=False, indent=2))
    print(f"Imported predictions -> {pred_dst}")
    print(f"Recomputed report -> {report_dst}")
    print(f"Manifest -> {RESULT_DIR / 'import_manifest.json'}")


if __name__ == "__main__":
    main()
