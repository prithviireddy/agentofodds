# Agent of Odds — Project Documentation

Last updated: 2026-09-30  
Documentation version: 1.1  
Stage: M0–M5.3 complete at recorded proof/fixture scopes; separately requested UI.1 React redesign complete. Current frontend follows frontend/DESIGN.md. The appended sections and demo/README.md record current functionality and historical proofs; independent financial/model-quality validation remains outstanding.

## 1. Purpose and document ownership

This is the living reference for the multi-agent financial research and portfolio optimisation project. It consolidates the discussion, including scope, ideas, data, workflow, implementation proposals, cost assumptions, evaluation, and open questions.

`documentation.md` describes the current project state. `changes.md` records significant decisions, revisions, implementation changes, and verification evidence. Update both when project work changes the design or implementation. Preserve existing file identities rather than creating differently named copies. This is a maintenance convention, not an unattended background process.

Status vocabulary:
- **Agreed:** explicitly accepted direction or user requirement.
- **Proposed:** recommendation awaiting detailed design or validation.
- **Unverified:** access, performance, pricing applicability, or behaviour not tested for this project.
- **Implemented:** code exists and supporting verification is recorded. Nothing in this document should be interpreted as implemented unless labelled accordingly.

### Portable context pack (v0.2)

The user requested portable context for other coding tools and a modular implementation. Added `README.md` (entry point), `AGENTS.md` (contributor rules), `architecture.md` (proposed module boundaries), `tasks.md` (acceptance checklist), and `handoff.md` (current checkpoint). These supplement this main reference and `changes.md`; they do not replace them.

Use a modular monolith with provider adapters, typed contracts, fixture/live/historical/replay modes, and domain calculations independent of the LLM framework. These are implementation proposals, not completed code. At meaningful milestones update the affected specification, task status, change log, and handoff together. Keep code, lockfiles, permitted data snapshots, prompt/config versions, and experiment manifests under user-controlled backup when they exist. The documentation archive is a dated snapshot; there is no automatic synchronisation.

## 2. Project definition

Build an evidence-backed financial research platform that uses specialist AI agents to analyse companies, uses mathematical optimisation to calculate constrained portfolio allocations, and explains and evaluates those proposals through historical analysis and paper tracking.

The product connects company research to an inspectable portfolio decision. It should answer:
1. Which companies merit consideration, and why?
2. Which sources support each finding?
3. What risks, missing evidence, and disagreements remain?
4. How should simulated capital be allocated under an explicit policy?
5. How does the proposal compare with simpler alternatives?
6. What changed since the previous review?

The project does not assume that additional agents improve investment returns. Their value must be measured against simpler systems.

## 3. User requirements and constraints

### Agreed direction

- A college major project and a learning project for GenAI and LangGraph.
- Multi-agent research plus mathematical portfolio construction.
- Prefer free resources and aim for zero additional expenditure.
- Use AI coding tools heavily, while verifying calculations and system behaviour.
- Choose the market with easier data access and implementation; US equities were selected as the initial design direction.
- Simulated portfolios and paper tracking; real-money execution is outside version 1.
- Preserve project context across the seven maintained Markdown files listed in README.md. This supersedes the original two-file requirement; each file has a defined owner role.
- Give direct assessments of limitations; do not present speculative capabilities as working features.

### Proposed operating scope

- One local user or a small demonstration audience.
- Develop with five companies; expand to approximately 20 across multiple sectors after the end-to-end path works.
- The company count must be configurable, not hardcoded as a system limit.
- Daily price data, with scheduled monthly research/rebalancing reviews and optional user-triggered reviews.
- USD simulated capital initially; currency conversion is not part of the core.
- Long-only holdings and no leverage as the initial design. Exact cash treatment and exposure constraints remain open.
- Maintain a broader universe of hundreds of companies later, with numerical screening before selective deep research.

Terminology: the **investment universe** is the set of eligible companies; the **investment horizon** is the intended investment duration.

## 4. Version 1 features and boundaries

| Feature | Intended behaviour | Status |
| --- | --- | --- |
| Preference capture | Amount, horizon, risk preferences, exclusions, exposure limits | Planned |
| Investment policy | Explicit objective and constraints, visible to the user | Planned |
| Data ingestion | Dated prices, financial facts, filings, and available news | Planned; access tests pending |
| Document retrieval | Company/date/topic-aware retrieval with source references | Planned |
| Specialist analysis | Fundamental, news, and quantitative reports | Planned |
| Research synthesis | Shortlist rationale, disagreements, missing evidence | Planned |
| Optimisation | Code calculates weights under explicit constraints | Planned |
| Validation | Numerical checks plus evidence review | Planned |
| Objective review | Flag limitations in the chosen objective | Proposed for initial version |
| Dashboard | Run status, reports, allocations, sources, risk and performance | Planned |
| Historical evaluation | Baselines, costs, data cutoffs, recorded assumptions | Planned |
| Paper portfolio | Virtual cash/holdings and valuation history | Planned |
| Monitoring | Daily numerical valuation, periodic research refresh | Planned |
| Replay mode | Clearly labelled reproduction of saved demonstration results | Proposed |

Deferred: automatic real trading, intraday strategies, reinforcement learning, model fine-tuning, broad multi-asset coverage, unrestricted public usage, and automatic objective switching.

## 5. End-to-end workflow

### Step 1 — Collect preferences

Accept simulated capital, investment horizon, risk preferences, and optional exclusions. Validate fields. A qualitative label such as moderate risk is insufficient on its own; show the concrete settings it maps to.

### Step 2 — Create the investment policy

Store the objective, eligible universe, concentration limits, cash rules, review schedule, and policy version. The user confirms the policy before portfolio generation. Distinguish hard constraints from preferences.

### Step 3 — Collect and prepare data

Fetch data through APIs or permitted source access, normalise units and identifiers, retain availability timestamps, and cache permitted responses. Prefer structured financial facts for arithmetic and source documents for narrative evidence.

For a large universe, apply a documented numerical screening process before deep research. Do not hide exclusions or silently treat missing data as a negative investment signal.

### Step 4 — Provide evidence and tools

Text retrieval supports documents and news. Numerical tools provide prices, ratios, risk measures, and calculations directly. Not every dataset belongs in a vector database.

Agents may make bounded follow-up retrieval calls during analysis. A single initial retrieval followed by a fixed prompt is a useful baseline, but should not be described as autonomous retrieval planning.

### Step 5 — Run specialist research

