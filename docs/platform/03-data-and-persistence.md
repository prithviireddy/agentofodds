# Data and persistence

## Product entities

All entities below are local application data. There is one trusted local operator, with no account, tenant or row-level authorization model. The HTTP surface exposes only the projections and actions in [the interface contract](06-interface.md); filesystem access is a separate trusted boundary.

| Entity | Owner and identity | Lifecycle and relationships |
| --- | --- | --- |
| Company/universe | Universe configuration; unique symbol, explicit SEC CIK in live-proof configuration | Configured input to a run; subsets are validated. Current ticker mappings cannot silently replace issuer identity. No company-management API exists. |
| Investment policy | Domain policy validator; policy ID/version and full values in run identity | Explicit inputs are validated before persistence; a new policy/configuration requires a new run. It governs selection feasibility, allocation and execution bounds. |
| Selection policy | Domain selection contract; ID/version and configured gates | Frozen with the run; determines per-company eligibility, not weights. |
| Price input | Data adapters and numerical contracts; source IDs plus input hash/provider/feed/adjustment/currency/cutoff | Validated observations feed research or evaluation. Research, fill and valuation inputs are separate. |
| Evidence document/chunk | Retrieval index; source ID, SHA256 version, chunk ordinal/text-derived identity | Source changes produce new chunk identities. Reports cite supplied chunks. Index rebuilds are explicit local operations. |
| Research report | Research role; company, role, cutoff, evidence and prompt/model identity within a run | Produced once per stage or retained in revision history; links findings to eligible passages and limitations. |
| Workflow run | Application/workflow; server-generated run ID and canonical input/configuration fingerprint | Created → checkpointed stages → success or structured stop/failure. Compatible completed work is reused; retry is explicit. |
| Selection/allocation/reviews | Workflow stages; run fingerprint and selection input hash | Derived from saved policy/reports/prices; successful reviews allow proposal preview. Diagnostic weights on failures are not actionable. |
| Paper proposal | Paper service; SHA256 of binding and exact execution plan | Read-only preview binds run, policies, selection, allocation and fill source. Changes invalidate an unapproved preview. |
| Approval and opening book | Paper service; unique run ID and proposal ID | Explicit consent atomically stores receipt and journal. One opening book per run; repeat approval returns the same receipt. No update/delete/rebalance API. |
| Valuation snapshot | Monitoring service; `(run_id, valuation_at)` linked to approved proposal | Explicit update archives inputs/result/time. Saved-date replay is immutable and verifies arithmetic against the approved book. |
| Comparison archive | Evaluation harness; source hashes, plan and deterministic decision hashes | Decisions freeze before evaluation prices; read-only replay verifies identities and recalculates archived outcomes. |

There is no tenant, brokerage account, trade order, independent holdings table, autonomous objective selector or scheduled review job. An agent role is a Python function/client contract, not a deployed service or durable user identity. A policy's review-frequency string is not a scheduling entity.

## Physical representation

- `config/*.toml` holds explicit proof configuration. `fixtures/*.json` holds synthetic prices, evidence, fills, valuations and comparison inputs.
- `data/ui_runs/` and `data/ui_runs_20/` isolate profile manifests, checkpoints and `paper_ledger.sqlite3`; these runtime directories are ignored by Git.
- `<run_id>.input.json` stores form values, fixture hash and creation time. Checkpoints use versioned checksummed JSON with atomic replacement, fsync, a fixed dataclass decoder and per-run exclusive lock files.
- SQLite `approvals` stores run ID, unique proposal ID, canonical receipt payload and SHA256. The journal and balances are inside that payload, not separate tables.
- SQLite `valuations` stores run ID, valuation timestamp, canonical snapshot payload and SHA256, with a composite primary key. Approval and valuation writes use explicit transactions under the run lock.
- A live evidence index may be built into ignored `data/evidence_index.json`. The committed comparison JSON embeds its permitted synthetic source text and hashes; live source corpora are not distributed.

Checksums detect accidental corruption, not malicious reauthoring. Saved receipts check binding identity and journal reconciliation; saved valuations also recompute arithmetic. Legacy run creation times remain unknown rather than guessed. Completed older reports/books are not rewritten; incompatible unfinished workflow identities require a new run. The UI also checks the current research fixture hash when reopening its input manifest, so checkpoints are not a universal source-independent replay format.

## Provenance and time

Keep source publication/filing time, availability time, retrieval time, effective financial period, research cutoff, run creation, fill time, approval time, valuation time and recording time distinct. A period ending before a cutoff does not establish publication by that cutoff.

`DailyClose` uses decimal closes, session dates, timezone-aware availability and source IDs. `PriceInput` requires explicit provider/feed/adjustment/currency/hash/retrieval metadata, coverage and `verified` or `not_verified` availability. Numerical eligibility requires verified availability and complete coverage. Fixture availability is invented and labelled, not a certification of real market history.

The SEC normalizer conservatively treats date-only filing records as available the next day at 05:00 UTC. This is a proxy, not exact dissemination evidence; current snapshots can contain later corrections. Alpaca probe bar timestamps do not establish historical availability. Publication filters on narrative evidence neither establish exact intraday availability nor remove model pretraining leakage.

## Storage evolution

**Implemented:** the local SQLite services lazily create `approvals` and `valuations` using `CREATE TABLE IF NOT EXISTS` inside explicit write transactions. There is no migration framework or production database deployment. This existing bootstrap is documented accurately, not represented as a completed migration system.

**Rule for future changes:** any change to persisted schema or meaning must specify compatibility, explicit versioned migration or a documented refusal/rebuild path, backup/recovery and verification before implementation. Do not add implicit destructive upgrades in startup/imports or ad-hoc scripts. If a production database is introduced, its ADR/FEAT must establish explicit migrations, migration-backed tests and a one-shot deployment migration step. This rule does not create that infrastructure or authorize deleting current books.
