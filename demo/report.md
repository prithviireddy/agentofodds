# Agent of Odds — college demonstration report

Prepared 2026-10-01. This package demonstrates a local, reproducible research-to-paper-simulation workflow. Its end-to-end results are invented fixtures with scripted model responses. It establishes neither research accuracy nor an investment advantage.

## Demonstrated contribution

Explicit policy and a configurable five/twenty-company universe feed dated research, deterministic selection, constrained minimum-variance allocation and numerical/evidence review. Human consent binds one exact synthetic proposal to an atomic, idempotent paper ledger. Price-only valuation preserves shares, cash and the original research; saved valuation replay needs no fresh generation. Python owns numerical finance and exact ledger arithmetic. React presents the local single-user workflow; no brokerage execution or automatic monitoring exists.

Follow [the walkthrough](walkthrough.md) for the approximately seven-minute sequence, [setup](README.md) for commands and [presenter notes](presenter_notes.md) for Q&A. Duration is an outline, not a measured rehearsal.

## Controlled experiment: recorded M5.2 archive

The archive compares equal weight, numerical-only allocation, one combined researcher per company and separate fundamental/news researchers, for both universes. Both researcher designs retain the same critic, selection and optimiser. Decisions freeze at January 31, 2025 before evaluation prices are loaded. Common February 3 execution charges 10 bps opening fees with zero slippage; development ends February 5 and synthetic holdout February 14. This comparison fee differs from the UI opening-book fixture's zero fee.

| Profile | Combined / separate scripted calls | Equal reserved output caps | Observed research effect |
| --- | ---: | ---: | --- |
| Five | 6 / 11 | 8,448 | All candidates retained; allocations and returns match numerical-only |
| Twenty | 21 / 41 | 31,488 | All candidates retained; allocations and returns match numerical-only |

Read [the archived comparison table](../evidence/m5_2_comparison.md) for rounded illustrative returns; [its JSON](../evidence/m5_2_comparison.json) contains source text/hashes, identities, selections, traces and exact arithmetic. Replay recalculates recorded outcomes without current fixtures or model calls. No winner, cost saving, quality improvement or model-latency advantage follows from scripted call counts. The synthetic holdout verifies code isolation, not financial generalisation.

## Historical live-access proofs — separate scope

Earlier records preserved in [requirements history](../docs/history/2026-10-24/requirements.md) and [task history](../docs/history/2026-10-24/tasks.md) describe SEC facts for the five configured companies, one Alpaca request yielding ten IEX daily bars for January 30–31, two Microsoft sources (10-Q and company investor release), a Gemini schema call and one manually checked MSFT fundamental report. The two successful Gemini samples recorded 386 and 3,481 total tokens respectively. Those isolated observations do not measure this demo's inference usage or cost, establish current account/free-quota entitlements, or prove comprehensive five/twenty-company research. These live proofs are historical; this refresh makes no live calls.

Only permitted code, configuration, dependency locks, synthetic inputs, recorded synthetic reports and documentation are distributed. Credentials/environment files, raw live caches, installed dependencies and runtime books are excluded. Historical live proof summaries are documentation, not a redistributed live corpus. BUNDLE_MANIFEST.json records each payload's SHA256 and byte size; hashes detect corruption, not malicious reauthoring.

## Limits to state aloud

- **Usage and cost:** fixtures call no external providers and add no provider spend. Reserved output tokens are caps, not consumption. Actual inference tokens/cost for full workflows remain unknown. Historical local timings include checkpoint/orchestration overhead and are not fair provider benchmarks. Paid fallback remains disabled; dependency installation may require network access and cached packages are not shipped.
- **Evidence:** shared invented passages and scripted judgments cannot prove factual correctness, independent news coverage or critic reliability. Citation validation checks eligible supplied IDs, not truth. Publication cutoffs do not establish dissemination timing or remove model pretraining leakage.
- **Price history:** three synthetic research sessions and short invented evaluation windows are inadequate market history. Historical live IEX bars used adjustment=all and lack established point-in-time availability/corporate-action conventions. No market-calendar validation, realistic fills, dividends, taxes, liquidation costs or rebalancing is implemented; unsupported actions fail explicitly.
- **Financial conclusions:** no forecast calibration, statistical significance, annualised return, Sharpe ranking, suitability, agent advantage or investable strategy is established. Constraints are explicit and never silently relaxed. Paper consent in rehearsal creates test data, not real investor approval or a trade.
- **Reproducibility:** Windows with existing dependency caches is the exercised setup. Cache-free installation, other operating systems, other browsers and a timed human presentation remain unverified. Historical browser proofs and current checks are recorded separately.

## Verification and evidence map

[evidence/m5_3_verification.json](../evidence/m5_3_verification.json) preserves the original September 30 clean-extraction/browser proof. [evidence/m5_3_refresh_verification.json](../evidence/m5_3_refresh_verification.json) records only this refresh's completed commands. [The fixture audit](../evidence/m5_1_fixture_audit.json) records local scaling samples; `evidence/frontend_redesign_audit.md` is a historical checkout record and is not included as a new proof. The refreshed bundle includes current React source, its design reference and optional audit script so the existing formatting command is usable after extraction.

Current refresh: cached locked setup, production build, 168 tests, eight archive outcomes and five/twenty Chromium smoke passed. Optional frontend formatting failed on existing main.jsx; it was preserved. No new visual screenshot audit or timed human presentation is claimed.
