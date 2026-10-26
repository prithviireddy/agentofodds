# Research and workflow

## Retrieval and specialist reports

[LocalEvidenceIndex](../../backend/app/retrieval/index.py) creates deterministic overlapping word chunks and a local JSON index. Exact company and inclusive publication-cutoff filters apply before TF-IDF cosine ranking. Source hashes bind citation versions. This is lexical retrieval, not semantic embeddings or autonomous retrieval planning.

[Fundamental research](../../backend/app/research/fundamental.py) accepts one company, cutoff, one to four unique queries and one to five hits per query. It deduplicates evidence, builds a prompt of at most 8,000 characters and makes at most one generation call. No eligible evidence returns `insufficient_evidence` without a model call. Output validates company, status, bounded findings, assessment, limitations and citations to actual prompt-visible passages. Prompt version is `fundamental-research-v2`; the older version string in the research TOML does not override the role's code constant.

[News research](../../backend/app/research/news.py) uses an explicit inclusive publication window, with investor-release/fixture source filtering before ranking. Findings separate source-reported events from uncertain interpretations. Company releases are not independent news. Prompt-visible citations and structured output are validated, with incomplete coverage and uncertain historical availability exposed.

[Quantitative research](../../backend/app/research/quantitative.py) calls domain calculations without an LLM. It validates complete price coverage, cutoff, provenance, observations and caller-supplied calendar-day freshness. It returns descriptive means, sample volatility/covariance and compounded return, not forecasts or allocation weights.

## Eligibility and allocation handoff

[SelectionPolicy](../../backend/app/domain/selection.py) requires exclusions, fundamental/news assessment allowlists, maximum cited-evidence and price ages, minimum return observations, a per-observation volatility ceiling and minimum candidate count. No thresholds are silently inferred from qualitative risk labels.

[select_candidates](../../backend/app/application/selection.py) requires both text roles and quantitative data to pass identity, cutoff, evidence and configured gates. Every consumed finding/citation must qualify. It retains all eligible companies in configured order, without ranking or model-generated scores; exclusions retain reasons and limitations. Explicitly excluded companies skip text research.

Too few candidates returns `insufficient_candidates`. Revalidating unchanged investment bounds against the remaining universe can return `infeasible`. Neither outcome yields an actionable candidate set. The downstream numerical stage recomputes covariance in candidate order. Selection input hashes provide traceability, not proof that the research is true.

## Sequential execution and limits

[run_workflow](../../backend/app/workflows/runner.py) executes quantitative validation → fundamental/news per company → eligibility → candidate-aligned allocation → numerical review → evidence critic. The caller supplies prices, evidence index, requests, configuration and model factory. The fixture UI supplies scripted responses and no live providers.

`WorkflowBudget` persists company/call/output/query/retry/review/revision bounds. Concurrency is one. Ordinary workflow model calls reserve 768 output tokens each, with 8,000-character researcher prompts. Critic context is a separate explicit cap. Calls/output reservations and content-free prompt hashes are saved before dispatch; retrieval reservations conservatively count declared queries. Ambiguous interrupted calls remain charged against the reservation budget. Known token fields are summed, unknown usage calls are counted, and cost remains null. Reservations are not measured usage or provider billing limits.

| Fixture profile | Companies allowed | Calls allowed | Reserved output ceiling | Retrieval queries | Critic characters |
| --- | ---: | ---: | ---: | ---: | ---: |
| Five | 5 | 15 | 11,520 | 20 | 8,000 |
| Twenty | 20 | 45 | 34,560 | 80 | 64,000 |

Both UI profiles permit one explicit retry per step, one critic round and zero revisions. The reusable executor allows at most one targeted revision and two critic rounds when the supplied budget permits both. These ceilings differ from actual calls used by successful fixtures and from the comparison harness's combined-research path.

## Review, checkpoint and resume

Numerical review checks symbols, finite values, totals, cash/asset bounds and variance independently of the critic. It surfaces minimum-variance limitations; it does not autonomously change the objective.

The evidence critic receives all selected claims and complete cited passages, deduplicated without losing coverage. If these do not fit, the workflow returns `review_incomplete`; it never approves a silently reduced subset. The critic can approve, reject or request a single allowlisted research-stage revision. Feedback is untrusted, capped at 400 characters and cannot choose tools/destinations. Revision plus evidence exceeding the researcher prompt cap fails validation. Earlier reports/reviews remain in stage history.

Resume requires matching policy, selection, prices, evidence, request, model, prompt, solver, workflow and budget identities. Finished stages are reused. Provider/quota failures stop for explicit retry; no automatic timer/backoff runs. A saved in-flight stage becomes interrupted, retains its reserved call and needs an explicit bounded retry. `max_steps` permits a cooperative stop at a checkpoint boundary. Lock, filesystem and corruption failures return `checkpoint_error`.

Only top-level workflow success exposes an actionable reviewed proposal. Critic approval is neither factual truth nor human paper approval. [The interface](06-interface.md) suppresses failed-run diagnostic allocations; [simulation](05-allocation-and-simulation.md) separately requires consent. Crash-lock recovery belongs to the [runbook](../runbooks/local-demo.md#recovery).
