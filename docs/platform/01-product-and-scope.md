# Product and scope

## Purpose and terms

Agent of Odds is a student project for inspectable company research and constrained paper portfolio simulation. It connects cited findings to explicit selection rules and mathematical allocation. Additional agents are an experiment, not an assumed source of better returns.

An **investment universe** is the configured set of companies eligible for a run. An **investment policy** supplies capital, objective and hard portfolio bounds. A **selection policy** supplies explicit eligibility gates over research and numerical results. A **proposal** is a reviewed allocation; **paper approval** is a separate human action that opens a synthetic book. A **valuation** marks that book using dated prices without changing holdings. **Replay** reads archived inputs/results and is labelled with their original dates.

## Implemented scope

The application is a local, single-user React workspace with Python application services. It supports configurable five-company and twenty-company fixture profiles and selected subsets. The original development universe is MSFT/JPM/JNJ/XOM/WMT, with a research cutoff of `2025-01-31T23:59:59Z`. Company labels and sectors are engineering examples, not recommendations or a reconstructed historical index.

The complete UI flow is synthetic: invented prices/evidence and scripted research/critic responses. Separate provider probes and one grounded live research sample have historical proof records, described in [evaluation and evidence](08-evaluation-and-evidence.md). The UI has no live-provider switch.

The user journey is:

1. Supply explicit policy and selection values; optionally load labelled demo values.
2. Start a run, inspect progress and use explicit pause/continue/retry controls.
3. Inspect cited fundamental/news findings, numerical observations, eligibility reasons and review outcomes.
4. View allocation only after complete workflow success.
5. Inspect a proposal preview and explicitly consent to one paper opening book.
6. Request a dated price-only valuation or read a saved valuation. Reload is read-only.

USD, long-only minimum variance, uniform per-asset bounds and explicit cash bounds are the implemented numerical scope. A qualitative risk label does not resolve to settings automatically. There is no saved actual user investment policy; test values are not validated product defaults. `review_frequency` records policy intent and does not create a scheduler.

## Boundaries

M0–M5.3 and UI.1 are complete at their recorded proof scopes. This means demonstrated mechanics, not production readiness or verified investment quality. Manual valuation and immutable replay are implemented; live/automatic monitoring, research refresh, rebalancing, withdrawals and a complete rolling backtest are not.

The system does not provide authentication, tenants, brokerage orders, public hosting, multi-currency portfolios, leverage or tax/dividend/corporate-action accounting. Unsupported corporate actions fail explicitly. Fees and timing conventions are visible in [allocation and simulation](05-allocation-and-simulation.md).

Zero additional spend is the default. Spending or publication requires the authorization described in [contributor instructions](../../AGENTS.md). Proposed larger-universe screening, alternative objectives and infrastructure are [deferred options](../deferred/README.md), not current delivery promises.
