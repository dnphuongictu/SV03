# Fresh locked baseline results

Date imported: 2026-06-27

Eval set: `vi_droidcall_fresh_test_locked_20260626.jsonl`  
N: 126  
Eval SHA-256:
`051C811625F0D22925EA60868BDCE03A67B291E34976636306DB9BF8F13387B4`

## Validated results

| Configuration | ToolAcc | SchemaValid | SoftArgAcc | E2E | Wilson 95% CI |
| --- | ---: | ---: | ---: | ---: | --- |
| Zero-shot, hybrid K=5, alpha=0.7 | 0.6111 | 0.6746 | 0.6116 | 0.3175 (40/126) | [0.243, 0.403] |
| v8 LoRA, hybrid K=5, alpha=0.7 | 0.7460 | 0.9206 | 0.7438 | 0.5635 (71/126) | [0.476, 0.647] |
| v8 LoRA, BM25 K=5 | 0.7698 | 0.9286 | 0.6860 | 0.6270 (79/126) | [0.540, 0.706] |

## Paired comparisons

- Fine-tuning effect at fixed hybrid retrieval:
  `0.5635 - 0.3175 = +0.2460` E2E (+24.6 percentage points).
  Discordant pairs: hybrid-v8 only 43, zero-shot only 12.
  Two-sided exact McNemar/binomial p = `0.0000331`.
- Retriever comparison at fixed v8 adapter:
  `0.6270 - 0.5635 = +0.0635` E2E in favor of BM25 (+6.35 percentage points).
  Discordant pairs: BM25 only 16, hybrid only 8.
  Two-sided exact McNemar/binomial p = `0.1516`; this difference is not
  statistically significant at 0.05.

The fresh split therefore provides strong paired evidence for the LoRA
fine-tuning contribution. It does not support claiming that hybrid retrieval
outperforms BM25 on this split; the observed point estimate favors BM25, with
overlapping uncertainty and a non-significant paired test.

## Artifact validation

Both experiment folders contain:

- `predictions.jsonl`
- `main_report.json`
- `run_manifest.json`

Validation completed:

- exactly 126 unique prediction IDs per experiment;
- no missing or extra eval IDs;
- protocol ID:
  `fresh-baselines-v8-k5-frozen-20260627-r1`;
- prediction and report hashes match each run manifest;
- local canonical evaluator recomputation exactly matches both saved reports;
- frozen eval, tool-schema, adapter, and retrieval-reference hashes match.

Prediction hashes:

- zero-shot hybrid:
  `6A27F4062EBF9E51C3612BD996A1E83C8A81362DA613E377F88BE8A6AB4509E8`
- v8 BM25:
  `074B3A5A02F6A28783F23A98E6BA20C5E788EE15FA6E2831460E5EB15DE55B0D`

