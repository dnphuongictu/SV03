# Project handoff - 2026-07-01

## Final paper artifacts

- Final anonymous submission: `paper_icta/VIntentAgent_ICTA2026_anonymous_submission.pdf`
- Editable final paper: `paper_icta/VIntentAgent_ICTA2026_anonymous_submission.docx`
- Text extracts for audit:
  - `paper_icta/VIntentAgent_ICTA2026_anonymous_submission_plain.txt`
  - `paper_icta/VIntentAgent_ICTA2026_anonymous_submission_pdf.txt`

## Main result artifacts to keep

- Fresh locked headline result:
  - `prototype/results/fresh_test_locked_20260626/main_report.json`
  - `prototype/results/fresh_test_locked_20260626/fresh_analysis.json`
  - `prototype/results/fresh_test_locked_20260626/fresh_analysis_tables.md`
  - `prototype/results/fresh_test_locked_20260626/PAPER_RESULT_SNIPPET.md`
  - `prototype/results/fresh_test_locked_20260626/repro_package_20260626/`
- Fresh locked repro archive:
  - `prototype/results/fresh_test_locked_20260626/vintentagent_fresh_locked_repro_package_20260626.zip`
  - SHA file beside it.
- Fresh baseline comparison:
  - `prototype/results/FRESH_BASELINE_RESULTS_20260627.md`
  - `prototype/results/fresh_v8_bm25_k5/main_report.json`
  - `prototype/results/fresh_zeroshot_hybrid_k5/main_report.json`
- Android execution pilot:
  - `prototype/results/execution_pilot_v1_20260627/FINAL_22_RUN_UNIFIED_REPORT_20260628.md`
  - `prototype/results/execution_pilot_v1_20260627/OPERATOR_OBSERVED_FINAL_SUMMARY.md`
  - `prototype/results/execution_pilot_v1_20260627/pilot_report.json`
  - `prototype/results/execution_pilot_v1_20260627/evidence/`

## Models likely needed later

- Phone/deployment model used in paper: `models/vidroidcall_v21_q4km.gguf`
- Other comparison GGUFs referenced in the project:
  - `models/vidroidcall_v2_q4km.gguf`
  - `models/vidroidcall_q4km.gguf`
  - `models/vidroidcall_v21_q3km.gguf`
- Fresh server adapter used by headline result: `prototype/results/adapter_v8/`

Large regenerable files that are not required for the submitted paper PDF but may be useful for retraining/conversion:

- `models/*_f16.gguf`
- `models/qwen2.5-*-vidroidcall-merged*/model.safetensors`
- older LoRA zip/checkpoint copies under `models/qwen2.5-*-vidroidcall-lora/`

## Final paper numbers

- Fresh126 v8 hybrid K=5 alpha=0.7: ToolAcc 0.746, SchemaValid 0.921, SoftArgAcc 0.744, policy-assisted E2E 0.563, Wilson 95% CI [0.476, 0.647].
- Fresh126 post-hoc BM25 K=5 comparison: E2E 0.627, not statistically established over hybrid (p=0.152).
- Device30 v2.1 BM25 K=2 Q4_K_M: ToolAcc 0.67 (20/30), TTFT 16.1 +/- 3.2 s, RAM PSS 1204 MB, GGUF size 940 MB.
- Pilot22: 13/22 correct pre-action Intent resolutions. Only first 7 records are persisted by the automatic runner; remaining tasks are operator-observed with screenshots/logs.

## Cleanup notes

- Safe to remove Python caches, pytest caches, Word temp lock files, and render/check directories.
- Do not delete the final paper files, Fresh126 result/repro package, execution-pilot evidence, or `vidroidcall_v21_q4km.gguf`.
- For C: drive pressure, the largest safe cleanup candidates found were Gemini history/tmp, npm cache, pip cache, user Temp, `.cache`, and Codex temp/cache/log/session files. Avoid deleting application folders such as `AppData/Local/Programs`, browser profiles, Android SDK, or OneDrive user files unless explicitly reviewed.
