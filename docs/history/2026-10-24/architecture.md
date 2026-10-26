# Architecture — Agent of Odds

Version: 0.6 · 2026-09-30  
Status: Python modular monolith, independent numerical core, bounded research workflow, local API, React/Vite frontend, exact paper ledger, valuation replay and demo packaging are implemented at recorded fixture scopes. Current interfaces are documented in the appended milestone sections; the initial layout below includes historical proposals. Python uses uv with NumPy; no deployed worker, LangGraph or FastAPI is installed.

## 1. Modular monolith

Use one backend codebase with clearly separated modules. It can initially run as one local process. Move long-running execution into a separate worker only when demonstrated needs justify it. Multiple agent roles do not require multiple servers or different model subscriptions.

The UI calls application services. Application services coordinate domain logic, workflow execution, and adapter interfaces. Provider implementations fulfil those interfaces. Domain calculations remain usable from tests and offline scripts without the web server or an LLM.

## 2. Proposed source layout

| Path | Responsibility |
| --- | --- |
| backend/app/api/ | HTTP request/response validation, run submission, status and result access |
| backend/app/application/ | Use cases: research, allocation, review, paper tracking |
| backend/app/domain/ | Policies, finance calculations, selection, optimisation, validation, ledger rules |
| backend/app/contracts/ | Typed data models and provider/repository interfaces |
| backend/app/adapters/data/ | SEC, price/news providers, and fixture implementations |
| backend/app/adapters/llm/ | Hosted or local model integrations |
| backend/app/adapters/storage/ | Structured repositories, document store, retrieval index |
| backend/app/workflows/ | LangGraph nodes, routing, state, checkpoints and run budgets |
| backend/app/research/ | Role instructions, evidence interpretation, synthesis and critic logic |
| backend/app/evaluation/ | Historical replay, baseline strategies, metrics and experiment manifests |
| backend/app/config/ | Validated configuration and budget defaults |
| backend/tests/ | Domain, contract, integration, and workflow tests |
| frontend/ | React UI; communicates through backend interfaces |
| fixtures/ | Small permitted/synthetic datasets and recorded model outputs |
| experiments/ | Configurations and compact result manifests; large data stored separately |

This is a design map, not an existing directory tree. Avoid creating empty layers until a milestone needs them.

## 3. Interface boundaries

| Interface | Example operation | Required outcome |
| --- | --- | --- |
| MarketDataProvider | get_bars(symbols, start, end, feed, adjustment) | Bars plus provider, feed, adjustment and timestamps |
| FundamentalsProvider | get_facts(company, as_of) | Values with units, period, filing/publication dates and source IDs |
| DocumentProvider | list/fetch(company, as_of, document_type) | Versioned source records and content references |
| NewsProvider | search(symbols, start, end) | Dated deduplicated records, coverage limitations |
| EvidenceRetriever | retrieve(query, company, as_of, limit) | Passages with source IDs and availability metadata |
| ModelClient | generate(messages, tools, output_schema, budget) | Validatable output, model ID, usage and error status |
| ResearchRepository | get/put(cache_key, report) | Stored evidence-grounded report and compatibility metadata |
| PortfolioOptimiser | solve(numerical_inputs, policy) | Weights, solver status, diagnostics or infeasibility |
| RunRepository | checkpoint/load(run_id) | Serializable state and execution metadata |

Signatures are illustrative; settle concrete schemas during implementation. Provider substitution is conditional on capabilities. A replacement must support the required data, tools, structured output, and cutoff semantics; fail clearly if it cannot.

## 4. Contracts and versions

Use typed schemas, initially Pydantic-compatible, for:
- InvestmentPolicy: policy version, universe, amount/currency, horizon, objective, hard constraints and review schedule.
- EvidenceRecord: source ID, provider, company, source URL/reference, published/available time, retrieved time, period, units where relevant, content hash/version.
- ResearchFinding: claim, fact/interpretation classification, evidence IDs, uncertainties, missing information, as-of cutoff.
- ResearchReport: role, findings, concise rationale, model/prompt/config versions, evidence snapshot references.
- PortfolioProposal: candidate set, weights, cash treatment, objective, policy/data versions, diagnostics and validation status.
- RunManifest: run ID, schema version, cutoff, inputs, code revision when available, model, prompts, tokens, costs, checkpoints, outcomes.

Version schemas when persisted meanings change. Do not put provider-specific response objects directly into the shared domain models.

## 5. Time, cache and reuse

Centralise data access. Every historical request carries an explicit as-of cutoff; enforce availability in tools rather than relying on prompts. Current facts and later restatements cannot be substituted for earlier public information.

Research cache compatibility should include company, cutoff, evidence versions, prompt/model version, and analysis settings. User-independent company research can be reused across users; suitability and allocations are recomputed from each policy. A change in amount alone does not trigger fresh filing analysis.

