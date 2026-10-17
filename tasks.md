# Build Checklist — Agent of Odds

Last updated: 2026-10-01

Status: TODO / IN PROGRESS / BLOCKED / DONE. DONE requires evidence. M0–M5.3 and UI.1 are complete at their recorded proof scopes; the current-interface demo package was refreshed on October 1. Presentation-machine rehearsal remains pending.

| ID | Task | Depends on | Status | Acceptance criteria |
| --- | --- | --- | --- | --- |
| D0 | Portable documentation baseline | — | DONE | Seven Markdown files describe scope, boundaries, state and maintenance; archive contains all seven |
| M0.1 | Inspect/create repository and basic Python setup | User starts implementation | DONE | Actual tree recorded; dependency/environment choices explicit; no secret committed |
| M0.2 | Choose five companies and a sample cutoff | M0.1 | DONE | Named symbols, identities, sectors and selection rationale recorded |
| F0.1 | Synthetic price adapter and cutoff checks | M0.2 | DONE | Labelled prices, explicit missing coverage and validation; 12 passing tests (evidence below) |
| M0.3 | Prove structured financial/price access | M0.2 | DONE | Sample data with units/dates/feed metadata; actual access and missing fields recorded |
| M0.4 | Prove news/document access | M0.2 | DONE | One accessible filing and dated news/release sample; actual entitlement and limitations documented |
| M0.5 | Prove one model call | M0.1 | DONE | Model ID, schema validation, quota and usage recorded; paid billing stays off |
| M1.1 | Implement policy and numerical data contracts | M0.3 | DONE | Explicit constraints, dates, units and missing-data status validated |
| M1.2 | Implement numerical baseline and optimiser | M1.1 | DONE | Known simple cases checked; valid weights; infeasibility is explicit |
| M1.3 | Implement basic evaluation | M1.2 | DONE | Equal-weight comparison, timing and cost assumptions recorded; no future-price access |
| M2.1 | Index small evidence corpus | M0.4 | DONE | Source versions and company/date filters checked; no paid embedding dependency |
| M2.2 | Implement fundamental research role | M2.1, M0.5 | DONE | Source-backed structured report; manually checked sample; missing evidence surfaced |
| M3.1 | Implement news and quantitative roles | M2.2, M1.2 | DONE | Tools compute numbers; dated news interpretation and limitations visible |
| M3.2 | Implement candidate-selection policy | M3.1 | DONE | Explicit rule, exclusions and rationale; no arbitrary LLM allocation percentages |
| M3.3 | Implement bounded orchestration and review | M3.2 | DONE | Retry/critic limits, checkpoints, per-run usage; recover from quota/provider failure |
| M4.1 | Build UI for complete research-to-portfolio flow | M3.3 | DONE | User policy, run status, evidence, allocations, failure outcomes and report view |
| M4.2 | Build paper ledger and approval | M4.1 | DONE | Opening-book fixture scope; exact reconciliation, explicit bound approval and atomic idempotency; evidence below |
| M4.3 | Monitoring and labelled replay | M4.2 | DONE | Manual fixture price-only valuation; immutable replay and original timestamps; evidence below |
| M5.1 | Expand to about 20 companies | M4.3 | DONE | Configurable 20-company fixture profile, coverage audit, measured local runtime and explicit unknown inference usage/cost |
| M5.2 | Compare baseline, single-agent and multi-agent variants | M5.1 | DONE | Controlled offline variants, synthetic holdout isolation, self-contained replay and explicit limits; evidence below |
| M5.3 | Prepare college demonstration | M5.2 | DONE | Fresh extraction, 168 tests, React build, five/twenty browser flows, archive replay and hash-verified evidence bundle |
| UI.1 | Redesign the existing React frontend | M5.3 | DONE | DESIGN.md/Taste/Vercel review; all workspace states, reusable primitives, both profile browser flows and eight-width audit |

## Later experiments

UI.1 is the user's separately requested frontend redesign; the existing M0–M5 milestone scopes are unchanged.

- Larger universe with numerical screening; compare excluded and selected candidates and measure incremental cost.
- Alternative optimisation objective such as CVaR; keep fixed-objective controls.
- Bounded objective switching with predefined triggers and approval rules.
- Optional external paper-trading integration and public hosting.

## Evidence convention

For each completed implementation task append: relevant files, command/check performed, observed result, known limitation, and commit/experiment ID if available. Do not use a checkmark as a substitute for evidence.

## Current blockers and prerequisites

Local repository and uv bootstrap verified; project accounts remain unverified. No deadline supplied. Access tests require the user's locally configured credentials where applicable; never ask them to paste secrets into these documents. Work can begin with fixtures and public sources while account-specific checks wait.

## M1.3 evidence — 2026-09-26

- Files: `backend/app/evaluation/basic.py`, `backend/app/evaluation/__init__.py`, and `backend/tests/test_m1_evaluation.py`.
- Implemented a constraint-compatible equal-weight portfolio, explicit decision/execution/valuation contract, single hold-period gross/net return calculation, one-way transaction cost, and optimized-versus-baseline comparison.
- Future-access safeguards require matching policy/decision cutoffs, next-session execution, later valuation, point-in-time-eligible complete prices, and required bar availability by the evaluation cutoff.
- Verified: `uv run --locked python -m unittest backend.tests.test_m1_evaluation -v` — 6 tests passed. `uv run --locked python -m unittest discover -s backend/tests -q` — 64 tests passed.
- Limits: synthetic inputs only; no live result, rolling backtest, dividends, taxes, trading calendar, corporate actions, partial fills or realistic market-impact model. No commit ID.
- Next: M2.1 small evidence index. M0.5 remains independently blocked by Gemini HTTP 503 service availability.

