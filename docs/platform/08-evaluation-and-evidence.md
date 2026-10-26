# Evaluation and evidence

## Evaluation contracts

Research accuracy, candidate selection, numerical allocation and execution are separate evaluation subjects. Comparable experiments declare universe/candidates, dates, evidence access, hard bounds, execution timing, costs and missing-data behavior. Numerical facts come from code and archived inputs, not generated prose.

[evaluation/basic.py](../../backend/app/evaluation/basic.py) implements a single hold-period comparison with a constraint-compatible equal-weight baseline. It validates matching decision/policy cutoffs, later execution/valuation and price availability. The named `next_session_close` convention rejects same-day execution but does not implement an exchange calendar. It reports gross return, normalized costs and net return; it is not a rolling backtest.

[comparison.py](../../backend/app/evaluation/comparison.py) compares equal weight, numerical-only, one combined researcher per company and separate fundamental/news researchers. Both research designs share eligibility, optimiser, numerical review and a critic. Combined research keeps separate citation allowlists, a complete 16,000-character input cap and 1,536 output tokens versus two 768-token calls. The product workflow is unchanged by this experiment.

The fixed [comparison plan](../../fixtures/comparison_plan.json) freezes all decisions before loading development/holdout prices: January 31, 2025 cutoff, February 3 fills, February 5 development valuation, February 14 synthetic holdout. Common opening fees are 10 bps with zero slippage; dividends/actions are unsupported and taxes/liquidation costs excluded. Failed research/prices produce unavailable outcomes rather than partial rankings. No tuning is performed.

Archives embed byte-preserved source text/hashes, plan, reports, citations, selection, identities, limits, usage, allocations and exact books/results. Decision hashes exclude local timings. Archive-only replay verifies identities and recomputes results without models or current fixtures. Hashes detect corruption, not malicious reauthoring.

## Recorded proof register

These are historical observations, not tests rerun by reading this page. The latest task's evidence lives in its FEAT and handoff.

| Record | Demonstrated scope | Limits |
| --- | --- | --- |
| M0/M2, September 2026 | SEC facts for five configured issuers; 10 Alpaca IEX bars; two MSFT documents; one schema response and one manually checked fundamental report | Narrow access proofs; no current account entitlement, complete company/news corpus or point-in-time market dataset |
| [M5.1 audit](../../evidence/m5_1_fixture_audit.json) | Five/twenty synthetic workflows, approval and two valuations; recorded coverage/hashes/timing | Single local timing samples include checkpoint I/O; invented shared evidence and three price sessions |
| [M5.2 comparison](../../evidence/m5_2_comparison.md) and [archive](../../evidence/m5_2_comparison.json) | Eight profile/variant combinations and both splits; all candidates retained; researcher portfolios match numerical-only | No incremental selection benefit or strategy winner; holdout tests code isolation only |
| [M5.3 original](../../evidence/m5_3_verification.json) | Fresh extracted cached setup, 168 Python tests, React build, eight replays, both Chromium flows | September 30 Windows environment; historical frontend snapshot |
| [M5.3 refresh](../../evidence/m5_3_refresh_verification.json) | October 1 current-interface extraction, same suite/build/replay and five/twenty browser flows | Existing `main.jsx` formatting failure; no fresh visual audit or cache-free setup |
| UI.1 visual audit | Checkout record `evidence/frontend_redesign_audit.md`: 34 relevant tests, both Chromium flows and eight widths from 320 to 1920px | Historical September 30 check; other browsers, screen-reader devices, axe and Lighthouse not verified |
| October 17 Git-upload checkpoint | 168 offline Python tests and React build recorded as passing | No fresh browser/formatter check; no automatic synchronization |

The original proof details and hashes remain in the repository history snapshot. Their preservation is documented in the documentation map; active contracts do not rely on reconstructing that chronology.

The comparison records combined/separate calls of 6/11 for five companies and 21/41 for twenty, with equal output reservations of 8,448/31,488. Actual inference tokens/cost for those scripted runs are unknown; external calls and provider spend are zero. Local timings are not fair model-latency benchmarks.

## Limits on conclusions

Schema validity, eligible citation IDs and critic agreement do not prove factual support, complete evidence or suitability. Publication cutoffs do not certify exact dissemination time or remove LLM pretraining leakage. Current universe membership can introduce survivorship bias. Synthetic few-session prices cannot establish reliable risk estimates or market generalization.

No independent financial/model-quality evaluation, calibrated selection thresholds, annualized return/Sharpe ranking, statistical significance, real total-return backtest or multi-agent advantage is established. Research inspired by external papers remains historical motivation, not experimental evidence for this implementation.

## Distribution contract

[demo_bundle.py](../../backend/app/demo_bundle.py) creates a local allowlisted ZIP with sorted entries, fixed timestamps and SHA256/byte inventory. It includes source, locks, synthetic inputs, recorded proof artifacts and explicitly listed documentation. It excludes environment files, raw live caches, runtime books, dependencies, compiled assets and screenshots. Source paths must stay within the root and cannot be symlinks. Archive verification checks path policy, bounded inventory/size and payload hashes.

New documentation is included in newly built bundles; original schema-v1 bundles remain verifiable without requiring documents introduced later. The checked-in October 1 bundle manifest remains historical. A new local packaging check is not a fresh browser or financial proof. Build and recovery procedures belong to [the runbook](../runbooks/local-demo.md).