Do not refresh data solely because the frontend rerenders. Price valuation is numerical and does not require agent execution.

## 6. Execution modes

- **Fixture:** no network or paid inference; explicit synthetic/recorded sources for development.
- **Live research:** permitted provider access with freshness checks and quota controls.
- **Historical evaluation:** fixed cutoff and experiment configuration; disallow unrestricted present-day search.
- **Demo replay:** display an existing run, visibly labelled with its original date; no claim of fresh analysis.

Same use-case contracts across modes; different adapters. Start with fixture mode and one tested live adapter.

## 7. Failure handling and safe boundaries

Use explicit statuses: success, partial_data, awaiting_quota, failed_validation, infeasible, cancelled, and failed, or a comparable defined enum. No silent fabricated values or automatic policy relaxation.

Workflow retries must not duplicate paper orders or ledger entries. Give proposals and approved paper transactions stable IDs and enforce idempotency. Checkpoints should preserve the last completed stage so a quota error does not force a full rerun.

Backend owns secrets and spending controls. External document contents cannot override policy or tool permissions. The optimiser and ledger must not depend on generated prose.

## 8. Evaluation boundaries

Research quality, stock selection, allocation, and paper execution are separate units of evaluation. Compare strategies with compatible evidence, universe, dates, constraints, and costs. Archive inputs and outputs sufficient to inspect a result. A saved model response supports replay, not a promise that a later generation will be identical.

## 9. Decisions to resolve during implementation

Concrete schemas; authentication; background execution approach; covariance estimator; selection rule; solver; feed adjustments; trading-calendar handling; paper fill/dividend conventions; exact provider/model; persistence migration strategy. Do not invent default numerical finance settings just to make an integration pass.

## 10. Implemented fixture boundary (v0.4)

`load_universe(Path) -> Universe` loads schema v1 TOML into frozen dataclasses; no five-company limit is encoded. `load_prices(Path, symbols, as_of, start, end) -> PriceResult` validates synthetic schema v1 JSON and filters by requested companies, inclusive session window and availability timestamp. `DailyClose` stores Decimal close, session date, timezone-aware availability and source ID. These minimal standard-library contracts precede the proposed full schemas.

Result statuses are success or partial_data; validation raises errors translated by the CLI to failed_validation. The CLI exits 0/1/2 respectively. Provenance includes fixture kind, USD units, synthetic feed, no-adjustment convention, artifact creation time, SHA-256, requested dates and cutoff. Creation time is not presented as historical retrieval time. Source IDs refer to invented fixture records.

Success means at least one eligible observation per requested symbol, not trading-calendar completeness or freshness. No returns, actions, dividends, financial facts or evidence retrieval are implemented. Live data needs separate provenance, availability and adjustment contracts; the fixture adapter deliberately rejects live/unlabelled inputs.

## 11. SEC access-proof boundary (v0.5)

`SecClient.fetch(url)` accepts only ticker JSON, CIK submissions and CompanyFacts endpoints. It returns parsed JSON (decimal numbers retain precision) plus response URL, SHA-256, retrieval time and byte count. It requires a declared application/contact header, disallows redirects, bounds request count/size/time, and translates failures into missing_configuration, awaiting_quota, provider_error or failed_validation. It is sequential and single-process; the limit is not a distributed rate limiter. No automatic retries or cache exists yet.

`resolve_symbols` checks unique exact current ticker matches. `eligible_assets` checks response CIK, USD units, finite nonnegative values and accession syntax; preserves period-end, filed date, form and source ID. `eligible_filings` checks parallel arrays and creates validated archive references from recent submissions. Neither function downloads a filing body.

Date-only filing records use next-day 05:00 UTC as a conservative end-of-US-Eastern-day availability proxy, not a claimed exact dissemination timestamp. This excludes same-day records and later filings/restatements. Current SEC snapshots may include post-acceptance corrections; filters alone do not establish a point-in-time archive. The probe chooses the latest eligible period/filed Assets observation, not a full financial statement. Older submission pages, timestamps from acceptance metadata, full evidence contracts and raw-response persistence are future work.

The explicit `backend.app.sec_probe` CLI is separate from the offline default. It prints a narrow access-proof result; success requires an Assets observation and filing metadata per configured company. Partial coverage exits 1; missing configuration and provider errors also exit 1 with distinct JSON statuses. Unfinished companies are not checkpointed on a failed probe.

## 12. Local configuration boundary (v0.5.1)

The explicit SEC probe now reads a project-root `.env` by default using a deliberately small parser for `KEY=VALUE` entries. It ignores comments and blank lines, rejects malformed keys/lines, supports matching single/double quotes, and never overwrites a variable already set by the launching shell. This is configuration loading only; no general dotenv dependency was added. `.env` is ignored and `.env.example` must contain placeholders only.

## 13. Verified SEC live proof (2026-09-21)