## M2.1 evidence — 2026-09-26

- Files: `backend/app/retrieval/index.py`, `backend/app/retrieval/__init__.py`, `backend/app/index_probe.py`, and `backend/tests/test_m2_index.py`.
- Implemented deterministic overlapping chunks, source-version hashes, local JSON persistence, bounded TF-IDF cosine retrieval, and company/publication-date filters. No hosted vector database, embedding API or new dependency was added.
- Verified offline: 6 focused tests and 70 total tests pass. Tests cover deterministic version-bound chunk IDs, ranking, filters, save/load, version mismatch and bounded invalid queries.
- Verified live: two existing Microsoft sources produced 313 chunks in ignored `data/evidence_index.json`; a bounded MSFT query before the configured cutoff returned three version-linked hits. SEC source hash `5334bcac5d6bb14324e6f3336539ea06000b8490810146e4ee0539b882951940`; investor-release hash `f4d3b3054fc9eb5c970e055edc98de682de1abc9d1ebd4e684dc36ec9d1c8c94`.
- Limits: lexical baseline, two Microsoft sources only, local rebuilt index, no embedding semantics or relevance benchmark. No commit ID.
- Next: M2.2 is gated by M0.5. Retry the single bounded Gemini proof deliberately; after success, build the fundamental research role over this retriever.

## M2.2 progress — 2026-09-26

- Files: `backend/app/research/fundamental.py`, `backend/app/research/__init__.py`, `backend/app/research_probe.py`, `config/research.toml`, and `backend/tests/test_m2_research.py`; the Gemini adapter now exposes a bounded generic JSON-schema request used by application roles.
- Implemented bounded query retrieval, company/cutoff filters, an 8,000-character prompt budget, untrusted-document framing, at most one injected model call, exact retrieved-chunk citation validation, structured findings/limitations, and a no-model insufficient-evidence path.
- Verified offline: 7 research tests plus one generic Gemini-budget test; 78 total tests pass. The fixture-backed sample confirms a cited claim manually encoded from its supplied passage. Unknown citations, missing company evidence, bad requests and provider failures are rejected or surfaced.
- Live dependency result: one deliberate `backend.app.model_probe` call reached Gemini but returned `failed_validation` because the provider response did not match the existing structured-output envelope. No valid result, usage record or research finding was accepted, and no automatic retry followed.
- M2.2 remains IN PROGRESS. The runnable probe is ready, but completion requires diagnosing M0.5, obtaining one valid live structured report, and manually checking its claims against cited chunks.

## M0.5 and M2.2 completion evidence — 2026-09-26

- Root cause of the invalid Gemini response: `finishReason=MAX_TOKENS`; the 256-token cap included hidden thinking tokens and left only 27 characters of candidate JSON. Safe diagnostics recorded response shape and usage without recording the generated fragment.
- Applied the official Gemini 3 control `thinkingLevel=minimal`; kept temperature 0 and the original 256-token M0 cap. The next deliberate M0.5 call passed schema validation on `gemini-3.6-flash`: 212 prompt, 174 candidate and 386 total tokens. Prompt hash `0e31c3b27e0d7d1360d0d0c0ce65afd52bfa2c4fc9f987f0791ce7a623856147`; response hash `97c17d0c45e2f0704e3bb2b57d08fdbb56e8407cc3b72c84194d5c202c4cc923`.
- The live M2.2 probe searched three bounded MSFT questions and made one model call. It returned three findings with citations to retrieved chunks. Usage: 2,959 prompt, 522 candidate and 3,481 total tokens; prompt hash `27f9634a35c7d76484a9d035ced076c6760b3fd1b29fe3c6f03ceab29ea7346d`; response hash `d1b4116a0ef25b72f2ba6ede219fe51523b48d531286d07a0b2a939abc67c3de`.
- Manual citation check passed: the cited release passages contain the reported $69.6B revenue/12% growth, $24.1B net income/10% growth, and $13B AI annual run rate/175% growth; the cited 10-Q passage contains the expected capital-expenditure increase for cloud offerings and AI infrastructure/training.
- Scope remains two MSFT sources. This validates mechanics and citation support for one sample, not completeness, investment merit or factual accuracy across the five-company universe. Full offline suite: 79 tests pass. M0.5 and M2.2 are DONE; next M3.1.

## M0.1 evidence — 2026-09-20

- Files: `pyproject.toml`, `uv.lock`, `.python-version`, `backend/app/__init__.py`, `backend/app/__main__.py`, `.env.example`, `.gitignore`.
- Verified: `uv lock`, `uv sync --locked`, `uv run --locked python -m backend.app`, `uv run --locked python -m compileall -q backend` all succeeded. Bootstrap reported offline mode and unverified provider access.
- Environment: Windows, uv 0.9.9, Python 3.14.3. No third-party dependencies, financial tests, live calls or performance claims.
- Git initialised; no commit or remote. Ownership differs after runner identity changed; status works with command-local `git -c safe.directory=C:/codeblender/agentic/agentofodds status --short`. No global Git configuration changed.
- Next: M0.2, then M0.3–M0.5 access proofs. Revisit interpreter compatibility when numerical dependencies are introduced.

