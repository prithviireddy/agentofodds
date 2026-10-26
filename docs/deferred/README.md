# Deferred options

This directory holds unimplemented ideas outside current delivery. Nothing here is a contract, schedule, provider commitment or spending authorization. The current platform is described in [platform/](../platform/README.md).

| Option | Missing design/evidence before delivery |
| --- | --- |
| Broader live research and independent news | Permitted coverage/retention, timestamps, account-specific access, bounded ingestion, sampled factual evaluation and authorized inference scope |
| Meaningful financial/model evaluation | Independent evidence, richer time-aware prices, historical universe membership, predefined splits/baselines, leakage controls and measured inference usage |
| Larger-universe numerical screening | Explicit screening rule, excluded-candidate evaluation and measured incremental resource use |
| Alternative objective such as CVaR | Defined objective/input assumptions, constraints and fixed-objective controls |
| Bounded objective switching | Predefined triggers, candidate objectives, approval rules, frequency bounds and comparative evaluation |
| Automatic monitoring/research/rebalancing | Scheduling/lifecycle/recovery, fresh-data conventions, approval semantics and migration design |
| Corporate actions and realistic execution | Splits/dividends, trading calendars, taxes/fills/slippage and exact journal semantics |
| LangGraph, FastAPI, PostgreSQL, embeddings/vector store, CVXPY | A demonstrated need over the current local state machine/HTTP/SQLite/lexical/NumPy implementation; dependency and compatibility assessment |
| Public hosting, multi-user access or distributed workers | Authentication, authorization, data ownership, concurrency, security, explicit migrations and operating budget |
| External paper-trading provider | Separate adapter, account/idempotency/reconciliation design and explicit authorization |

Real-money brokerage execution remains excluded from version 1, not an implied next milestone. Intraday strategies, broad multi-asset coverage, reinforcement learning and fine-tuning remain outside the approved scope.

To revive an option, scope a FEAT and, when a hard boundary changes, an ADR. Update the owning platform chapter as a labelled Target, then remove the corresponding deferred entry when its scope has an active owner. Do not cite this table as proof that work was approved or implemented. Original research-paper summaries, pricing examples and schedules remain historical only.