The live probe was run using the locally configured SEC contact identity. It verified the configured issuer CIKs and a USD Assets record eligible at the 2025-01-31 cutoff for all five companies. It found accessible recent filing metadata for MSFT, JNJ, XOM and WMT. JPM's current submissions response did not contain a qualifying filing at the cutoff, while its CompanyFacts record did; historical submission-page support remains needed for full filing coverage.

The SEC current ticker listing maps `XOM` to CIK 0002115436, titled ExxonMobil Holdings Corp, while the intended Exxon Mobil Corporation is CIK 0000034088. The universe now carries explicit SEC CIKs and uses them for retrieval; ticker results are an audit only. This prevents an ambiguous ticker from changing issuer identity silently.
## 14. Alpaca Market Data proof boundary (v0.7)

`AlpacaMarketDataClient` exposes one method: `daily_bars(symbols, start, end, feed="iex", adjustment="all")`. It permits one HTTPS request per proof run to the allowlisted Alpaca Market Data endpoint, has a 20-second timeout and 20 MB response cap, disallows redirects/retries, and exposes no trading operation. It authenticates through Trading API key/secret headers loaded from ignored local configuration.

The initial normaliser emits only symbol, session, close, provider bar timestamp and source ID. It retains request provenance externally. It rejects invalid/nonpositive closes and reports missing symbols. A historical daily-bar timestamp is not treated as a publication-availability timestamp; no live bar is marked cutoff-eligible from this adapter. The request convention is IEX plus `adjustment=all`; IEX coverage and adjustment semantics must remain part of every later comparison.
## 15. Filing/release evidence proof boundary (v0.8)

`EvidenceClient` fetches at most two configured HTML documents per explicit proof run: one URL constructed from validated SEC CIK/accession/document components, and one exact allowlisted Microsoft investor-relations URL. It disallows redirects/retries, has a 20-second timeout and 10 MB cap, and computes source provenance without retaining the body. HTML is converted to visible text only for minimum-length and configured date/title-marker checks; external content is never executed.

The current proof configuration is one MSFT Form 10-Q and one MSFT FY25 Q2 release. It does not provide a general crawler, document cache, vector index, independent news feed, citation passages or historical timestamp guarantee. Those belong to later retrieval work.
## 16. M0.5 model-proof boundary (v0.9)

`GeminiClient` sends at most one request to the allowlisted Gemini generate-content endpoint. The contract fixes `gemini-3.6-flash`, temperature 0, 256 output tokens and JSON schema output; it permits no tools, browsing, arbitrary model names, retries or fallback models. Safe metadata includes model ID, prompt/response hashes, retrieval time and provider usage fields when supplied; it never stores the API key.

`validate_m0_output` requires the exact company, `insufficient_evidence` status, exact source-ID set and non-empty limitation. The proof receives only M0 source IDs, not source text, and cannot produce a substantive finding. Its schema validation is engineering validation, not factual validation.

Live state: model listing succeeded, two legacy 2.5 model generation IDs returned 404 because they are unavailable to new users, and the provider-recommended 3.6 Flash returned HTTP 503. The adapter maps this to `awaiting_quota` and makes no retry.
## 17. M1.1 policy and numerical-input contracts (v1)

`InvestmentPolicy` is a frozen domain model independent of LLM/provider code. It validates a timezone-aware cutoff, unique eligible symbols, positive capital, USD scope, explicit minimum-variance objective, asset/cash bounds and review frequency. It detects mathematical infeasibility from aggregate minimum/maximum weights before an optimiser runs; it never relaxes inputs. No qualitative risk profile or user default has been mapped yet.

`PriceInput` is a frozen provider-neutral numerical record. It requires complete provenance (provider, feed, adjustment, currency, hash, retrieval time), explicit coverage outcome and `verified`/`not_verified` availability. `point_in_time_eligible` is false unless coverage and availability are both explicit. It uses `DailyClose` values but does not calculate returns, covariance, allocations or performance.
## 18. M1.2 numerical baseline and optimiser (v1.1)

`aligned_simple_returns` intersects session dates across all requested assets, then computes `close[t] / close[t-1] - 1`. It requires verified availability and at least three common sessions. `sample_covariance` uses `numpy.cov(..., ddof=1)` and requires at least two return observations. No live Alpaca proof bar is point-in-time eligible until its availability conventions are resolved.

`solve_minimum_variance` validates a symmetric positive-semidefinite covariance matrix using eigenvalues, projects weights onto a bounded simplex, and applies projected gradient descent with a spectral-radius step size. Output includes weights, cash, estimated variance, iteration count and declared conventions. The objective is `w'Σw`; when cash is permitted it is zero variance, so the solver assigns the largest permitted cash weight and minimises variance over the remaining asset exposure. It never relaxes bounds.

The solver is deliberately limited to long-only minimum variance, uniform asset bounds, USD and explicit policy inputs. It is not yet a persisted service, a return forecast, a CVaR optimiser, or a tax-aware allocator.