## M0.2 / F0.1 evidence — 2026-09-20

- `config/universe.toml`: MSFT/Microsoft, JPM/JPMorgan Chase, JNJ/Johnson & Johnson, XOM/Exxon Mobil, WMT/Walmart; project-defined sectors and rationale. Cutoff `2025-01-31T23:59:59Z`. Development sample only; no investment ranking or historical-universe claim.
- `backend/app/config/universe.py`: variable-size, versioned universe with duplicate/name/timestamp validation.
- `backend/app/contracts/market_data.py`, `backend/app/adapters/data/fixture.py`, `fixtures/prices.json`: decimal-string daily closes, availability cutoff, source IDs, metadata/hash, synthetic labelling, missing-symbol reporting and input validation.
- `backend/app/__main__.py`: configurable fixture command with structured JSON outcomes and exit codes 0/1/2.
- Verified: `uv run --locked python -m unittest discover -s backend/tests -v` — 12 tests passed. `uv run --locked python -m backend.app` — success, 10 synthetic records, five symbols, no missing coverage.
- Tests exercise late availability, inclusive cutoff, no eligible history, variable universe size, missing symbols, duplicates, nonfinite/nonpositive values, units, timezone requirements and CLI failure statuses.
- Limits: two synthetic sessions cannot support covariance or performance estimates. No live prices, financial facts, filings/news or model access proved. M0.3–M0.5 stay TODO. No commit ID.

## M0.3/M0.4 progress — 2026-09-21

- Implemented `backend/app/adapters/data/sec.py` and `backend/app/sec_probe.py`: bounded SEC client, ticker/CIK resolver, USD Assets normaliser, recent filing metadata references and explicit error outcomes.
- `backend/tests/test_sec.py` adds 15 offline tests for request limits, failed HTTP/transport/JSON, missing identity, allowlisted destinations, Decimal precision, company mismatch, date-only availability, later restatement exclusion, units and filing reference validation.
- Verified `uv run --locked python -m unittest discover -s backend/tests -v`: 27 tests pass (12 existing + 15 SEC). `uv run --locked python -m backend.app.sec_probe`: expected exit 1, missing_configuration; no live call made.
- Fixed `.gitignore` from `data/` to `/data/`; the former unintentionally hid the source adapter folder.
- SEC_USER_AGENT is absent; a contact identity was requested. No real CIK mapping, Assets value, filing body, price feed, news or model response has been verified. M0.3/M0.4 remain IN PROGRESS, not DONE.
- Next: set local contact configuration, run the SEC probe and inspect/save actual evidence; then fetch a filing body and verify prices/news. Configured live transport, additional historical submission pages and cache persistence remain pending.
## Local configuration update — 2026-09-21

- `backend/app/sec_probe.py` now loads an ignored project-root `.env`, with shell variables taking precedence. Added two tests; full suite: `uv run --locked python -m unittest discover -s backend/tests -v` — 29 passing tests.
- Removed populated values from `.env.example`; it holds placeholders only. Local `.env` is absent, so SEC live access remains unverified. Existing provider credentials that were placed in the example file should be rotated.


## Live SEC evidence — 2026-09-21

- `uv run --locked python -m backend.app.sec_probe` completed 11 read-only public SEC requests at 06:33–06:34 UTC and returned `partial_data`, not failure.
- All configured issuer CIKs produced a cutoff-eligible USD Assets sample. Recent filing metadata: MSFT, JNJ, XOM, WMT. JPM remains partial because `filings.recent` contains no qualifying historical row, while CompanyFacts does.
- Corrected XOM: SEC's ticker table currently lists CIK 0002115436 for `XOM` (ExxonMobil Holdings Corp), but intended Exxon Mobil Corporation CIK 0000034088 was verified separately. `config/universe.toml` now requires each company's SEC CIK; ticker results are audit-only.
- M0.3: IN PROGRESS, pending Alpaca/live price proof. M0.4: IN PROGRESS, pending a dated news/release sample, JPM historical filing metadata and filing-body retrieval. M0.5 remains TODO.
- Full test suite: 29 offline tests passed. `.env.example` contains placeholders only; `.env` is present and ignored. Any credentials that were formerly placed in the example file must be rotated.

## M3.1 evidence — 2026-09-29