Fundamental, news, and quantitative roles produce structured findings with evidence, dates, limitations, and concise rationale. Independent analyses precede synthesis to reduce copying of conclusions. Agreement does not establish correctness.

### Step 6 — Select candidates and optimise

A versioned explicit eligibility rule now converts specialist reports into candidates (M3.2 details below). Thresholds and assessment allowlists are caller-supplied experiment inputs. Selection must still be evaluated separately from allocation; no ranking or investment advantage is established.

A Python optimiser calculates weights. Initial proposal: minimise estimated portfolio variance subject to the policy constraints. Define the historical lookback, covariance estimator, and numerical tolerances before implementation. The objective is estimated-risk reduction, not a promise of maximum future returns.

### Step 7 — Validate and review

- Code checks budget/weight totals, long-only rules, exposures, missing inputs, and solver status.
- An evidence critic checks whether claims and explanations are supported.
- An objective review checks what the active objective may overlook.

Start with one critic pass and at most one revision. Route a failed check to the responsible stage. If no feasible solution exists, return that status and an explanation; do not quietly relax user constraints or force agreement.

### Step 8 — Produce the report and approve tracking

Report the policy, allocations, research rationale, sources, estimated risks, unresolved issues, comparison results, data cutoff, and limitations. User approval starts or changes the paper portfolio. A proposed allocation is not a trade execution.

### Step 9 — Monitor

Update portfolio values using code and fresh prices. Re-run research only for relevant new evidence or a scheduled review. Proposed rebalancing returns through validation and user approval. Changes to the investment policy need explicit approval.

## 6. Logical components and contracts

These are proposed interfaces, not existing endpoints or schemas.

| Component | Receives | Produces | Boundary |
| --- | --- | --- | --- |
| Data service | Symbols, fields, cutoff, freshness policy | Normalised data and provenance | Handles fetching and cache access centrally |
| Retriever | Company, question, cutoff | Evidence passages and source IDs | Enforces company/date filters |
| Fundamental analyst | Financial facts and filing tools | Business strengths, risks, supported findings | Never invents missing financial figures |
| News analyst | Dated news/release tools | Events and possible implications | Separates fact from interpretation |
| Quantitative analyst | Price/calculation tools | Numerical measures and interpretation | Arithmetic performed by code |
| Synthesis stage | Specialist findings | Candidate rationale and disagreements | No automatic requirement for consensus |
| Optimiser | Eligible assets, numerical inputs, policy | Weights, status, objective value | Does not accept arbitrary LLM-generated weights |
| Validator | Portfolio, policy, evidence | Pass/fail findings and revision targets | Hard constraints enforced by code |
| Objective reviewer | Policy and diagnostic results | Suitability concerns and alternatives | Initially cannot change policy autonomously |
| Report generator | Validated outputs | User-readable report | Must not add unsupported facts |

Use one model provider initially with different role prompts, tools, and state. Multiple agents do not require separate subscriptions or models.

## 7. Data architecture and scaling

### API access and caching

APIs and downloaded/stored data are complementary. An API fetches information; a local cache avoids redundant requests and preserves reproducible inputs.

Access pattern: check cache freshness and cutoff suitability; fetch missing or outdated information; validate and store it; return it with provenance. Respect source retention and redistribution terms.

| Data | Refresh strategy |
| --- | --- |
| Daily prices | Initial history fetch, then incremental updates; account for corrections/corporate actions |
| Financial statements | New filing or amendment |
| Filings and embeddings | Index needed documents once; version changes |
| News | Incremental collection, publication-time retention, deduplication |
| Research reports | Reuse only when evidence, prompts, model, and settings remain compatible |
| Allocations | Recompute for policy/input changes without repeating unchanged research |

Example scale calculation: 500 companies × 252 sessions × 5 years is approximately 630,000 daily price records. Daily structured data is manageable locally; exhaustive document analysis and repeated LLM calls are the larger concern.

Proposed scaling path: screen 500 companies numerically, shortlist approximately 30–50, perform deeper research, then optimise. These are illustrative counts, not validated defaults. Screening can exclude valuable candidates and requires baseline testing.

### Candidate sources

- SEC EDGAR: filing history, source filings, structured XBRL facts; public APIs without API keys. Requires identifier mapping, rate-limit compliance, unit/period normalisation, and filing-version handling.
- Alpaca Basic: candidate daily/historical price provider. Official documentation reviewed in the discussion lists free access, 200 historical requests/minute, historical coverage since 2016, and limited real-time IEX data. Exact accessible historical feeds must be tested with the project account. Its 30-symbol WebSocket subscription limit is not a 30-company database limit.
- Alpaca/Benzinga historical news: candidate, not verified as a free and sufficient source for this project.
- Company investor-relations releases: supplemental dated material where accessible and permitted; not equivalent to comprehensive independent news.
- Paper execution: start with our own ledger; external paper-trading integration is optional.

Do not promise comprehensive historical news or production-grade real-time coverage at zero cost.

### Proposed records

Companies/instruments; raw source metadata; daily price bars; financial facts with units and periods; document versions and chunks; news/events; investment policies; workflow runs; research reports; evidence references; portfolio proposals; validation findings; approvals; paper holdings/cash/transactions; valuation history; cost and error logs.

Preserve source publication/filing time, retrieval time, effective period, provider, and version where available. A financial period ending before a decision does not mean its report was public by that decision.

## 8. Proposed implementation stack

| Layer | Initial proposal |
| --- | --- |
| Application | Python FastAPI backend and React/Vite frontend, local development |
| Workflow | LangGraph executed locally |
| Structured storage | Local PostgreSQL |
| Documents | Local files with database metadata |
| Retrieval | Local Chroma plus Sentence Transformers embeddings; keyword/hybrid retrieval can be evaluated later |
| Numerical processing | pandas/NumPy and explicit financial calculations |
| Optimisation | CVXPY with an appropriate open-source solver |
| LLM | Gemini free-tier model available to the account; pin the actual model per experiment |
| Observability | Local logs and database run records |
| Scheduling | Local scheduler; only runs while the host is available |
| Optional sharing | Lightweight Streamlit demo; not a presumed hosting solution for the entire React/FastAPI stack |

The libraries can be used without paying for hosted orchestration, vector storage, or tracing products. No training infrastructure or rented GPU is required. Final dependency versions, model choice, API contracts, and deployment are not selected yet.

### LangGraph design principles

Use a controlled overall workflow, with bounded tool choice inside research nodes. Shared state should carry run ID, as-of cutoff, policy version, candidate set, evidence IDs, findings, portfolio, review outcomes, retry counters, and usage. Prefer structured outputs validated at boundaries. Implement checkpoints/resume, bounded retries/backoff, and quota-aware concurrency. A hosted agent platform is optional.