## 19. M1.3 basic evaluation boundary (v1.2)

`EvaluationPlan` separates the allocation decision cutoff from the next-session execution date and later valuation date. It requires explicit transaction cost basis points and fixed conventions: `next_session_close` execution and close-to-close valuation excluding dividends. Same-date execution, valuation before execution, negative costs, and an evaluation cutoff before required prices are rejected.

`equal_weight_portfolio` uses the same symbols, uniform asset bounds and maximum-cash convention as the minimum-variance result. `evaluate_hold_period` accepts fixed weights, requires a successful allocation and fully covered point-in-time-eligible price input, checks that the policy cutoff equals the decision timestamp, and rejects required bars unavailable by the evaluation cutoff. `compare_with_equal_weight` applies identical sessions and costs to both portfolios and reports their net-return difference.

This is a deterministic single hold-period evaluator, not a rolling backtest. It excludes dividends, taxes, slippage beyond the declared basis-point cost, bid/ask effects, partial fills, trading calendars, corporate actions and repeated rebalancing. Live Alpaca proof bars remain ineligible because their historical availability has not been certified.

## 20. M2.1 local evidence index boundary (v1.3)

`EvidenceDocument` validates source identity, company, source type, timezone-aware publication/retrieval times, URL, SHA-256 source version and nonempty text. `chunk_document` creates deterministic overlapping word chunks whose IDs bind the source ID, source version, ordinal and chunk text. A changed source version therefore cannot silently reuse old chunk identities.

`LocalEvidenceIndex` persists a schema-versioned JSON manifest and chunks under ignored `data/`. Search first applies exact company and inclusive publication-time filters, then ranks eligible chunks with a bounded local TF-IDF cosine baseline. Results carry chunk ID, source ID, source hash, company, publication time, score and text so later findings can cite the retrieved evidence version. Query result count is limited to 1–20.

This is lexical retrieval, not an embedding model or semantic-vector claim. It adds no paid service or dependency. The live proof contains only the configured Microsoft 10-Q and investor release. Full-document HTML is not committed; rebuilding can produce a new source version when provider HTML changes.

## 21. M2.2 grounded fundamental-research boundary (v1.4)

`ResearchRequest` bounds a role to one company, one timezone-aware cutoff, one to four unique queries, and one to five hits per query. Retrieval always supplies the exact company and publication cutoff to the index. Duplicate chunks across queries are removed before prompting.

The research prompt is capped at 8,000 characters and labels every retrieved passage as untrusted data rather than instructions. It forbids memory-based facts, advice, price targets and portfolio weights. Model output is restricted to at most five findings, a qualitative assessment, exact retrieved chunk IDs and limitations. Validation rejects unknown or duplicate citations, empty successful reports, findings attached to an insufficient-evidence status, and unexpected fields.

When no eligible evidence exists, the role returns `insufficient_evidence` without calling a model. Provider quota, availability and validation failures remain structured outcomes. The runnable probe emits citation metadata without echoing document passages. One live MSFT report passed schema and manual citation checks; this completes the role proof but does not establish broad research accuracy.

Gemini 3.6 Flash uses `thinkingLevel=minimal` for these bounded structured tasks. Google documents that output limits include thought tokens; safe envelope diagnostics retain finish reason, response hash, shape and token usage without retaining invalid generated content. This makes truncation distinguishable from transport, quota and malformed-envelope failures.

## 22. M3.1 specialist boundaries — 2026-09-29

`run_news_research(index, NewsRequest, model)` wraps the existing ResearchRequest with an explicit inclusive publication-window start. It selects investor-release and fixture sources before lexical ranking, excluding SEC filings; fixture sources in this role must be supplied as synthetic news/release evidence. It deduplicates chunks, makes at most four searches and one 768-token model call, and caps the prompt at 8,000 characters. Validation allows citations only to the actual prompt-visible passages. NewsFinding separates a reported-event claim from a hypothesis/interpretation and retains qualitative assessment and chunk citations. NewsReport includes publication window, evidence dates/hashes, prompt version/hash, provider metadata, trace and mandatory coverage/availability limitations. Missing evidence skips generation; provider and validation failures remain structured. This is fixed retrieval, not autonomous tool planning.

`run_quantitative_research(PriceInput, max_age_days=...)` has no model dependency and requires an explicit nonnegative calendar-day freshness tolerance. It returns QuantitativeReport with structured status, symbol ordering, cutoff, provenance, limitations and optional PriceStatistics. Missing coverage and unverified historical availability return insufficient_evidence; a latest common session older than the tolerance returns stale_data; malformed, future or insufficient-length series return failed_validation.