- Files: `backend/app/research/news.py`, `backend/app/research/quantitative.py`, `backend/app/domain/statistics.py`, and `backend/tests/test_m3_research.py`.
- News role uses the existing ResearchRequest, evidence index and injected generate_json contract. It filters company, inclusive publication window and release/fixture source types before ranking; deduplicates chunks; bounds retrieval to four queries, prompt to 8,000 characters and generation to one call / 768 output tokens. Reported events and uncertain interpretations are separate fields. Only prompt-visible chunks can be cited. Reports preserve dates, source versions, prompt version/hash, model metadata and explicit limitations.
- Quantitative role accepts PriceInput and an explicit calendar-day freshness threshold. Independent domain code computes aligned simple-return means, sample volatility/covariance (ddof=1) and compounded return. Outputs retain symbol/session ordering, observation count, input provenance/source IDs and calculation version. No model is used. Missing/unverified coverage, stale data and invalid/future inputs yield structured outcomes without numerical findings.
- Verified: `uv run --locked python -m unittest backend.tests.test_m3_research -v` — 9 tests passed. `uv run --locked python -m unittest discover -s backend/tests -q` — 88 tests passed.
- Numerical fixture check: AAA closes 100, 110, 99 produce returns +0.1/-0.1, mean 0, sample variance 0.02 and cumulative return -0.01. BBB closes 100, 105, 110.25 produce mean 0.05 and cumulative return 0.1025. News fixture claim was compared with the supplied passage reporting increased cloud revenue; its demand-growth interpretation is explicitly uncertain.
- Limits: fixture-backed proof only, using inline synthetic data and an injected fake model; no live calls, real performance, broad news coverage or new measured model usage/cost. Publication timestamps do not establish historical availability. No annualisation, trading calendar or corporate-action validation. No new dependency, commit or remote.
- M3.1 is DONE at the requested fixture scope. Next unblocked task: M3.2 candidate-selection policy; selection rules and exclusions must be explicit, separate from allocation.

## M3.2 evidence — 2026-09-29

- Files: `backend/app/domain/selection.py`, `backend/app/application/__init__.py`, `backend/app/application/selection.py`, and `backend/tests/test_m3_selection.py`.
- Explicit versioned SelectionPolicy requires exclusions, fundamental/news assessment allowlists, evidence/price freshness limits in calendar days, minimum return observations, unannualised volatility ceiling and minimum candidate count. No user defaults were inferred.
- Deterministic eligibility service requires both research roles and quantitative success, matching identities/cutoffs, valid cited evidence and numerical fields. All findings must meet the role allowlist and all cited evidence must meet freshness. Returns every passing symbol in investment-universe order, per-company reasons/citations/limitations, policy snapshots and a hash of supplied reports/settings. No ranking, model call or weights.
- Too few candidates returns insufficient_candidates; an eligible subset violating unchanged investment bounds returns infeasible. Both return no actionable candidate set while preserving per-company decisions. Missing/quota/stale/invalid reports exclude affected companies without fallback.
- Verified: `uv run --locked python -m unittest backend.tests.test_m3_selection -v` — 7 passed. `uv run --locked python -m unittest discover -s backend/tests -q` — 95 passed.
- Tests cover deterministic provenance, explicit exclusions, negative assessment filtering, provider failure/missing/stale reports, unknown citations, future evidence/cutoff mismatches, numerical limits/NaN, minimum count, infeasible residual asset bounds and invalid policies.
- Limits: synthetic role/price fixtures only; no actual shortlist or investment benefit established. Schema/citation checks do not prove claims true. Selection thresholds are experiment inputs; comparison against a no-selection baseline remains future evaluation. No new dependencies, live calls, spending or commit.
- Next: M3.3 bounded orchestration and review, checkpoints, usage and provider-failure recovery.

## M3.3 evidence — 2026-09-29

- Files: `backend/app/workflows/__init__.py`, `checkpoint.py`, `runner.py`, `review.py`; `backend/tests/test_m3_workflow.py`; prompt-visible citation correction in `backend/app/research/fundamental.py` (prompt version v2).
- Sequential workflow composes quantitative validation, fundamental/news reports, candidate selection, subset-aligned covariance/allocation, independent numerical review and a bounded evidence critic. No numerical calculation moved into a model. Explicit exclusions skip text research; bad quantitative inputs stop before generation.
- Required WorkflowBudget caps companies, model calls, reserved output tokens, declared retrieval queries, retries per stage (0–1), critic rounds (1–2) and revisions (0–1). Concurrency is one. Calls reserve 768 output tokens and prompts are capped at 8,000 characters. Reservations are durably saved before dispatch and never refunded after ambiguous interruption. Provider failure stops; only explicit retry_failed=True permits a bounded retry with the same run budgets. No automatic retry/backoff loop, credentials rotation or paid fallback.
- Local atomic JSON checkpoints have checksum/schema validation, fixed dataclass decoding and per-run exclusive locks. Resume is bound to exact policy, price/evidence/request/config/model/prompt identity. Successful stages are reused; completed resume makes no calls. Interrupted calls remain charged with unknown usage. Stage history retains earlier reports/review outcomes, including revision history. Unknown token usage is distinct from measured counts; cost remains unknown.
- Critic sees all selected claims and complete cited passages within its prompt budget, with shared passages deduplicated. Oversized/conflicting coverage returns review_incomplete without truncation. Critic output can approve, reject or request one allowlisted research-stage revision. Repeated revision requests or rejected evidence never yield workflow success. Code independently checks symbols, finite weights, sum/cash/asset constraints and variance; objective limitations are explicit.
- Verified: `uv run --locked python -m unittest backend.tests.test_m3_workflow -q` — 21 passed. `uv run --locked python -m unittest discover -s backend/tests -q` — 116 passed.
- Five-company synthetic fixture proof: MSFT/JPM/JNJ/XOM/WMT, 10 fake research calls plus 1 fake critic call, successful selection and reconciled allocation. No actual model calls, costs, news, performance or live workflow reliability were measured. Fake usage fields exist solely to verify aggregation.
- Additional verification covers mid-run and completed resume, explicit quota retry, retry exhaustion, interrupted reservation, every call/query/output budget, changed/corrupt/locked checkpoints, failed disk writes, model mismatch, missing/bad inputs, candidate/covariance ordering, review rejection/revision/overflow, invalid critic targets, unknown usage and omitted fundamental citations.
- Testing caught and fixed loss of timestamp types during checkpoint round trips. Full review initially exceeded the five-company fixture prompt budget because shared evidence was repeated; deduplication retained coverage. The overflow fixture was adjusted to guarantee large cited passages rather than accidentally selecting a short tail chunk.
- Limits: local single-writer state machine, no LangGraph dependency/distributed workers; crash locks require manual verification/removal. Checksum is corruption detection, not authentication. Injected factories/transports remain trusted application code. Provider call deadlines remain adapter-owned. Critic approval is not factual truth or human approval; no trade/paper-ledger action. No new dependency or commit.
- M3 is DONE at fixture/proof scope. Next: M4.1 UI for complete research-to-portfolio flow, using fixtures by default and exposing run/review/usage/failure state.

