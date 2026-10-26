# Allocation and simulation

## Numerical policy and estimation

[InvestmentPolicy](../../backend/app/domain/policy.py) validates explicit version/identity, timezone-aware cutoff, unique symbols, positive USD capital, minimum-variance objective, uniform asset bounds, cash bounds and review frequency. Aggregate infeasibility is rejected. Hard constraints are never silently relaxed.

[Return calculations](../../backend/app/domain/returns.py) intersect session dates across requested assets, require at least three aligned sessions, and compute simple returns `close[t] / close[t-1] - 1`. Sample covariance uses `ddof=1` over at least two returns. Quantitative statistics are fractions per observed interval, with no annualization or trading-calendar gap correction. Source availability and adjustment conventions remain explicit.

[The optimiser](../../backend/app/domain/optimizer.py) checks covariance symmetry/positive semidefiniteness and uses projected gradient descent on a bounded simplex to minimize `w'Σw`. Cash has zero variance and is set to the largest feasible cash weight under all policy bounds. For N assets, the asset target is `max(1 - max_cash_weight, N * min_asset_weight)`; cash fills the remainder. This is a mathematical baseline convention, not a calibrated risk preference or return forecast. It returns structured success, infeasibility or validation failure with diagnostics.

Solver version `projected_gradient_v2_exact_output` reconciles decimal output within original bounds, distributing only a residual no larger than `1e-9`, derives exact residual cash and recomputes variance on returned weights. Its version enters workflow identity. Strict downstream ledger checks must not be weakened to accommodate numerical output.

## Proposal and paper approval

[PaperService](../../backend/app/application/paper.py) requires a fully successful saved workflow, successful selection/numerical review and approved evidence review. It revalidates policy and allocation before constructing a preview. The proposal SHA256 binds run fingerprint, policy, selection identity, research/fill hashes, allocation and exact execution plan.

Approval requires the exact preview ID and boolean `true`. A changed preview returns `proposal_changed`; a different proposal on an already approved run returns `approval_conflict`. Repeating approval for the same ID returns the original receipt and timestamp. Receipt and journal persist together atomically under the run lock. Reload never approves anything.

## Exact opening book

[domain/paper.py](../../backend/app/domain/paper.py) uses rational `Fraction` arithmetic independently of models. One funding entry followed by fractional buys must reconcile exactly:

`cash + position cost + opening fees = funding`

Post-fee equity must satisfy unchanged asset/cash bounds. Display rounding never changes stored quantities or balances. Fills must follow the decision date; there is no exchange-calendar validation. Fill sources are separate from research inputs, and current approval time differs from historical fill time.

The UI fixture uses invented February 3, 2025 closes after the January 31 research cutoff, explicit zero opening fees and zero slippage. The comparison harness uses 10 bps opening fees. Taxes are excluded. Splits/dividends are unsupported and reject; one isolated opening book exists per run, with no rebalancing, withdrawals, liquidation or brokerage operation.

## Manual valuation and immutable replay

[domain/valuation.py](../../backend/app/domain/valuation.py) replays the approved journal, then computes market value, equity, P/L and return relative to original funding from unchanged shares/cash. Opening fees are included; no liquidation fee is invented.

Prices must cover every held symbol once, use USD/unadjusted conventions, be available by the explicit valuation cutoff, be no earlier than the fill session and satisfy the declared calendar-day freshness. The fixture adapter supplies two invented February 4/5 frames with a one-day limit and source hashes. Corporate actions and invalid/stale/incomplete prices fail explicitly.

[MonitoringService](../../backend/app/application/monitoring.py) requires approval and stores inputs/result/recording time atomically by run/date. Updating an already saved date returns the original snapshot, without refetching prices. Reads verify checksum, proposal identity and recalculated arithmetic. Missing current valuation fixtures leave saved history readable. No research/model call or approval/journal mutation occurs.

These mechanics establish exact synthetic simulation and reproducibility. They do not establish realistic fills, total returns, financial suitability or investment performance. Evaluation conventions belong to [evaluation and evidence](08-evaluation-and-evidence.md).