## 9. Research grounding and objective review

### AlphaAgents

Reference: AlphaAgents: Large Language Model based Multi-Agents for Equity Portfolio Constructions, arXiv:2508.11152.

The uploaded paper describes fundamental, sentiment, and valuation roles, financial-report RAG, and agent collaboration/debate. Its conclusion distinguishes its stock-selection focus from a complete portfolio optimisation engine. RAG alone is therefore not a novel difference for this project. Its reported results do not establish universal superiority of multi-agent analysis.

### Agentic Asset Allocation and the Illusion of Evaluation

Reference: Peter Kahl, 2026, DOI 10.5281/zenodo.19572052. The supplied version is marked submitted for peer review.

Central concern: improving search and coordination under a shared objective does not establish that the objective is appropriate. The paper proposes bounded, auditable selection among alternative objective specifications. Its simulation findings are model-specific and do not show that every multi-agent financial system fails.

Version 1 interpretation: explicitly represent the objective and flag its limitations. Mathematical optimisation and a critic alone do not solve objective misspecification.

Future experiment: compare a fixed variance-based objective with an alternative such as CVaR, which emphasises losses in adverse scenarios, and then evaluate a predefined, bounded switching mechanism. Merely adjusting a risk parameter is not necessarily a change in objective form. Any switch needs logged triggers, candidate objectives, transition rules, frequency limits, and policy authorisation. This remains a hypothesis, not a validated improvement.

### Research notes

`research-doc1(1).txt` is a broad ideation summary, not independently verified evidence for every cited paper or performance claim. Its claims that additional agents improve outcomes must be tested rather than copied into the project conclusions.

## 10. Evaluation and correctness

### Baselines

1. Equal weighting over a clearly specified comparable universe.
2. The same optimiser without agent-driven selection.
3. Single-agent research with comparable evidence and budget.
4. Multi-agent research with fixed objective.
5. Later: objective-review or objective-switching variants.

Keep dates, data access, transaction-cost assumptions, constraints, and comparison conventions explicit. Report selection effects separately from allocation effects. Record universe membership and exclusions; choosing today's survivors for historical tests creates selection/survivorship bias.

### Metrics

- Financial: cumulative and annualised return, volatility, Sharpe ratio with declared risk-free-rate convention, maximum drawdown, turnover, concentration, and costs.
- Research: factual accuracy on a manually checked sample, citation support, retrieval relevance, missing-evidence handling, and numerical consistency.
- Engineering: latency, calls/tokens, estimated cost, failures, retries, and reproducibility.
- Coordination: unsupported agreement, unresolved disagreement, and incremental benefit versus a single agent at comparable resources.

Historical evaluation must enforce information-availability cutoffs, prevent future-price access, handle corporate actions and dividend conventions consistently, avoid same-bar execution assumptions, and model declared costs/slippage. Restricting retrieved data does not eliminate future information memorised by an LLM. State that limitation and use forward paper tracking as additional evidence.

A one-year, monthly experiment is a starter evaluation, not proof of general performance. Predefine development/test periods and avoid tuning using the held-out results. Saved outputs may be replayed for a demo only when clearly labelled.

## 11. Costs and budget controls

### Budget policy

Target zero additional cash expenditure using existing hardware, free software, free inference quotas, and existing/student coding-tool access. Electricity, internet, and already-paid subscriptions are excluded from this incremental budget. Free quotas do not guarantee unlimited capacity or availability.

Optional inference reserve discussed: INR 500–1,000 for the initial build, not a purchase authorisation or a guarantee. No paid fallback, top-up, or new subscription should activate automatically.

### Coding versus application inference

Coding tools help implement the application. Runtime agents use their own configured inference provider and quota. An existing ChatGPT Plus subscription can provide included Codex usage subject to limits, but does not constitute an OpenAI API-token budget. GitHub Copilot Student is a candidate free benefit after verification and activation, subject to its plan limits. No additional coding subscription is required by the current design.

### Snapshot estimates from the 2026-09-20 discussion

Prices and entitlements below were checked against provider documentation during planning; they are not account-tested commitments and must be rechecked before enabling billing.

| Reference model | Input USD / million tokens | Output USD / million tokens |
| --- | ---: | ---: |
| Gemini 2.5 Flash-Lite | 0.10 | 0.40 |
| Gemini 2.5 Flash | 0.30 | 2.50 |

Output includes billable thinking tokens. Models are pricing references, not final dependencies. Formula: input tokens / 1,000,000 × input rate + billable output tokens / 1,000,000 × output rate, plus any separately billed tools/services.

Assumption: 4,000 input and 800 billable output tokens per call.

| Illustrative workload | Calls | Flash-Lite USD | Flash USD |
| --- | ---: | ---: | ---: |
| Initial full-run planning envelope | 60 | 0.0432 | 0.192 |
| 100 such runs | 6,000 | 4.32 | 19.20 |
| 12 monthly such runs | 720 | 0.5184 | 2.304 |
| Deep research on 30 companies at three calls each | 90 | 0.0648 | 0.288 |
| Deep research on 500 companies at three calls each | 1,500 | 1.08 | 4.80 |
| Same 500-company research daily for 30 days | 45,000 | 32.40 | 144.00 |

The original 60-call envelope was an approximate total-run budget; it is NOT equivalent to three calls for each of 20 companies plus extra synthesis and review. The per-company rows exclude those shared steps. Use measured traces to replace both assumptions. Costs exclude taxes, FX fees, extra search, retries, longer prompts, and additional reasoning. INR conversions in discussion assumed INR 90/USD for budgeting, not a live exchange rate. Approximately 2× headroom was suggested, but actual use can exceed it.

Free-tier execution costs zero within available quotas but may require spreading work across days. Provider limits can be per project, not per API key. Additional keys are not a scaling solution. Alpaca's reviewed paid market-data plan was USD 99/month; hundreds of daily-data symbols alone do not establish a need for it.

### Cost controls to implement

Reuse unchanged research; cache evidence and embeddings; refresh incrementally; cap context and output; avoid LLM calls for arithmetic or daily valuation; bound review loops; queue quota-limited calls; use recorded responses during UI development; keep provider billing off by default; enforce an application budget before submitting calls. Provider budget alerts alone should not be assumed to be hard spending stops.

## 12. Delivery plan and learning path