## M4.1 evidence — 2026-09-29

- Files: `backend/app/application/demo.py`, `backend/app/ui.py`, `fixtures/workflow_demo.json`, `frontend/index.html`, `frontend/style.css`, `frontend/app.js`, `frontend/smoke.cjs`, and `backend/tests/test_m4_ui.py`.
- Added a local responsive research workspace: explicit editable demo policy, selectable fixture universe, exclusions, selection/freshness settings, fixture scenario controls, stage progress/history, pause/continue/explicit retry, saved-run reopening, citation passages/source hashes, company decisions, numerical provenance, reviews, usage and JSON report download.
- Separate production-module fixture service supplies five synthetic companies, three synthetic price sessions and scripted research/critic responses without importing tests or live adapters. Demo values require an explicit Load demo policy action; they are labelled test inputs, not recommended user settings. Fixture universe is file-configured and UI-selectable.
- Allocation is omitted at the API boundary unless the top-level workflow succeeds. Rejected review and insufficient candidates never expose an actionable portfolio. Input manifests and workflow checkpoints are saved under ignored data/ui_runs; reload reads saved state and never dispatches calls by itself. Each explicit advance runs one stage. A browser-driven run loop stops at pause, failure or completion; no scheduler/background maintenance exists.
- Loopback Python HTTP service serves only allowlisted assets and JSON routes. Host/Origin/content-type and bounded request bodies are checked; fixture input schema/policies are validated. Evidence is inserted as text nodes; no raw HTML interpretation. No external font/script/library/CDN, package installation, live key loading or provider call.
- Verified: `uv run --locked python -m unittest backend.tests.test_m4_ui -v` — 6 tests passed; final `uv run --locked python -m unittest discover -s backend/tests -q` — 122 tests passed. Coverage includes five-company completion, persisted reload, missing evidence/rejected review, exclusions, explicit quota retry through eventual completion, invalid inputs/paths, HTTP routes and cross-origin refusal.
- Verified local server: `uv run --locked python -m backend.app.ui` at http://127.0.0.1:8765. Browser verification used `node frontend/smoke.cjs` with PLAYWRIGHT_MODULE pointed to the bundled Playwright installation. Passed success flow, cited-passage inspection, completed reload, review rejection hiding weights, quota recovery, pause/reload/resume, 390px horizontal-overflow check and no page JavaScript errors. Desktop/mobile screenshots were inspected; artifacts remain ignored in data/ui-verification.
- Browser verification initially timed out on quota recovery against an old running server; after restarting the task-owned server with the corrected single-interruption fixture, it passed. In-app browser automation failed during kernel initialization; bundled headless Chromium provided the recorded visual/UI checks.
- Limits: dependency-free HTML/CSS/JavaScript plus local Python HTTP server, not the earlier proposed React/FastAPI stack; local fixture demonstration only, no production/multi-user server, live research, calibrated policy, human approval, ledger or execution. Fixed fixture cutoff and small synthetic corpus are visible. Scripted critic/usage are not measured model accuracy/cost. No new dependencies or commit.
- M4.1 DONE at local fixture scope. Next: M4.2 paper ledger and explicit approval, idempotency, cash/holdings reconciliation and declared fill/corporate-action/dividend conventions.

## M4.1 React correction evidence — 2026-09-30

- User required React. Added frontend/src/main.jsx component/hook implementation, Vite React configuration, package.json and package-lock.json; removed legacy frontend/app.js. Updated index entry and built-asset serving in backend/app/ui.py.
- Fixed the partial migration's stale initial-run and pause state. Preserved success-only allocations, evidence text, saved reload, failure/explicit retry behavior and limits/usage display. React/Vite is now the required frontend stack.
- Verified clean `npm ci` and `npm run build` in frontend. `uv run --locked python -m unittest discover -s backend/tests -q`: 122 passed. Static route tests use isolated temporary assets, checking bundled assets, path traversal/source refusal and missing-build 503.
- Existing browser smoke passed against production http://127.0.0.1:8765 and development http://127.0.0.1:5173 (UI_BASE_URL override). Covered new run, citations, reload, rejected review, quota recovery, pause/reload/resume, 390px overflow and no page errors. Desktop React screenshot inspected. The smoke wait was made tolerant of React's async first render.
- npm packages: React/React DOM 19.3.0, Vite 8.3.1, React plugin 6.1.1, locked formatter. Python dependencies unchanged. No live providers or financial results. M4.1 remains complete; M4.2 remains next.