`domain/statistics.py` owns arithmetic, reusing aligned_simple_returns and sample_covariance. It checks all supplied bars for future session/availability, missing source IDs and nonfinite prices before calculating means, sample volatility, cumulative compounded returns and covariance. Measures use intersected sessions, fractions, ddof=1 and no annualisation. Reported volatility is per observed interval; market-calendar gaps, corporate-action accuracy and total-return conventions remain limitations. The roles neither select candidates nor allocate weights. Existing fundamental-role interfaces remain unchanged; there is no new provider integration or dependency.
## 23. M3.2 candidate-selection boundary — 2026-09-29

`domain.selection.SelectionPolicy` is a required-input, versioned eligibility configuration. It declares excluded universe members, per-role assessment allowlists, maximum cited-evidence and price ages (calendar days), minimum return observations, maximum sample volatility (fraction per observed interval, no annualisation), and minimum candidate count. There are no implicit settings or risk-profile mappings.

`application.selection.select_candidates(investment, policy, fundamentals, news, quantitative)` receives existing specialist report dataclasses, company-keyed text reports, and one quantitative report covering the relevant symbols. It makes no provider/model call. Both text roles must succeed at the investment cutoff and contain findings with valid same-company, nonfuture, fresh citations. Each finding must pass its role's assessment allowlist; news citations must also lie inside the report window. Quantitative results require matching cutoff/symbol ordering, finite relevant measures, verified availability/version provenance, sufficient observations and policy freshness/volatility limits. Report failures are preserved in exclusion reasons.

All passing companies are retained in original universe order; there is no ranking, cap, tie-breaking score or LLM percentage. SelectionResult includes decisions with reasons/citations/limitations, complete selection/investment policy snapshots and a SHA-256 over supplied reports/settings for reproducibility. Explicit exclusions bypass research requirements. Too few eligible companies returns insufficient_candidates. Revalidating a copy of the InvestmentPolicy on eligible symbols detects infeasible unchanged aggregate bounds and returns infeasible; the original policy is not modified. Both failures suppress the actionable candidate tuple while preserving eligibility decisions. Allocation and covariance construction remain downstream responsibilities.

The service validates consumed report fields and citations, not semantic truth or recomputation of numerical statistics. Inputs must originate from the validated research/calculation paths; the input hash is a trace identifier, not an authenticity guarantee. No product-level thresholds or demonstrated investment advantage are claimed.
## 24. M3.3 bounded workflow and checkpoint boundary — 2026-09-29

`workflows.runner.run_workflow` composes the existing modules as a sequential local state machine: quantitative inputs -> per-company fundamental/news -> selection -> recomputed candidate-ordered covariance/allocation -> deterministic allocation review -> evidence critic. Explicitly excluded companies skip text roles. No network retrieval is added; the caller supplies prices, index, per-company ResearchRequest values and news-window start. The injected `model_factory(step)` supplies the configured client for each dispatch; model identity must match returned metadata. A fresh one-request adapter can be constructed per dispatch using the same configured account. All dispatches remain governed by the persistent run budget; no credential/account rotation is implemented.

WorkflowBudget requires maximum companies, model calls, reserved output tokens, retrieval queries, retries per stage, review rounds and revisions. Each generation uses at most 768 output tokens and 8,000 prompt characters; concurrency is one. Retrieval reservations count declared queries conservatively even if a stage fails early. Call/output reservations and content-free prompt hashes are saved before dispatch. Per-event metadata retains only allowlisted identity/hash/time/usage fields. Reported token sums cover known values only, unknown-call counts are explicit and cost is null; reserved output ceilings are not measured usage or billing limits. Maximum input size is bounded by prompt characters and call count, not a tokenizer estimate.

`JsonCheckpointStore(directory)` writes versioned checksummed JSON through fsync and atomic replace; decoding is restricted to a fixed dataclass registry, dates, decimals and tuples. Use ignored `data/workflow_runs/` for application checkpoints because they contain research passages and configuration. Per-run exclusive lock files prevent concurrent writers. An abrupt process kill can leave a lock: an operator must establish that no writer is active before removing it. Checksums detect corruption, not hostile modification; checkpoints and model factories are trusted local application inputs. No pickle, dynamically imported type or evidence-selected destination is used.

Resume requires identical inputs/configuration, model, source versions and prompt/workflow versions, compared through a canonical fingerprint. The caller supplies the original inputs again. Finished stages are reused and a completed run is idempotent. Provider/quota failures are checkpointed and returned immediately; no automatic retry or timer runs. `retry_failed=True` explicitly permits retry of a retryable failed stage, up to the persisted per-stage limit (at most one). A saved in-flight stage becomes interrupted and also requires explicit retry; its reserved call remains charged because provider completion is unknown. Changing budgets requires a new run ID. `max_steps` permits a cooperative checkpoint boundary without changing the run fingerprint. Local filesystem failure/lock/corruption is an explicit checkpoint_error.