Estimated effort discussed: 6–8 weeks at roughly 10–15 hours/week. This is a planning range, not a deadline; data quality and evaluation may require more work.

| Milestone | Deliverable | Exit evidence |
| --- | --- | --- |
| M0: access proof | Five-company data and one model response | Actual API entitlements, dates, quotas, and sample outputs recorded |
| M1: numerical baseline | Prices, policy, optimiser, basic evaluator | Valid weights, constraint checks, cost/dividend conventions |
| M2: grounded research | Retrieval and one research agent | Checked citations and structured output on sample questions |
| M3: orchestration | Specialist roles, synthesis, critic, resume | Bounded runs, failure handling, measured usage |
| M4: product flow | Dashboard, reports, approvals, paper ledger | One complete user journey and ledger reconciliation |
| M5: evaluation/demo | 20-company run and baseline comparisons | Reproducible experiment records and clearly labelled replay |
| Later | Larger universe and objective-layer experiments | Separate benchmarks showing whether added complexity helps |

Learning order: LLM requests and structured outputs; tool calling; document chunking/embeddings/retrieval; LangGraph state/nodes/edges/routing/checkpoints; controlled multi-agent coordination; optimisation basics; point-in-time evaluation and instrumentation.

Use AI coding tools module by module with clear inputs, outputs, acceptance criteria, and small reviewable changes. Verify financial calculations, information cutoffs, and failure handling rather than accepting generated code solely because it runs.

## 13. Open decisions and risks

- Development companies selected below; formal sector taxonomy and historical membership policy remain open.
- Initial risk profiles, objective, cash handling, constraint values, and feasible fallback behaviour.
- Selection threshold calibration and evaluation; no validated weighting of agent opinions or investment benefit exists yet.
- Price feed/account entitlement, adjustment conventions, and API reliability.
- News access, retention terms, coverage, and historical availability.
- Final model, account-specific free quotas, context budgets, and actual run cost.
- Retrieval model/chunking and table/number preservation.
- Authentication and hosting if access expands beyond a local demonstration.
- Backtest dates, execution timing, transaction costs, repeated-run count, and test split.
- Whether objective comparison is a stretch feature or required academic contribution.

Important limitations: agents may share model biases; consensus is not evidence; estimates can be unstable; an optimiser cannot repair poor data or unsuitable objectives; an all-equity design may be unsuitable for some requested profiles and should return an explicit limitation instead of mislabelling risk.

## 14. Current implementation inventory

Completed: consolidated documentation, change log, portable README, coding-assistant instructions, architecture blueprint, build checklist, and handoff checkpoint.

Implemented and verified on 2026-09-20: local Git repository, uv project metadata and lockfile, Python 3.14.3 offline bootstrap, placeholder environment configuration and ignore rules. Use uv exclusively for Python dependency/environment management. No third-party runtime dependencies yet. Maintained workspace: `C:/codeblender/agentic/agentofodds`; Desktop source files remain a snapshot.

Not completed or verified: financial application features, API credentials/access tests, data pipeline, retrieval index, agents, optimiser, dashboard, historical experiment, paper ledger, deployment, measured quality, measured cost, and performance results.

Next concrete milestone: M0, the five-company access and evidence proof, before committing to providers or spending.

## 15. References and source traceability

Project attachments reviewed during this conversation:
- `alpha_agents.pdf` — AlphaAgents.
- `illusion_of_asset_allocation(1).pdf` — objective-layer critique and proposal.
- `0fc6ef09-6bc0-4257-ad76-cb28a875436a.png` — original nine-stage methodology image visible in the conversation.
- `research-doc1(1).txt` — broad research/ideation notes.

External references checked during the planning discussion (2026-09-20):
- AlphaAgents: https://arxiv.org/abs/2508.11152
- Objective-layer paper: https://doi.org/10.5281/zenodo.19572052
- SEC APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- Alpaca data: https://docs.alpaca.markets/us/docs/about-market-data-api
- Alpaca news: https://docs.alpaca.markets/us/docs/historical-news-data
- Alpaca paper trading: https://docs.alpaca.markets/us/docs/paper-trading
- Gemini pricing: https://ai.google.dev/gemini-api/docs/pricing
- Gemini quotas: https://ai.google.dev/gemini-api/docs/rate-limits
- LangGraph concepts: https://docs.langchain.com/oss/python/langgraph/workflows-agents
- LangGraph source: https://github.com/langchain-ai/langgraph
- Chroma: https://github.com/chroma-core/chroma
- CVXPY: https://www.cvxpy.org/index.html
- Embedding model candidate: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- OpenAI coding plans: https://learn.chatgpt.com/docs/pricing
- Copilot Student: https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/enable-copilot/set-up-for-students
- Copilot plans: https://docs.github.com/en/copilot/get-started/plans
- Optional Streamlit hosting: https://docs.streamlit.io/deploy/streamlit-community-cloud

Use exact sources for factual claims; do not turn literature summaries or illustrative costs into experimental results.

## 16. Development universe and fixtures — 2026-09-20

Implemented configuration: `config/universe.toml`, schema v1, cutoff `2025-01-31T23:59:59Z`. MSFT/Microsoft (Technology), JPM/JPMorgan Chase (Financials), JNJ/Johnson & Johnson (Healthcare), XOM/Exxon Mobil (Energy), WMT/Walmart (Consumer staples). Labels are internal categories, not a licensed taxonomy. Selection exercises software/financial/healthcare/energy/retail cases; it is not an investment recommendation, representative benchmark, or point-in-time universe reconstruction. Official identifier mapping is part of upcoming live access verification.

`fixtures/prices.json` supplies two invented daily USD closes per company (January 30–31, 2025), synthetic availability timestamps, unique source IDs and artifact metadata. The fixture adapter enforces availability cutoff and validates price units, decimal strings, duplicates and timezone-aware timestamps. It surfaces missing symbols without substituting prices. No provider access or real historical performance is implied. Fixtures do not yet include fundamentals, filings, news or model responses.

Implemented CLI and 12 passing tests are recorded in tasks.md. No dependency changes or spending. Next: live data access proof; full policy, financial-data and evidence schemas remain pending.

## 17. SEC implementation checkpoint — 2026-09-21

Implemented a bounded, standard-library SEC JSON adapter and explicit probe. No dependency or spending changes. The default application remains offline. The probe will resolve ticker/CIK identities and select one USD Assets observation and recent filing metadata reference per company under the configured cutoff. Offline synthetic-response tests pass; these are not real provider evidence.