## M4.2 evidence — 2026-09-30

- Added `backend/app/domain/paper.py`: exact rational funding, fractional buys, explicit fees, journal reconciliation, dated fills and unchanged post-fee policy constraints. No model dependency.
- Added `backend/app/application/paper.py`, wired through demo/UI: read-only preview, SHA256-bound explicit approval, atomic SQLite receipt/journal per run, repeat-request idempotency, corruption detection and run locking. Changed policy/fills invalidate unapproved previews; reviewed-success runs only. Approval makes no research calls.
- Separate `fixtures/paper_fills.json`: invented February 3 closes following January 31 cutoff, zero fees/slippage. Exact fractions are stored; display rounding does not affect balances. Current approval time and historical fill time are distinct. Splits/dividends reject; taxes excluded. One isolated opening book per run; rebalancing/withdrawals unsupported.
- React `frontend/src/PaperLedger.jsx`, `paper.css` and main integration show holdings, cash, fees, reconciliation, conventions and identity. Checkbox plus explicit button creates the receipt; reload is read-only; failed runs have no ledger controls.
- `uv run --locked python -m unittest backend.tests.test_m4_paper -q`: 11 passed. Covers fee arithmetic, timing/price/action failures, strict bounds, corrupt/duplicate/overdrawn entries, consent, changed policy/fills, unreviewed/rejected runs, idempotent reload, unchanged workflow usage, transaction rollback/retry and HTTP contracts. Fixed SQLite handle cleanup on Windows.
- Full offline suite: 133 passed. React production build passed. Extended `frontend/smoke.cjs` verifies consent-gated approval, durable receipt/reload and previous workflow recovery checks. Browser test approvals are synthetic fixtures, not actual user investment approvals. Final browser results recorded in handoff.
- M4.2 DONE at opening-ledger scope. Next M4.3: price-only monitoring and labelled replay. No live calls, added dependencies, spending, real trades or commit.

## M4.3 evidence — 2026-09-30

- Added `domain/valuation.py`: exact mark-to-market equity and P/L from approved journal quantities and unchanged cash. Return since funding includes opening fees; no liquidation fee is invented. Rejects pre-fill valuation, missing/duplicate coverage, future/unavailable/stale prices, invalid provenance, incompatible currency/adjustment and unsupported corporate actions.
- Added `adapters/valuation_fixture.py`, separate `fixtures/paper_valuations.json` and `application/monitoring.py`: two invented historical frames, explicit one-calendar-day freshness, source hash, archived inputs/results and recorded time. Atomic SQLite valuations keyed by run/date; repeat dates return the original snapshot. Reads verify checksum, approval identity and recomputed arithmetic. Missing current fixtures do not prevent saved replay.
- Added GET/POST `/api/runs/{id}/valuations`; POST requires one explicit fixture timestamp. Approval is required; no research/model dispatch. New manifests and approvals retain run creation time and research cutoff; legacy creation dates remain unknown. Existing approvals are preserved.
- React `Monitoring.jsx`, PaperLedger integration and styles expose manual price updates, saved replay selection, dates, exact provenance and synthetic/no-fresh-research labels. Reload only reads; no polling/scheduler or live mode.
- `backend/tests/test_m4_monitoring.py`: 13 tests. Full `uv run --locked python -m unittest discover -s backend/tests -q`: 146 passed. Tests prove unchanged book/workflow state, no model/research construction, date/coverage failures, duplicate replay, unavailable provider, corruption, rollback/retry, legacy timestamps and HTTP behavior.
- React production build passed. Extended Chromium smoke passed production :8765 and Vite :5173 with two updates, earlier replay, reload, unchanged research state, prior approval/recovery flows and 390px monitoring layout; mobile monitoring screenshot inspected. Made the pause test deterministic with a test-only stage-response delay after an initial Vite timeout; final rerun passed.
- Scope: manual synthetic valuation, not live monitoring, automatic research refresh, rebalancing or validated investment performance. No new dependency, live calls, spending, trades or commit. Next M5.1: configurable expansion to approximately 20 companies with coverage audit and honest runtime/usage evidence.

## M5.1 evidence — 2026-09-30

