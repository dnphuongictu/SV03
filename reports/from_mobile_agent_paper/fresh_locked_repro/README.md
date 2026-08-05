# VIntentAgent — Reproducibility Package (ICTA 2026)

This repository contains the **fresh locked evaluation** used as the headline
generalization result in the paper submission.

## Headline Result (N = 126, v8, Hybrid K=5, α=0.7)

| Metric | Value |
|--------|-------|
| Tool Selection Accuracy | 0.746 |
| Schema Valid Rate | 0.921 |
| Soft Argument Accuracy | 0.744 |
| **End-to-End (E2E)** | **0.563** |
| Wilson 95% CI | [0.476, 0.647] |
| Confirmation Accuracy | 0.944 |
| Null Status Accuracy | 0.367 |

## Repository Structure

```
├── data/
│   ├── vi_droidcall_fresh_test_locked_20260626.jsonl   # 126 test queries
│   └── vi_droidcall_fresh_test_locked_20260626_ledger.csv
├── results/
│   ├── v8_hybrid_k5_predictions.jsonl   # model predictions (126/126)
│   ├── main_report.json                 # canonical metrics
│   ├── fresh_analysis.json              # per-tool breakdown
│   ├── fresh_analysis_tables.md         # paper-ready tables
│   ├── fresh_errors.csv                 # error breakdown
│   └── final_config.json                # frozen run configuration
├── notebooks/
│   └── vidroidcall_fresh_locked_eval_kaggle_v3.ipynb  # GPU eval notebook
├── kaggle_input/
│   └── kaggle_fresh_locked_eval_input_20260626.zip    # Kaggle input bundle
├── scripts/
│   ├── evaluate.py                      # local evaluation script
│   ├── evaluate_ft.py                   # full LoRA evaluation
│   ├── analyze_fresh_results.py
│   ├── create_fresh_locked_testset.py
│   ├── import_kaggle_fresh_results.py
│   └── safety_policy_tests.py
└── MANIFEST.json                        # locked SHA-256 hashes
```

## Reproducing the Result

### Option A — Kaggle (GPU recommended)

1. Upload `kaggle_input/kaggle_fresh_locked_eval_input_20260626.zip` as a Kaggle dataset.
2. Open `notebooks/vidroidcall_fresh_locked_eval_kaggle_v3.ipynb` in Kaggle.
3. Run all cells. Expected output: `v8_hybrid_k5_predictions.jsonl` + `main_report.json`.

### Option B — Local

```bash
# Install dependencies
pip install transformers peft torch sentence-transformers rank_bm25

# Run evaluation (adapter must be downloaded separately)
python scripts/evaluate.py \
  results/v8_hybrid_k5_predictions.jsonl \
  --eval-path data/vi_droidcall_fresh_test_locked_20260626.jsonl \
  --output results/main_report.json
```

### Verify Integrity

SHA-256 hashes for all locked artifacts are in `MANIFEST.json`.

Key hashes:
- Test set: `051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4`
- Predictions: `A60FD6F891ECBB6D2C5A0176B9376F01B0DEAE664297784F3F095624548664DC`
- Main report: `8A6792C115E36C162A4688BAA5411993ACBA66204B2F34AF4BC2211DE222123F`

## Leakage / Audit

- Train/test exact overlap: **0**
- SequenceMatcher ≥ 0.90: **0**
- Char-3 Jaccard ≥ 0.70: **0**
- Safety policy tests: **12/12 passed**
- Unit tests: **15/15 passed** (`pytest prototype/tests`)
