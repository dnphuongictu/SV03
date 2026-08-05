# Fresh locked test run status

Date: 2026-06-26

## Completed

- Created locked split: `data/eval/vi_droidcall_fresh_test_locked_20260626.jsonl`
- Created ledger: `data/eval/vi_droidcall_fresh_test_locked_20260626_ledger.csv`
- Created leakage report: `results/fresh_test_locked_20260626/leakage_report.json`
- Created frozen config: `results/fresh_test_locked_20260626/final_config.json`
- Verified gold labels with canonical evaluator contract.
- Added `--stream-output` to `src/evaluate_ft.py` so long CPU runs can write predictions incrementally.

## Locked hashes

- Test SHA-256: `051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4`
- Ledger SHA-256: `59D9B09257FF97789183F009CC368740DF314CFDA755BF9D3B3B889F16575FC4`

## Leakage audit

- Exact normalized overlaps: `0`
- High SequenceMatcher matches >= 0.90: `0`
- High char-3 Jaccard matches >= 0.70: `0`

## Model evaluation status

An attempted CPU-only run of the frozen v8 configuration was started with `src/evaluate_ft.py`.
It was aborted after a long runtime because the previous evaluator only wrote predictions after the full batch.
No complete prediction file or main report was produced from that aborted run.
The local machine has no CUDA GPU available, so the full v8 fresh evaluation should be run on Kaggle GPU.

Prepared Kaggle artifacts:

- Notebook: `prototype/vidroidcall_fresh_locked_eval_kaggle_v3.ipynb`
- Upload/input bundle: `prototype/kaggle_fresh_locked_eval_input_20260626.zip`

Kaggle run v1 failed because the latest Kaggle image had `torchao==0.10.0` while
newer `peft` expected `torchao>0.16.0`. Notebook v2 removes `torchao` and pins
`peft==0.13.2`, `transformers==4.46.3`, and `sentence-transformers==3.3.1`.
Kaggle run v2 then failed because the adapter was saved by PEFT 0.18.x and
included config keys unknown to PEFT 0.13.2, such as `alora_invocation_tokens`.
Notebook v3 creates a working copy of `adapter_v8` and sanitizes
`adapter_config.json` to the keys supported by the installed `LoraConfig`.

On Kaggle:

1. Create a new notebook with GPU enabled.
2. Upload/add `kaggle_fresh_locked_eval_input_20260626.zip` as a dataset/input.
3. Import or copy `vidroidcall_fresh_locked_eval_kaggle_v3.ipynb`.
4. Enable internet unless Qwen2.5-1.5B-Instruct and multilingual-e5-small are already attached as Kaggle inputs.
5. Run all cells.

Expected Kaggle outputs:

- `/kaggle/working/fresh_test_locked_20260626/v8_hybrid_k5_predictions.jsonl`
- `/kaggle/working/fresh_test_locked_20260626/main_report.json`
- `/kaggle/working/fresh_test_locked_20260626/RUN_SUMMARY.md`

## While waiting for Kaggle

Prepared local post-processing and safety artifacts:

- `src/import_kaggle_fresh_results.py`
  - imports Kaggle outputs, rejects incomplete prediction files by default, recomputes `main_report.json` using the local canonical evaluator, and writes `import_manifest.json`.
- `src/analyze_fresh_results.py`
  - creates `fresh_analysis.json`, `fresh_analysis_tables.md`, and `fresh_errors.csv` after a complete prediction file exists.
- `src/safety_policy_tests.py`
  - writes `results/safety_policy_tests_20260626.json`.

Safety tests passed: `12/12`.

Kaggle v3 completed and was imported locally. The previous partial local
`v8_hybrid_k5_predictions.jsonl` with `67/126` predictions was backed up as
`v8_hybrid_k5_predictions.backup_20260626_162240.jsonl`.

Imported final fresh metrics:

- N: `126`
- ToolAcc: `0.746`
- SchemaValid: `0.921`
- SoftArgAcc: `0.744`
- E2E: `0.563`, Wilson 95% CI `[0.476, 0.647]`
- Confirmation accuracy: `0.944`
- Null status accuracy: `0.367`

Generated analysis artifacts:

- `main_report.json`
- `import_manifest.json`
- `fresh_analysis.json`
- `fresh_analysis_tables.md`
- `fresh_errors.csv`

When Kaggle succeeds and the output folder is downloaded, run:

```powershell
python -X utf8 src\import_kaggle_fresh_results.py `
  --input-dir "C:\path\to\downloaded\fresh_test_locked_20260626"

python -X utf8 src\analyze_fresh_results.py
```

Use the streaming mode for the next full run:

```powershell
$env:HF_HOME='D:\.cache\huggingface'
python -X utf8 src\evaluate_ft.py `
  --adapter results\adapter_v8 `
  --retriever hybrid `
  --top-k 5 `
  --alpha 0.7 `
  --fix-confirmation `
  --robust-prompt `
  --stream-output `
  --eval-path data\eval\vi_droidcall_fresh_test_locked_20260626.jsonl `
  --output results\fresh_test_locked_20260626\v8_hybrid_k5_predictions.jsonl
```

After the prediction file is complete:

```powershell
python -X utf8 src\evaluate.py `
  results\fresh_test_locked_20260626\v8_hybrid_k5_predictions.jsonl `
  --eval-path data\eval\vi_droidcall_fresh_test_locked_20260626.jsonl `
  --output results\fresh_test_locked_20260626\main_report.json
```