- Added three `_20.json` fixture files for research, fills and valuations: 20 illustrative company labels with full synthetic coverage. Retained original five-company fixtures/live-proof config. `--fixture-set twenty --port 8766` uses isolated data/ui_runs_20; React supports selectable subsets.
- DemoService validates universe uniqueness/price-array coverage and loads explicit profile budgets. Expanded limits: 20 companies, 45 scripted calls, 34,560 output-token reservation ceiling, 80 retrieval queries, one explicit retry per step, one review round, zero revisions, concurrency one. Complete critic context explicitly capped at 64,000 characters; research prompts remain at 8,000. Five-company critic default remains 8,000; no evidence truncation.
- First expanded audit reached workflow success but strict paper approval exposed decimal weight summation error. Fixed optimiser output to reconcile to the exact asset target within original bounds, reject material residuals and recompute variance on returned weights. Solver version is now in workflow fingerprint; pending pre-change runs require a new run. Saved reports/receipts remain readable.
- `backend/app/universe_audit.py` produces `evidence/m5_1_fixture_audit.json`: per-company coverage, source hashes, configuration, stage timings, statuses and usage. Both profiles completed research, approval and two valuations in temporary test directories.
- Recorded workflow sample: five 0.4010881s; twenty 1.9336716s. Scripted calls 11/41; reserved output tokens 8,448/31,488; critic prompt 6,194/21,663 characters. All call token usage is unknown; inference cost null. External calls/provider spend zero. Single local samples include checkpoint I/O; these are not provider latency or investment-performance measurements.
- Full offline suite: 152 passed, including six M5 tests for complete flow, subsets/exclusions, complete critic coverage/bounds, invalid fixture coverage, isolated storage and exact decimal weights. Five-company regressions pass. Non-failing ResourceWarnings appeared from mocked HTTP 429/503 cleanup.
- React build passed. Chromium smoke with UI_BASE_URL=:8766 and EXPECTED_COMPANIES=20 passed research, approval, two updates/replay/reload, rejection, quota recovery, pause/resume and 390px layout without page errors; mobile screenshot inspected. Initial load timed out once; console/network probe and full rerun passed, without a reproducible load failure.
- Limits: one shared invented passage per company serves both roles; no independent news/live 20-company coverage. Three sessions/repeated patterns cannot support investment evaluation. Membership is illustrative, not point-in-time verified. No new dependency, live call, spending, trade or commit. Next M5.2: comparable baseline/single-agent/multi-agent experiments.

## M5.2 evidence — 2026-09-30

- Added `fixtures/comparison_plan.json` and `comparison_holdout.json`. Fixed dates/costs/variants and no tuning; decisions for both profiles freeze before reading either development or synthetic holdout prices. Holdout is evaluation-only code input, not independent market evidence.
- `research/combined.py` and `adapters/comparison_fixture.py`: one bounded scripted call per company returns existing fundamental/news contracts, with separate citation allowlists and shared news validation. Two research designs retain common selection, optimiser and critic. Equal output allowance: 1,536 combined vs two 768 specialist tokens, plus 768 critic tokens. Complete combined input cap 16,000; existing profile critic bounds preserved.
- `evaluation/comparison.py`, `compare_experiments.py`: equal-weight, numerical-only, combined researcher and separate researchers on five/twenty profiles; exact common fees and book/valuation rules. Archived candidates, selection reasons, reports, prompts/model identities, input hashes, timings/usage, allocations and results. Stable decision identities exclude timing; archive-only replay verifies sources/decisions and exact arithmetic without source-file/model access.
- `uv run --locked python -m backend.app.compare_experiments --output evidence/m5_2_comparison.json`: all eight variant/profile combinations succeeded on development and holdout. JSON and readable Markdown saved. `--replay evidence/m5_2_comparison.json --output data/m5_2_replay.json`: passed; ignored replay artifact generated. Final report also regenerated from archive successfully.
- Outcome: all candidates retained; research allocations/returns exactly match numerical-only. Combined vs separate scripted calls: 6 vs 11 (five), 21 vs 41 (twenty). Output reservation caps equal at 8,448 and 31,488. Actual model tokens/cost unknown, external calls/provider spend zero. No incremental selection benefit or winner established.
- `uv run --locked python -m unittest backend.tests.test_m5_comparison -q`: 12 passed. Full `uv run --locked python -m unittest discover -s backend/tests -q`: 164 passed. Tests cover holdout perturbation without decision changes, input-read isolation, same costs/caps, reproducible decision identity, bad citations/role keys, missing/future evidence, invalid prices/actions, failed research suppression, corrupt archives and accurate reporting. Existing non-failing mocked HTTP 429/503 cleanup ResourceWarnings remain.
- React unchanged; no frontend build/browser rerun needed. No new dependency, live access, real approval, ledger mutation, trade, spend, publication or commit. M5.2 DONE at offline harness scope; no financial/model-quality conclusion. Next M5.3: verified college demonstration and evidence bundle.

## M5.3 completion evidence — 2026-09-30

- Files: demo/README.md, walkthrough.md, presenter_notes.md; backend/app/demo_bundle.py; backend/tests/test_m5_demo_bundle.py; evidence/m5_3_verification.json and m5_3_bundle_manifest.json. Bundle includes source/locks/configuration/synthetic fixtures and reproducible M5 reports. Excludes credentials/environment files, live caches, dependencies, compiled frontend and existing runtime books.
- Packaging checks: four tests passed for repeatability, inventory/exclusions, adapter source retention, checksum corruption, traversal/unlisted payload rejection, missing required files and source overwrite prevention. Initial extracted suite failed because a generic data-folder exclusion omitted real adapter source; corrected and reran from a new extraction.
- Corrected fresh extraction data/m5_3_clean_demo_v2: uv sync --locked --offline and npm --prefix frontend ci --offline passed using local caches; npm --prefix frontend run build passed. uv run --locked python -m unittest discover -s backend/tests -v: 168 passed. Archive-only compare_experiments replay: all eight combinations succeeded without model/current-fixture calls. Existing mocked HTTP cleanup ResourceWarnings are non-failing.
- Local production Chromium smoke passed with EXPECTED_COMPANIES=5 on :8770 and 20 on :8771. Verified cited reports, explicit consent/approval, identical reload receipt, exact reconciliation, two valuations and saved replay, unchanged research, rejection hiding allocation, quota retry, pause/reload/resume, 390px layout and no page errors. Inspected the expanded monitoring screenshot. Runtime generated books/screenshots remain ignored synthetic test data.
- Final ZIP inventory/hash verification passed with 108 files plus its manifest; executable sources, fixture/configuration and dependency identities match the tested extraction. Presenter outline is approximately seven minutes, not a measured presentation duration. Windows/cached setup only; dependency downloads may be needed elsewhere. No new dependency, live call, provider spend, publication, real trade or commit. M5.3 DONE; planned proof tasks complete. Next: presentation-machine rehearsal, then separately scoped independent evaluation.

