# Paper numbers audit - 2026-07-01

Scope: `paper_icta/VIntentAgent_ICTA2026_anonymous_submission_plain.txt`.

## Verdict

No clear unsupported exaggeration was found in the final anonymous paper text. The paper is conservative on the important boundaries: Fresh126 is the headline server result, Device30 is a separate phone ToolAcc/latency benchmark, and Pilot22 is a pre-confirmation/operator-observed pilot rather than a fully automated execution benchmark.

## Checked headline claims

| Paper claim | Source artifact | Status |
| --- | --- | --- |
| Fresh126 v8 hybrid K=5 alpha=0.7: ToolAcc 0.746, SchemaValid 0.921, E2E 0.563, CI [0.476, 0.647] | `prototype/results/fresh_test_locked_20260626/main_report.json` | Matches |
| SoftArgAcc / soft field micro-average 0.744 | `prototype/results/fresh_test_locked_20260626/fresh_analysis.json` | Matches |
| Query-level Arg/Status 77/126 = 0.611 | `prototype/results/fresh_test_locked_20260626/fresh_analysis_tables.md` | Matches |
| Error summary: 15 wrong tool, 1 schema invalid, 15 argument mismatch, 24 unsafe/null errors | `prototype/results/fresh_test_locked_20260626/fresh_analysis_tables.md` | Matches if unsafe/null combines 12 unsafe + 7 status mismatch + 5 null-instead-tool |
| Post-hoc BM25 K=5: 0.627 vs hybrid 0.563, p=0.152, no hybrid advantage on Fresh126 | `prototype/results/FRESH_BASELINE_RESULTS_20260627.md` | Matches |
| Device30 v2.1 BM25 K=2: 0.67 ToolAcc, 16.1 s TTFT, 1204 MB PSS | paper audit/history and on-device handoff files; paper explicitly says corrected after overlap replacement | Matches stated corrected value |
| Pilot22: 13/22 pre-action flow success; final sensitive actions not committed; only 7 runner JSON records | `prototype/results/execution_pilot_v1_20260627/FINAL_22_RUN_UNIFIED_REPORT_20260628.md` and `OPERATOR_OBSERVED_FINAL_SUMMARY.md` | Matches and is properly caveated |

## Risk notes

- The abstract says the system maps requests into executable device actions. The rest of the paper clarifies that final sensitive actions were not committed in Pilot22 and that production readiness is not claimed; keep those caveats.
- Device metrics are for v2.1 BM25 K=2, not the v8 hybrid Fresh126 headline model. The conclusion explicitly states these are complementary but not interchangeable; keep that sentence.
- The phrase "first Vietnamese on-device CPU benchmark" appears as positioning. I did not verify external novelty from the literature during this local audit; treat it as a literature-review claim rather than a project-result claim.
- Fresh126 is manually designed and not proven template-disjoint; the limitations section already says this.

## Recommended final wording discipline

- Prefer "policy-assisted E2E" over plain "E2E" when describing Fresh126.
- Prefer "correct pre-action Intent resolutions" over "successful executions" for Pilot22.
- Prefer "feasibility evidence" or "prototype" over "production-ready assistant".
- Avoid claiming hybrid retrieval wins on Fresh126; the paper correctly says it does not.
