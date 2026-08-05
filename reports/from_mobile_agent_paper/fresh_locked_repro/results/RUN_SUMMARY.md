# Fresh locked eval summary

- Eval split: `vi_droidcall_fresh_test_locked_20260626.jsonl`
- Eval SHA-256: `051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4`
- Model: v8 adapter + `Qwen/Qwen2.5-1.5B-Instruct`
- Retriever: hybrid K=5, alpha=0.7
- Prompt: SYSTEM_PROMPT + ROBUST_SUFFIX
- Predictions: `v8_hybrid_k5_predictions.jsonl`
- Report: `main_report.json`

## Main metrics

- N: 126
- ToolAcc: 0.7460
- SchemaValid: 0.9206
- SoftArgAcc: 0.7438
- ConfirmationAcc: 0.9444
- Negative/clarification Acc: 0.4000
- E2E: 0.5635 [0.476, 0.647]