## UI.1 frontend redesign evidence — 2026-09-30

- Inspected all frontend code, entry/configuration/lock files, styles, forms, responsive behavior and smoke tests before edits. Read frontend/DESIGN.md, installed design-taste-frontend and web-design-guidelines skills, and fetched the current Vercel guideline source for initial/final review. One root workspace; no client-side router or extra pages.
- Updated main.jsx, PaperLedger.jsx, Monitoring.jsx, style.css, paper.css and index.html for the supplied white/parchment/black/Action Blue system, deliberate system typography and consistent form/table/section spacing. Covered initial/loading/error states, configuration/saved runs, progress/recovery, allocation, selection/citations, approval/journal and valuation/replay. Original brand, action names, consent text and raw evidence preserved.
- Added src/ui.jsx primitives (Button/Field/SectionHeading/Notice/Metrics/DataTable/Timestamp). Added field names/labels, inline native errors, expanded hidden invalid controls, error focus, skip link, scoped table headings/captions, keyboard scroll regions, 44px targets, reduced-motion pending indicator and unsaved edited-policy guard. Display date/currency formatting retains original ISO/exact JSON values. Domain math remains in Python.
- Added optional frontend/design-audit.cjs; extended smoke screenshot-output configuration and changed date assertion to the preserved time datetime attribute. npm run check uses existing Prettier; no semantic lint/typecheck was added or claimed. No dependency/lockfile, backend, API, auth/database, policy/workflow, fixture or route change.
- npm --prefix frontend run build and run check passed. Relevant backend/UI/ledger/monitoring/bundle suite: 34 passed. Final Chromium smoke passed five-company :8772 and twenty-company :8773 through research/citations, approval/reload, two valuations/replay, rejection, quota retry, pause/resume and 390px layout without page errors.
- Final design-audit passed both profiles at 320/390/640/768/834/1024/1440/1920px: initial failure/loading, native/backend errors/focus, unsaved-policy guard, read-only saved runs, missing-evidence suppression, names/labels, 44px targets, long metrics and no document overflow. Corrected a pause control offered before a new run was ready; original executor unchanged. Visual review refined date labels, narrow metrics and unfocused skip-link clipping. See evidence/frontend_redesign_audit.md; screenshots/results are ignored runtime test data.
- UI.1 DONE. Chromium-only; Safari/Firefox, screen-reader device testing, axe and Lighthouse/CWV scoring unverified. M5.3 ZIP remains the prior UI snapshot; demo repackaging is separate. No provider call, spend, publication, real trade or commit. Next: user visual review/presentation-machine rehearsal and separately scoped wider validation.

## M5.3 package refresh evidence — 2026-10-01

- Existing milestone was already DONE; refreshed its historical ZIP after UI.1. Added demo/report.md and evidence/m5_3_refresh_verification.json; extended demo_bundle fixed allowlist for report/current verification and frontend/DESIGN.md/design-audit.cjs. Updated guide evidence links. Source/API/fixtures/dependency locks preserved.
- Fresh extraction data/m5_3_refresh_20261001: uv sync --locked --offline, npm --prefix frontend ci --offline and npm --prefix frontend run build passed with existing caches. Full offline suite: 168 passed in 22.331 seconds; non-failing mocked HTTP 429/503 ResourceWarnings. All eight archived comparisons replayed successfully without current fixtures/models.
- Both production Chromium smoke rehearsals passed on :8780/:8781 with five/twenty companies: citations, consent, exact ledger/reload, two valuations/saved replay, unchanged research, rejection, quota retry, pause/resume, 390px containment and no JS errors. Used existing Playwright runtime; no fresh screenshot visual audit. Both task-owned servers stopped.
- npm --prefix frontend run check failed on existing src/main.jsx formatting; no unrelated UI change. Historical passing checks remain historical. Final package checks and identities: ignored data/m5_3_refresh_integrity.json; inventory evidence/m5_3_bundle_manifest.json; refreshed ZIP data/agent-of-odds-demo.zip has 113 payload files plus manifest.
- Windows/cached installation only; cache-free/other-OS setup, other browsers and timed presentation unverified. Synthetic evidence and historical narrow live proofs are clearly separated. No live provider call, spend, publication, real trade or commit. Next: presentation-machine rehearsal; independent evaluation requires separate scope.