The evidence critic checks every selected text finding against its complete cited passage, separates reported events and interpretations, and can approve/reject/request a single target from the supplied research-stage allowlist. Shared passages and limitations are deduplicated. If complete coverage cannot fit, review_incomplete is returned; no subset is silently reviewed. Revision feedback is untrusted text, has at most 400 characters and cannot choose tools or destinations. One allowed revision reruns that report and downstream selection/allocation/review; a second critic round must approve. A revision prompt that exceeds 8,000 characters fails validation rather than truncating cited evidence. Stage history preserves the original and revised reports. Numeric review independently checks portfolio symbols, finiteness, totals, asset/cash bounds and estimated variance, and surfaces minimum-variance objective limitations. Only top-level workflow success denotes a fully reviewed fixture proposal; intermediate allocations on failures remain diagnostic and must not be actionable.

The fundamental prompt contract is v2: evidence/citation validation now uses only actual prompt-visible passages, including any truncated final passage. This fixes acceptance of citations omitted by the prior prompt budget. M3.3 adds no dependency: the initial resumable executor is a local state machine; a LangGraph backend remains a future implementation option rather than an installed capability. No API/UI, scheduler, ledger, human approval or execution is introduced.
## 25. M4.1 local fixture UI boundary — 2026-09-29

Updated September 30: the implemented frontend is React/Vite in frontend/, as explicitly required by the user. `backend.app.ui` serves the compiled frontend/dist index and assets on 127.0.0.1:8765. FastAPI remains unimplemented. Browser code calls a narrow JSON application service; numerical/selection/workflow modules remain independent. No external fonts, scripts or browser-to-provider calls are used. This is a local fixture demonstration, not a production HTTP server or multi-user deployment.

`DemoService` loads a versioned `fixtures/workflow_demo.json` universe, fixed cutoff, invented prices and evidence. UI settings expose required explicit policy/selection values and immutable fixture execution limits. Test values are loaded only on the user's demo-policy action. `FixtureModel` generates scripted cited findings and critic decisions; the quota scenario interrupts the first eligible news stage and recovers only on explicit retry. Normal, missing-evidence and rejected-review scenarios are also available. No tests, .env values or live provider adapters are imported by the UI service.

Endpoints: GET /api/settings, GET /api/runs (up to 30 saved runs), POST /api/runs (validate/persist policy), GET /api/runs/{id} (read-only snapshot), POST /api/runs/{id}/advance with an explicit boolean retry field (one workflow stage). Run IDs are generated server-side and validated before filesystem access. Saved input manifests and workflow checkpoints live under ignored data/ui_runs. Resume rebuilds identical fixture inputs and enforces the existing workflow fingerprint. Browser reload never starts a run; Continue/Retry are explicit actions. Pause stops the browser loop after the current atomic stage; closing the tab does not undo that stage. No worker, scheduler or unattended update is created.

The projection exposes policy, cutoff, history, progress, evidence, citations, company exclusions, review outcomes, numerical provenance, budget and known/unknown usage. It omits allocation unless top-level status is success. Failed-run diagnostic allocations are therefore absent from both UI and downloadable report. Successful output is labelled a reviewed synthetic proposal, not human approval or a ledger action. Mutable form values apply only to a new run; saved-run settings remain visible in the report.

The server allowlists static assets and API routes, checks loopback Host and same-origin Origin, requires JSON POST bodies of at most 16 KB, validates policies and uses no arbitrary path-serving endpoint. CSP and text-node rendering prevent evidence markup from becoming executable UI content. Input manifests/checkpoints remain trusted local application data. Server execution is single-threaded; live workloads, authentication, larger run history and hostile local users require a later server design.

## 26. React frontend correction — 2026-09-30

Subsequent M4.2 implementation is described in section 27 below.

React App, Results, Table and Reports components render the UI through createRoot; controlled form state and hooks own interaction. Run dispatch accepts the newly created run explicitly; mutable refs provide current pause/in-flight flags across async stage requests. Evidence remains escaped React text. Existing API contracts, persistence and allocation gating are unchanged. The old imperative app.js is removed.

Vite uses the React plugin and an explicit loopback development server on :5173. Its /api proxy targets :8765, changes the upstream Host, and removes Origin only when it matches the incoming request's own origin; other origins remain subject to backend refusal. Production uses the same-origin built bundle with the existing CSP. Only index and assets paths are served, resolved within frontend/dist; an absent build returns 503 with build instructions. package-lock.json records frontend dependencies separately from the unchanged Python uv lock.

## 27. Opening paper ledger — 2026-09-30

The subsequent monitoring implementation is described in section 28.

`domain/paper.py` owns exact Fraction arithmetic and journal replay, independently of models/workflows. An opening funding event plus fractional buys must reconcile cash + position cost + fees = funding exactly. Explicit basis-point fees reduce cash/equity; unchanged policy bounds are checked against post-fee equity. Residual cash comes from the journal, never a rounded display value. Fill dates must follow the decision date; no market-calendar validation is claimed.

