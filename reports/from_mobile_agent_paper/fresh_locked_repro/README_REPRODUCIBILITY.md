# VIntentAgent Fresh Locked Reproducibility Package

Date: 2026-06-26

This package freezes the fresh locked evaluation used as the headline
generalization result for the ICTA 2026 paper draft.

## Headline Result

- Model/protocol: v8, Qwen2.5-1.5B + LoRA adapter
- Retriever: hybrid BM25 + dense, K=5, alpha=0.7
- Prompt/decoding: robust prompt, greedy decoding, max_new_tokens=256
- Post-processing: schema-based confirmation override
- Fresh locked split: 126 queries
- ToolAcc: 0.746
- SchemaValid: 0.921
- SoftArgAcc: 0.744
- E2E: 0.563, Wilson 95% CI [0.476, 0.647]
- Confirmation accuracy: 0.944
- Null status accuracy: 0.367

## Locked Hashes

| Artifact | SHA-256 |
| --- | --- |
| data/vi_droidcall_fresh_test_locked_20260626.jsonl | 051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4 |
| data/vi_droidcall_fresh_test_locked_20260626_ledger.csv | 59D9B09257FF97789183F009CC368740DF314CFDA755BF9D3B3B889F16575FC4 |
| results/v8_hybrid_k5_predictions.jsonl | A60FD6F891ECBB6D2C5A0176B9376F01B0DEAE664297784F3F095624548664DC |
| results/main_report.json | 8A6792C115E36C162A4688BAA5411993ACBA66204B2F34AF4BC2211DE222123F |
| results/final_config.json | 5EC2C9306395E35D54E7B960BB27F04A8908B51A64ACC8482FEE40D344A2CF40 |
| notebooks/vidroidcall_fresh_locked_eval_kaggle_v3.ipynb | F903F025851EE31401281F75277318BCE7F432B79C2D10CD9646F5B92051B6B3 |
| kaggle_input/kaggle_fresh_locked_eval_input_20260626.zip | 9C33373DDFB9BBD40FD419591C96F0AC42027B8299C96855E577195E7C6F565A |

## Included Files

- `data/`
  - Fresh locked eval JSONL
  - Fresh locked ledger CSV
- `results/`
  - Frozen config
  - Leakage report
  - Imported predictions
  - Canonical main report
  - Fresh analysis JSON, Markdown tables, and error CSV
  - Run status and Kaggle run summary
- `notebooks/`
  - Kaggle notebook v3 used for the GPU run
- `kaggle_input/`
  - Uploadable Kaggle input bundle with POSIX zip paths
- `scripts/`
  - Dataset creation, import, analysis, safety test, and evaluation scripts

## Re-run on Kaggle

1. Create a Kaggle notebook with GPU enabled.
2. Upload or attach `kaggle_input/kaggle_fresh_locked_eval_input_20260626.zip`.
3. Import or copy `notebooks/vidroidcall_fresh_locked_eval_kaggle_v3.ipynb`.
4. Enable internet unless the base models are already attached as Kaggle inputs.
5. Run all cells.

Expected output files:

- `/kaggle/working/fresh_test_locked_20260626/v8_hybrid_k5_predictions.jsonl`
- `/kaggle/working/fresh_test_locked_20260626/main_report.json`
- `/kaggle/working/fresh_test_locked_20260626/RUN_SUMMARY.md`

## Recompute Local Report After Download

From the repository `prototype/` directory:

```powershell
python -X utf8 src\import_kaggle_fresh_results.py `
  --input-dir "C:\path\to\downloaded\fresh_test_locked_20260626"

python -X utf8 src\analyze_fresh_results.py
```

To recompute the canonical report directly:

```powershell
python -X utf8 src\evaluate.py `
  results\fresh_test_locked_20260626\v8_hybrid_k5_predictions.jsonl `
  --eval-path data\eval\vi_droidcall_fresh_test_locked_20260626.jsonl `
  --output results\fresh_test_locked_20260626\main_report.json
```

## Protocol Notes

- The v8 configuration was selected before fresh-test evaluation because it was
  the strongest prior diagnostic configuration.
- final48 and extTest144 are development/diagnostic evidence after this point,
  not the headline generalization estimate.
- Leakage audit for the fresh locked split found 0 exact normalized overlaps,
  0 SequenceMatcher matches >= 0.90, and 0 char-3 Jaccard matches >= 0.70.
- Safety policy tests passed 12/12.
- Unit tests passed 15/15 with `pytest prototype\tests`.
