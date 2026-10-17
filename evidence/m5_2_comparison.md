# M5.2 synthetic comparison

Fixture mechanics only. These results do not establish agent quality or investment performance.

Plan identity: `51f126f9c34a62c80b04565a84a5f1c82949974d621762df91ecb7c5d8adb917`. No tuning; all decisions frozen before loading evaluation prices.

Common execution: 2025-02-03T21:00:00+00:00; 10 bps opening cost, zero slippage, no dividends/taxes/liquidation cost.
Development valuation: 2025-02-05T22:00:00+00:00. Synthetic holdout valuation: 2025-02-14T22:00:00+00:00. Returns below include opening fees.

| Universe | Variant | Candidates | Calls | Output tokens reserved | Development return | Holdout return | Status |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| five | equal_weight | 5 | 0 | 0 | 0.44% | -0.41% | success |
| five | numerical_only | 5 | 0 | 0 | 0.43% | -0.39% | success |
| five | combined_researcher | 5 | 6 | 8448 | 0.43% | -0.39% | success |
| five | separate_researchers | 5 | 11 | 8448 | 0.43% | -0.39% | success |
| twenty | equal_weight | 20 | 0 | 0 | -0.91% | -0.09% | success |
| twenty | numerical_only | 20 | 0 | 0 | -0.91% | -0.01% | success |
| twenty | combined_researcher | 20 | 21 | 31488 | -0.91% | -0.01% | success |
| twenty | separate_researchers | 20 | 41 | 31488 | -0.91% | -0.01% | success |

Every variant retains the full universe. Research allocations match numerical-only allocation; no incremental selection benefit is established. No winner is inferred.

The combined and separate researchers use the same selection policy, optimiser and one shared critic. Combined is one researcher call per company, not a system without a critic. Equal-weight and numerical-only baselines do not use research selection.

Agent variants retain unknown actual token usage/inference cost. Reserved tokens are limits, not measured consumption. External calls and additional provider spend are zero. Local timings in JSON include unequal orchestration/checkpoint overhead.

JSON archives the plan, source files/hashes, report evidence, selection decisions, numerical allocations, exact opening books, valuations, call traces and deterministic decision identities.

- Scripted fixtures establish mechanics and schema/citation checks, not factual accuracy or an investment advantage.
- Holdout is synthetic and withheld from decision code, not independently sourced market evidence. No statistical significance claim.
- Combined means one researcher call per company plus the same shared critic; separate uses two role calls plus that critic.
- Local timings include different orchestration/checkpoint overhead and are not a fair model latency benchmark.
- No annualised return, Sharpe ratio or ranking is inferred from these short fixture windows.
- No external calls, real approvals, ledger writes, trades or provider spend. Model token usage/cost are unknown.