`application/paper.py` binds reviewed-success checkpoint fingerprint, policy, selection identity, allocation, research/fill hashes and exact execution plan into a SHA256 proposal ID. It revalidates policy identity and numerical allocation. Separate invented fill fixtures never enter research inputs. `GET /api/runs/{id}/paper` returns the stored receipt or a read-only preview. `POST /api/runs/{id}/approve-paper` accepts exactly `approved: true` and `proposal_id`; changes require a fresh preview. Errors include not_reviewed, approval_required, proposal_changed, approval_conflict, infeasible_execution, missing_fill_prices, unsupported_corporate_action, failed_reconciliation and ledger_storage_error.

Under the checkpoint run lock, SQLite stores receipt and journal together in one transaction at ignored `data/ui_runs/paper_ledger.sqlite3`. Unique run/proposal IDs prevent duplicate opening books. Repeat approvals return the original timestamp/receipt. Explicit connection closing releases Windows file handles; transaction failures roll back. Reads check checksum, proposal binding and journal reconciliation. Local files are trusted; these checks do not authenticate users or resist malicious edits. No new dependency is required.

React PaperLedger exposes preview, exact journal and explicit consent before mutation. Current approval time is separate from historical simulation time. Scope is one isolated opening book per run, synthetic later close, exact fractional shares, declared fees (fixture zero), zero slippage, taxes excluded. Splits/dividends fail explicitly; rebalancing, withdrawals, monitoring and realistic execution are not implemented. M4.3 adds price-only valuation and labelled replay next.

## 28. Manual valuation and saved replay — 2026-09-30

`domain/valuation.py` replays the approved journal and marks unchanged fractional holdings using provider-independent DailyClose contracts. Equity is cash plus market value; P/L and return are relative to original funding and include opening fees. Calculations use exact fractions; decimal output is display-only. Require exactly one valid price per held symbol, USD/unadjusted convention, availability by valuation cutoff, no pre-fill session and explicit calendar-day age limit. Corporate actions reject; no dividends, taxes, liquidation costs or automatic constraint-driven trades are applied.

`adapters/valuation_fixture.py` bounds fixture size/frames and returns separate historical prices, provenance and source hash. `application/monitoring.py` has no model calls: it requires a verified approval, computes valuations, and stores inputs/results together in an atomic SQLite transaction. The additive valuations table in paper_ledger.sqlite3 has a primary key on run/date. Repeating a saved date returns its original snapshot without refetching prices. History checks checksum, proposal identity and recomputed arithmetic; neither approval nor journal is mutated. Missing current fixtures leave saved history readable.

GET `/api/runs/{id}/valuations` returns original research cutoff, known run creation time, fill/approval timestamps, available fixture dates and saved history. POST to the same route accepts exactly `valuation_at` and performs an explicit update or saved replay under the existing run lock. New manifests record creation time and new approval bindings preserve it with research cutoff. Legacy receipts use their checkpoint cutoff and display unknown creation time. Existing receipts are not rewritten.

React Monitoring renders date selection, manual update, saved replay and archived numeric provenance. Research cutoff, fill date, approval time, valuation date and recording time are distinct. No frontend render/reload triggers model execution or valuation writes. This is fixture monitoring with explicit historical labels, not a scheduler, live feed or fresh research. Calendar-aware freshness and corporate-action accounting remain future work.

## 29. Twenty-company fixture profile and scaling audit — 2026-09-30

DemoService accepts `fixture_set=five|twenty`; the default five-company files remain unchanged. The twenty profile loads workflow_demo_20, paper_fills_20 and paper_valuations_20 JSON files, with isolated ui_runs_20 persistence. CLI `--fixture-set` selects the profile; React renders any selected subset of configured companies and exposes company count and review bounds. The original SEC/live configuration is separate and unchanged. Profile initialization checks uniqueness, count budget and aligned price-array lengths.

Expanded fixture budgets explicitly permit 45 model calls, 34,560 reserved output tokens, 80 retrieval queries and 64,000 critic prompt characters for 20 companies. Research prompts remain at 8,000; output cap remains 768 per call, concurrency one, retry one per step, one review round, no revisions. WorkflowBudget validates critic caps up to 64,000; the default is still 8,000. Complete claims/cited passages must fit the declared bound or review_incomplete is returned. No passage is silently dropped.

Scaling exposed a precision mismatch between decimal optimiser output and the strict exact ledger. `projected_gradient_v2_exact_output` clamps decimal rounding to original bounds, distributes only a residual no larger than 1e-9 within those bounds to reach the exact asset target, derives exact residual cash and recomputes variance on returned weights. The solver version enters workflow identity. Pending older workflows fail identity comparison and require a new run; stored completed reports/books remain read-only compatible.