SEC_USER_AGENT is not configured, and the actual probe returns missing_configuration without calling SEC. A real application/contact identity must be supplied locally before live verification. No API key is required for these public data endpoints. Contact values stay out of Git and Markdown. SEC guidance checked on 2026-09-21: [API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [automated access guidance](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

The adapter uses conservative filing-date availability and excludes later filings for earlier periods. This does not eliminate snapshot corrections or establish historical membership. It does not yet fetch filing bodies, full financial statements, prices or news. Exact request limits, implemented interfaces and tests are recorded in architecture/tasks. M0 completion remains pending.

## 18. Local configuration correction — 2026-09-21

The explicit SEC probe now loads a project-root ignored `.env` file, while shell-provided environment variables take precedence. It has no third-party dotenv dependency. The documented file contains `SEC_USER_AGENT`, `ALPACA_API_KEY`, `ALPACA_SECRET_KEY` and `GEMINI_API_KEY` placeholders; these values are not loaded by the default offline application. Tests cover malformed entries and shell precedence.

A populated configuration was found in `.env.example` and immediately replaced with placeholders. This repository has no commits, but any provider credentials placed there must be considered exposed and rotated. The expected ignored `.env` does not exist at this checkpoint, so no live SEC call has been made.

## 19. Live SEC evidence — 2026-09-21

The bounded SEC probe ran successfully against public endpoints at 2026-09-21 06:33–06:34 UTC using a locally configured declared contact identity. It made 11 requests. The ticker-list response hash was `23e6c511f3fc1a41413803dc77c50cf080f82ed79ab13a049127a8dccb1dd7de`.

Configured CIKs were verified through CompanyFacts: MSFT 0000789019, JPM 0000019617, JNJ 0000200406, XOM 0000034088 and WMT 0000104169. Eligible Assets samples were found for all five, in USD with filing dates and source IDs recorded by the command. Examples: MSFT 2024-12-31 Assets USD 533,898,000,000 filed 2025-01-29; JPM 2024-09-30 Assets USD 4,210,048,000,000 filed 2024-10-30; XOM 2024-09-30 Assets USD 461,916,000,000 filed 2024-11-04. These are access-proof samples, not comparable valuation metrics or investment conclusions.

Recent filing metadata was retrieved for MSFT, JNJ, XOM and WMT. JPM had no qualifying filing in the returned `filings.recent` list, despite an eligible CompanyFacts value; historical submissions pages are unimplemented. Current SEC ticker output reports an unrelated CIK for `XOM`; explicit configured CIK 0000034088 was separately verified as Exxon Mobil Corporation. M0.3 stays in progress because live prices are not verified; M0.4 stays in progress because news/release coverage and JPM historical filing metadata remain unverified.
## 20. Live Alpaca daily-price evidence — 2026-09-21

M0.3 is complete. The read-only Alpaca Market Data probe made one request at 2026-09-21 06:39:43 UTC for MSFT, JPM, JNJ, XOM and WMT, daily bars from 2025-01-30 through 2025-01-31. Result: 10 bars, no missing symbols, `feed=iex`, `adjustment=all`, `timeframe=1Day`, response SHA-256 `88c210baecada24669e24a86ca7e5149d1bf3ebb56bec64354e3c247f7bf1df9`. The account key pair successfully authenticated; no trading endpoint or order was used.

Returned closes: MSFT 409.19/409.36; JPM 260.31/259.45; JNJ 145.97/145.33; XOM 103.64/100.97; WMT 97.08/96.59 for January 30/31 respectively. These values prove one provider response only. IEX is limited coverage, `adjustment=all` affects comparability, and returned timestamps are not historical availability times. No backtest or financial-performance claim follows.
## 21. Live filing and investor-relations evidence — 2026-09-21

M0.4 is complete. The explicit evidence probe ran at 2026-09-21 06:45 UTC and successfully retrieved two configured MSFT sources under the 2025-01-31 cutoff: SEC Form 10-Q filed January 29, 2025 at `https://www.sec.gov/Archives/edgar/data/789019/000095017025010491/msft-20241231.htm`, and Microsoft FY25 Q2 investor-relations release dated January 29, 2025 at `https://www.microsoft.com/en-us/investor/earnings/fy-2025-q2/press-release-webcast`.

Filing evidence: 6,297,529 bytes, visible-text length 310,183, title `10-Q`, SHA-256 `253a2c005df27df63ef3671e43b4bff0b976bb0049682d6d2f95c1c9308a8937`. Release evidence: 573,736 bytes, visible-text length 25,250, title `FY25 Q2 - Press Releases - Investor Relations - Microsoft`, SHA-256 `6768cb420f41e963abb23fe73f2b28a2d03191749770cddd8ded61af7b569651`. Documents were not persisted, only metadata/hashes.

This proves a dated filing and company release are accessible. It does not prove comprehensive, independent or historical news coverage; exact release dissemination time is unavailable. The next unblocked M0 task is M0.5: one schema-validated model response.
## 22. Gemini M0.5 access-proof status — 2026-09-21

M0.5 is BLOCKED on provider availability. A standard-library, one-call Gemini client and strict JSON validation are implemented and 44 offline tests pass across the project. The proof prompt contains only two verified MSFT source IDs, asks for `insufficient_evidence`, and prohibits investment conclusions or unsupported facts. It uses no tools, no document body, no web search, temperature 0 and a 256-output-token cap.

The local API key successfully listed supported generation models. Attempts with `gemini-2.5-flash-lite` and `gemini-2.5-flash` returned HTTP 404; the provider response said 2.5 Flash is unavailable to new users and recommended `gemini-3.6-flash`. That configured model returned HTTP 503 and no response payload or usage data. The client returned `awaiting_quota`, made no retry or paid fallback, and recorded no model result. Model identity, prompt version and fixed limits are in `config/model.toml`.

A later deliberate rerun can complete M0.5 when the provider is available. Passing the schema test will still not establish that future research claims are factually supported; that requires M2 evidence retrieval and human checking.
## 23. M1.1 implementation — explicit policy and numerical inputs

M1.1 is complete, independent of the blocked Gemini proof. Implemented `InvestmentPolicy` and `PriceInput` domain contracts with no third-party dependencies. The policy contract enforces explicit values for cutoff, symbol universe, capital, USD currency, minimum-variance objective, minimum/maximum asset and cash weights, and review frequency. It rejects impossible aggregate constraints before an optimiser exists.

The numerical-input contract captures provider, feed, adjustment, currency, retrieval timestamp, source hash, coverage status, missing symbols and availability status. It makes a point-in-time eligibility decision only when availability is verified. This intentionally prevents the live Alpaca proof from becoming a backtest input merely because it returned historical-looking bars.

Tests include feasible and infeasible policies, missing/incompatible data provenance, coverage mismatch, timezone requirements and non-hardcoded universe size. The sample policy inside tests is not a selected investor policy, product default or allocation. M1.2 remains next; no optimiser, covariance estimator, return calculation or policy persistence has been implemented.
## 24. M1.2 numerical baseline — 2026-09-21

M1.2 is complete. Added NumPy 2.5.3 through uv for local matrix calculations. The numerical core is independent of Gemini, LangGraph, SEC and Alpaca SDKs. It calculates aligned simple close-to-close returns, sample covariance with Bessel’s correction, validates symmetry/positive semidefiniteness, and solves a long-only bounded minimum-variance allocation with a transparent projected-gradient algorithm.

Conventions are explicit: at least three aligned sessions create at least two returns; inputs must have verified point-in-time availability; objective is `w'Σw`; no leverage; asset bounds are uniform; cash has zero variance and is assigned at the maximum policy allowance before asset optimisation. This cash convention is a baseline assumption and appears in diagnostics. It is not a selected risk profile, return forecast or financial recommendation.

Known analytical tests passed: a diagonal covariance `[1, 4]` produces 0.8/0.2 with zero cash; allowing 0.1 cash produces 0.72/0.18/0.1. Bound enforcement, infeasible policy outcomes, non-symmetric/non-PSD covariance and short/unverified histories are tested. No live data has sufficient verified historical availability for a portfolio result, so no real allocation/backtest was produced.

## 25. M1.3 basic evaluation — 2026-09-26

M1.3 is complete as an offline evaluation primitive. An evaluation plan now records a timezone-aware decision cutoff, next-session-close execution, a later close valuation, explicit one-way transaction cost basis points, and a valuation convention that excludes dividends. The evaluator requires the policy cutoff to equal the decision timestamp and rejects same-day execution, missing prices, unverified availability, and prices that were not available by the evaluation cutoff.

The equal-weight comparator uses the same investable symbols, asset bounds and maximum allowed cash as minimum variance. Both strategies are valued over identical dates and charged the same declared cost. Results separately record gross return, normalized transaction cost, net return and diagnostics; the comparison reports the net-return difference. Zero cost is allowed only when explicitly supplied, rather than being an implicit default.

This implementation proves timing and comparison mechanics with synthetic inputs. It is not a performance result or complete backtest. It currently excludes dividends, taxes, spread/slippage beyond the declared basis-point charge, trading-calendar validation, partial fills, corporate-action processing and rolling rebalancing. Live Alpaca proof bars remain excluded because historical availability is not verified.

## 26. M2.1 local evidence index — 2026-09-26

M2.1 is complete. The project now converts evidence documents into deterministic overlapping chunks and records the originating source ID, source SHA-256 version, company, source type, publication time and ordinal on every chunk. The local JSON index can be rebuilt and loaded without a hosted database. It rejects duplicate source IDs and source-version mismatches.

Retrieval uses a bounded TF-IDF cosine baseline. Company and publication-date constraints are applied before ranking, preventing a relevant-looking chunk from an excluded company or future publication from entering results. This is a transparent lexical baseline, not true embedding-based semantic search. It costs nothing to run and gives us a benchmark before deciding whether local Sentence Transformers and a vector store add enough retrieval quality to justify their complexity.

The live index proof fetched the same bounded Microsoft sources established in M0.4 and created 313 chunks. A query for cloud revenue and operating income, filtered to MSFT and the configured cutoff, returned three source-version-linked hits. The generated index lives in ignored `data/evidence_index.json`; Git keeps the implementation and tests, not the retrieved document corpus.

Current coverage is too narrow for company research: one Microsoft filing and one company-issued release. M2.2 must surface that missing coverage instead of pretending the index represents all five companies. It also remains blocked until M0.5 produces one successful schema-validated model response.

## 27. M2.2 grounded fundamental research — progress 2026-09-26

The provider-independent research role is implemented. A request declares one symbol, cutoff, one to four research questions and a bounded result count. It searches only that company’s evidence published by the cutoff, deduplicates chunks, constructs a bounded prompt, and makes at most one model request. If no evidence exists, it returns `insufficient_evidence` without consuming model quota.

Every accepted finding must contain a nonempty claim, one qualitative assessment and one or more chunk IDs from the exact retrieved set. A model cannot introduce an unknown citation. Reports retain the retrieved evidence references, prompt version, safe model metadata, query trace and limitations. Evidence text is labelled untrusted and cannot select tools or destinations.

The runnable configuration currently asks MSFT questions about cloud/operating performance, infrastructure investment and business risks. This is a development proof, not a comprehensive analyst methodology. The local corpus contains only two Microsoft sources, so requests for other development companies correctly return missing evidence.

One deliberate M0.5 retry on 2026-09-26 reached Gemini, but the response failed the existing structured-output parser. This differs from the earlier HTTP 503: service access occurred, but no valid response was accepted. No usage or substantive finding is claimed, and no automatic second request was made. M2.2 remains in progress until this response path is diagnosed and one live report is manually checked against its cited passages.

## 28. M0.5 and M2.2 completed — 2026-09-26

Safe response diagnostics showed the failed Gemini call ended with `MAX_TOKENS`. Gemini counted thought tokens inside the 256-token output cap, leaving seven visible candidate tokens and truncated JSON. The adapter now requests the officially supported `minimal` thinking level for Gemini 3.6 Flash. It retains bounded temperature/output settings and records only safe failure shape, hashes, finish reasons and usage.

The corrected M0.5 call returned the required `insufficient_evidence` result because only source metadata—not passages—was supplied. This is the intended behavior. Model: `gemini-3.6-flash`; prompt/candidate/total tokens: 212/174/386; no paid fallback or tool call.

The live fundamental role then searched the two-source MSFT index with three questions and returned three accepted findings: quarterly revenue and net-income results, the reported AI annual revenue run rate, and expected capital-expenditure growth for cloud/AI infrastructure. Each claim cited only retrieved chunk IDs. Manual review confirmed the numeric statements in the cited investor release and the capital-expenditure statement in the cited 10-Q passage.

This single checked sample completes M2.2’s engineering gate. It does not show that the company is attractive, that two sources are complete, or that future model reports will be accurate. Four development companies still have no indexed research documents, and all generated claims require citation validation plus sampled human review.

## M3.1 implemented specialist scope — 2026-09-29

Separate news and quantitative roles now have fixture-backed verification. News reports distinguish source-reported events from uncertain implications, retain dated citations and always expose incomplete coverage and unverified historical availability. Company releases are not treated as independent news. The quantitative role computes descriptive price statistics in domain code without an LLM, with explicit freshness, cutoff, provenance, units and conventions. These measures are historical observations, not return predictions, candidate-selection rules or portfolio percentages.

The proof uses inline synthetic fixtures and a fake model; no live M3 model or news check was run. Nine new tests and all 88 offline tests pass. M3.2 remains the next task: explicit candidate selection and exclusions before mathematical allocation.

## M3.2 implemented selection scope — 2026-09-29

Candidate selection now requires explicit exclusions, per-role assessment allowlists, evidence/price freshness, minimum numerical observations, an unannualised volatility ceiling and minimum candidate count. Both fundamental and news reports must pass; quantitative measures come from code. Every finding and cited source must meet the configured gates. All eligible companies are retained without ranking. These are configurable engineering rules, not accepted user risk preferences or empirically validated investment filters.

Each decision preserves exclusion reasons, citations and limitations. Missing, stale, provider-failed or invalid reports exclude affected candidates. Too few candidates or infeasible unchanged investment bounds yields no actionable set; constraints are never relaxed. Seven new fixture tests and all 95 offline tests pass. M3.3 orchestration/review remains next.
## M3.3 implemented workflow scope — 2026-09-29

The local workflow now runs research through selection, numerical allocation and bounded review, with persistent call/query/output budgets, one-at-a-time execution and atomic checkpoints. Resume reuses finished stages only when inputs/configuration match. Quota/provider failures stop for explicit retry; ambiguous interrupted calls remain reserved with unknown usage. Review allows one initial critic pass and at most one targeted revision plus verification pass. Numeric checks remain independent of the LLM. Oversized evidence review returns review_incomplete instead of approving partial coverage.

A five-company synthetic run passed using 10 fake role calls and one fake critic call. Twenty-one new workflow tests and all 116 offline tests pass. This is engineering proof, not measured live reliability, factual critic accuracy, model usage/cost or investment performance. Critic agreement is not human approval. The implemented executor is a sequential local state machine; no LangGraph dependency or distributed worker was added. Checkpoints should remain under ignored data/workflow_runs and are trusted local data; stale crash locks need operator recovery.

M3 is complete at the documented proof scope. Next is M4.1: UI for explicit user policy, run/review status, evidence, candidate reasons, allocation and structured failures, using fixture workflows by default. No live calls, public publishing, payment or trade are implied by that next task.
## M4.1 implemented UI scope — 2026-09-29

A responsive local fixture workspace now exposes explicit policy settings, selectable fixture companies, research/selection controls, run progress, pause/resume/retry, saved reports, cited passages and hashes, exclusions, usage and reviewed allocations. Demo values are labelled test inputs and loaded explicitly. All data and model/critic responses are synthetic. No actual investor policy is inferred or saved by default.

Reviewed allocation is available only after top-level success; rejected or incomplete runs cannot present diagnostic weights as an approved proposal. Saved reports can be reopened or downloaded as JSON. No human approval, paper ledger, real trade or live provider connection is offered yet. The fixed fixture cutoff, unknown usage and research/optimization limitations remain visible.

The initial implementation used plain HTML/CSS/JavaScript. This was corrected on September 30 at the user's explicit request: the frontend now uses React/Vite with a locked npm build, while the loopback Python API remains in place. React is required for subsequent frontend work; FastAPI remains a proposal. Six new API/service tests and all 122 offline tests pass. Headless Chromium verified the rendered success/failure/recovery flow, citations, saved reload, pause/resume and a 390px layout; desktop/mobile screenshots were inspected. M4.2 paper ledger and approval is next.

## React requirement correction — 2026-09-30

Historical milestone note; the later M4.2 section supersedes the no-ledger status below.

The user's intended frontend stack is React. Migrated the fixture workspace to React components/hooks and Vite, retaining the API and fixture flows. npm ci/build, 122 backend tests and browser smoke for both production and development proxy passed. The previous zero-frontend-dependency choice was an assistant deviation, not an accepted user requirement. Future work must preserve React. No new product scope, ledger, publishing or provider spending was introduced.

## M4.2 implemented opening paper portfolio — 2026-09-30

A successfully reviewed fixture proposal can now preview and explicitly approve a local opening paper portfolio from the React UI. Preview lists dated invented fills, fractional holdings, cash, fees, conventions and exact reconciliation. Approval is bound to the reviewed run/policy/allocation and fill identity, persists atomically, and repeating approval does not duplicate transactions. Reload reads the original receipt without model calls.

This is a historical synthetic replay, not forward performance evidence: research cutoff is January 31, 2025; invented fill date is February 3, 2025; actual approval time is recorded separately. Each run has an isolated funded book. Numerical calculations use exact fractions outside the LLM; displayed decimals are rounded only. Basis-point fees are explicit (fixture zero), slippage zero and taxes excluded. Corporate actions/dividends reject; rebalancing and withdrawals are unsupported. Policy constraints are never relaxed for execution. Monitoring and labelled valuation history remain M4.3.

Verification: 11 new ledger tests; 133 total offline tests; React build and browser approval/reload/rejection checks. Browser-generated approvals are test fixtures, not user investment approvals. No real orders, live provider access, spending or publication occurred.

## M4.3 implemented monitoring and labelled replay — 2026-09-30

Approved paper portfolios now support explicit price-only updates and saved valuation replay in React. Two invented historical price frames are separate from research and opening fills. Equity, P/L since funding and return use exact arithmetic with unchanged cash/shares; opening fees are included. Prices require complete coverage, valid provenance, availability by the selected historical cutoff and an explicit one-calendar-day age limit. Incompatible adjustments/currency and unsupported actions fail rather than alter the book.

Each run/date valuation persists its exact inputs, source hash, result and recording time atomically. Repeat updates replay the original snapshot; reload is read-only and saved replay remains available if the fixture is unavailable. Creation time is recorded for new runs, with unknown shown for older runs; original research cutoff, fill, approval and valuation times remain visible. No model calls or fresh research are involved.

Verified 146 offline tests, React build and the production browser flow including two dates, replay/reload and mobile layout. This is manual synthetic monitoring, not automatic daily execution, live prices or demonstrated investment performance. Rebalancing, corporate-action accounting and periodic research refresh remain outside this milestone. M5.1 is next.

## M5.1 implemented 20-company fixture proof — 2026-09-30

A separate, configurable twenty-company profile now covers MSFT, JPM, JNJ, XOM, WMT, AAPL, NVDA, GOOGL, AMZN, META, BAC, V, UNH, PFE, CVX, PG, KO, HD, CAT and NEE. These are illustrative software-test labels, not a verified historical universe or recommendation. All have synthetic prices, role evidence, fills and two valuation frames. The unchanged five-company profile remains the default; expanded state is isolated and React supports subsets.

The full twenty-company fixture run produces 40 research reports, selection/allocation, numerical/evidence reviews, paper approval and replay. Expanded execution limits are explicit; complete critic context measured 21,663 characters against a 64,000 cap. No claim/passage truncation is used. A decimal rounding defect found by strict ledger verification was corrected in versioned numerical code without relaxing constraints. Unfinished runs using the earlier solver require a new run; saved reports/books are not rewritten.

Evidence in evidence/m5_1_fixture_audit.json records 0.4010881s and 1.9336716s for the five/twenty workflow samples, including local checkpoint I/O. Scripted model calls were 11 and 41, reserved output tokens 8,448 and 31,488; actual inference tokens/cost remain unknown, with no external calls or provider spend. These are single local timings, not provider benchmarks. Shared invented passages, only three price sessions and repeated patterns make this unsuitable for investment evaluation. Live coverage remains unaudited for the expanded universe.

Verified 152 offline tests, React build and the full twenty-company browser flow including failures, approval, replay and mobile layout. M5.1 is complete at fixture scaling scope. M5.2 must define comparable baseline/single-agent/multi-agent experiments and held-out inputs before drawing conclusions; live performance is not established.

## M5.2 controlled synthetic comparisons — 2026-09-30

Implemented an offline comparison harness for equal weighting, numerical-only optimisation, one combined researcher per company and separate fundamental/news researchers. Both research designs retain the same critic, selection policy, optimiser and numerical validation; this isolates researcher decomposition rather than removing review from one side. They have equal aggregate output-token caps per company. Baselines bypass research selection, with candidate sets recorded explicitly.

The fixed plan uses the January 31, 2025 decision cutoff, February 3 fills, February 5 development valuation and a new February 14 synthetic holdout. All decisions are frozen before either evaluation-price split is loaded. The common 10 bps opening cost is charged in exact ledger arithmetic; slippage is zero, dividends/actions unsupported, taxes and liquidation costs excluded. No tuning/search was performed. The holdout is a code-isolation fixture, not independent financial validation.

All eight profile/variant combinations completed both splits. Every company remained eligible; combined/separate research allocations and returns exactly matched numerical-only allocation. Combined uses 6/21 scripted calls for five/twenty companies, versus 11/41 for separate roles. Reserved output limits are identical at 8,448/31,488. Actual inference usage/cost remain unknown, with no external calls/provider spend. No research-selection benefit, quality improvement, latency advantage or strategy winner is established.

`evidence/m5_2_comparison.md` is the readable result; JSON beside it archives complete inputs, hashes, reports, controls, traces and exact outcomes. Archive-only replay needs neither models nor current fixtures. Verification covers holdout noninterference, common costs/caps, citation validation, failure suppression, stable decision identities and corrupt-archive rejection. M5.2 is complete at offline experimental-harness scope; meaningful financial/model evaluation still requires independent evidence, richer data and authorized inference. M5.3 demonstration preparation is next.

## M5.3 reproducible college demonstration — 2026-09-30

The demo guide, approximately seven-minute presenter outline and Q&A explain the React research-to-simulation flow, both fixture universes, explicit paper approval, price-only replay and controlled comparisons. They distinguish earlier narrow live proofs from fully synthetic end-to-end results. The reproducible ZIP packages permitted source, locks, synthetic fixtures and recorded reports with a file inventory and hashes; credentials/environment files, raw live caches, runtime books and dependencies are excluded. Install dependencies before presenting; fixture execution needs no credentials/provider calls.

Verified from a fresh extraction on Windows: cached locked Python/npm installation, production React build, 168 tests, all eight archived comparisons and browser smoke for five/twenty companies through consent/approval, valuations/replay, recovery and mobile layout. An initial source-folder packaging omission was found, fixed and retested in a new extraction. Final code/fixture/configuration/lock hashes match the tested copy. See evidence/m5_3_verification.json for actual commands and limits. Cache-free setup on another machine and other operating systems were not verified.

M5.3 completes the planned proof milestones. Next practical step is presentation-machine rehearsal. Meaningful investment/model-quality evaluation still requires separately scoped independent inputs and authorized inference; scripted results, citations and critic agreement do not establish accuracy, suitability or superior returns. No new spend, live provider call, publication or real trade was performed.

## UI.1 existing frontend redesign — 2026-09-30

At the user's request, frontend/DESIGN.md is the primary visual system. The existing React workspace now uses white/parchment, near-black system typography, Action Blue, consistent spacing and restrained utility surfaces across configuration/saved runs, research/reviews/citations, paper approval/journal and historical replay. Installed Taste and Vercel guideline skills informed initial/final audits; marketing-page prescriptions were limited to applicable presentation concerns.

Reusable presentation primitives, native form validation/error focus, named/labeled inputs, skip/in-page links, keyboard-scrolling tables, 44px targets, responsive metric layouts, pending feedback and unsaved-policy warning improve usability. Original action names, consent, evidence, raw timestamps/exact archived values and root URL remain. Display formatting does not move numerical finance out of Python. No backend/API/auth/database, fixture, workflow or dependency change.

Verified build/format checks, 34 relevant regression tests, complete five/twenty Chromium browser flows and eight-width audits from 320 to 1920px. Record: evidence/frontend_redesign_audit.md. Other browsers, screen-reader devices, axe and Lighthouse/CWV scores were not verified. This redesign improves interface quality; the underlying server remains a local single-user fixture demo. M5.3's ZIP is historical until rebuilt; no publication, spending or real trading occurred.

## M5.3 current-interface package refresh — 2026-10-01

The October 1 ZIP includes the current React interface and concise demo/report.md, distinguishing recorded synthetic comparisons from narrow historical live proofs. See evidence/m5_3_refresh_verification.json for fresh cached setup, production build, 168 fixture tests, eight archive replay outcomes and both Chromium smoke profiles. Optional formatting failed on existing main.jsx; no UI source was changed. September 30 records remain historical. No provider calls, spending, publication or real trades; presentation-machine rehearsal and independent evaluation remain outstanding.