The audit CLI executes both profiles in temporary stores, checks research/fill/valuation coverage, and records per-stage wall time, hashes, policies, budgets and known/unknown usage in a JSON evidence artifact. Test approvals are temporary synthetic operations. It is a local scaling proof, not a live dataset audit or investment comparison. Shared invented evidence and repeated price patterns are explicit limitations for M5.2.

## 30. Controlled comparison and archived replay — 2026-09-30

`evaluation/comparison.py` separates decision preparation from evaluation. The fixed comparison_plan.json declares profiles, variants, dates, fees, freshness and no tuning. All profile decisions are built and hashed before reading either evaluation split. Existing cutoff-filtered research and numerical contracts remain authoritative. Baselines retain the configured universe; research variants share eligibility policy, optimiser and critic. Selection decisions are archived separately so allocation and selection effects are not conflated.

`research/combined.py` retrieves the same eligible fundamental/news evidence in separate allowlists, performs one combined request and returns the existing FundamentalReport/NewsReport contracts. It validates citations per role, never merges citation allowlists, and refuses a complete input above 16,000 characters. `news.validate_news_output` is now shared by separate and combined paths. The experimental adapter is explicitly scripted (fixture-combined-v1), capped at 20 research calls; one common critic call follows. Combined output cap is 1,536 versus two 768-token specialist calls; shared critic cap is 768. No automatic retries or concurrent calls occur. The normal product workflow is unchanged.

Evaluation reuses exact opening_plan/value_portfolio arithmetic with common dated fills, 10 bps opening fees, zero slippage, unchanged constraints and no dividends/taxes/liquidation costs. Development and synthetic holdout prices never enter decision functions. Failed research or invalid prices produce unavailable comparison outcomes, not a partial return or ranking. The synthetic holdout verifies code separation only; it is not independently sourced unseen market evidence.

`compare_experiments` exports JSON and Markdown. The JSON embeds byte-preserved source text/hashes, plan/configuration, model/prompt/solver identities, reports/citations, selection, allocations, bounds, call traces, unknown token/cost fields and exact books/results. Decision hashes exclude wall-clock timing so repeated decisions have stable identities. Archive-only replay verifies all source/decision identities and recalculates results without model calls or current source files. Checksums detect corruption, not malicious reauthoring. Existing local timings include unequal checkpoint overhead and are not fair model-latency comparisons.

## 31. Demo distribution boundary — 2026-09-30

`demo_bundle` is a local packaging CLI, independent of generation and numerical computation. A fixed list includes project records, locks, four noncredential configuration files, synthetic fixture profiles and recorded M5 evidence; scoped discovery includes backend Python source/tests and frontend/src JSX/JS/CSS. Source adapter folders named data are included; root runtime data is outside the permitted prefixes. Environment files, live caches, runtime receipts, installed dependencies, compiled assets and screenshots are excluded. Sources must resolve within the supplied root and cannot be symlinks; output cannot overwrite included source.

ZIP entries use sorted inventory and fixed timestamps. BUNDLE_MANIFEST.json records SHA256/bytes for every payload. Verification checks purpose/schema, required files, unique names, path allowlist, entry/size bounds, symlinks and inventory/hash agreement. This detects accidental corruption, not malicious reauthoring. Dependencies are installed from locks after extraction; no API/UI contract or model configuration changes. Fresh extracted code was tested through both fixture profiles, and final executable/fixture/lock identities match that tested copy.

## 32. React presentation primitives and design boundary — 2026-09-30

The user-requested redesign retains the one-page React/Vite architecture and existing request/state/persistence behavior. frontend/DESIGN.md owns visual tokens. src/ui.jsx shares Button, Field, SectionHeading, Notice, Metrics, DataTable and Timestamp across the existing main, PaperLedger and Monitoring modules. These are presentation primitives: date/currency/percent/count formatting only, never allocation, selection, reconciliation or API payload arithmetic. Original ISO values remain in date options/time attributes and exact archived JSON remains accessible.

Field supplies names/labels/inline errors; native invalid events reveal closed required sections. Error summaries and skip links provide focus targets. Edited unsaved policy uses a cleanup-managed beforeunload listener; successful run creation clears that dirty flag. The pause control is offered only for a busy continuable run, avoiding a click during new-run creation without changing execution logic. Scoped table headers/captions and keyboard-focusable horizontal regions preserve complete ledger values at narrow sizes. The light-dominant design, dark context tile and fixed color/radius/type tokens follow DESIGN.md; no external font or new dependency. API contracts, root URL, backend, data and domain behavior are unchanged.

## 33. Demo package refresh — 2026-10-01

The fixed distribution list now also includes demo/report.md, evidence/m5_3_refresh_verification.json, frontend/DESIGN.md and frontend/design-audit.cjs. This preserves the current React design reference and makes the existing optional formatting script callable after extraction. Runtime exclusions, manifest schema and application interfaces are unchanged. Historical and current verification records remain separately dated.

