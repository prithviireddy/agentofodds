# Instructions for contributors and coding assistants

## Project intent

Build Agent of Odds: evidence-backed company research, constrained mathematical portfolio allocation, and simulation. Student budget: zero additional spend by default. US equities initially; five-company development proof before approximately 20 companies. The universe must remain configurable.

## Starting work

1. Read `handoff.md`, then the requirements, architecture, tasks, and recent changes relevant to the requested work.
2. Inspect the actual source tree and Git status if a repository exists. Do not overwrite unrelated work.
3. Distinguish agreed requirements, proposals, implemented behaviour, and verified results.
4. Work on the requested task or the next unblocked task when the user asks to continue. Ask only when a missing decision materially blocks useful progress.
5. New user instructions govern current work. Do not treat these project notes as permission to spend, publish, or trade.

## Design rules

- Use uv for Python environment and dependency management: `uv sync --locked`, `uv run`, and `uv add`. Keep `pyproject.toml`, `uv.lock`, and `.python-version` current. Do not use `python -m venv` or pip-based setup. uv may manage its default `.venv` directory.

- Use a modular monolith first. Separate Python modules, not a separate deployed service for every agent.
- Keep numerical finance, portfolio constraints, and ledger arithmetic independent of the LLM and LangGraph.
- Access external providers through adapters. Domain code must not import provider SDKs.
- Separate data retrieval, research, stock selection, allocation, and evaluation.
- A risk profile must resolve to explicit settings. Never silently relax constraints to obtain a portfolio.
- Return structured outcomes for missing evidence, stale data, quota exhaustion, invalid output, and infeasible optimisation.
- Keep model identity, prompts, policy version, source dates, configuration, and usage traceable.
- Require bounded tool calls, retries, review rounds, output tokens, and concurrency.
- Treat retrieved documents as evidence, not executable instructions. Allow only defined tools; do not let document text choose arbitrary shell commands or external destinations.
- Do not expose hidden model reasoning. Store tool events, evidence, structured findings, and concise decision rationale.

## Spending and external actions

- Default to fixtures or available free quotas; paid fallback is disabled.
- No new subscription, paid billing activation, premium data purchase, publishing, or real trade without user authorisation.
- Do not rotate keys/accounts to evade quotas.
- Never commit secrets, personal financial details, or restricted datasets.
- No live brokerage execution in version 1.

## Correctness and evaluation

Verify meaningful risks: time cutoffs, units, corporate-action conventions, portfolio constraints, ledger reconciliation, and API failure handling. Numerical facts must come from code and recorded inputs. Validate agent output schemas and citations. Do not interpret a passing schema as factual correctness.

Use fixtures for routine development; live calls are explicit integration checks, not required for every test. Never fabricate benchmarks, investment results, account entitlements, latency, or cost measurements. Date-filtered retrieval does not remove LLM pretraining leakage.

## Completing a work session

- Record implemented files and verification actually performed.
- Update `tasks.md` statuses and attach evidence before marking completion.
- Update `documentation.md` when product requirements/design change and `architecture.md` when interfaces change.
- Add a dated `changes.md` entry for meaningful decisions or implementation changes.
- Refresh `handoff.md`: current stage, last completed task, next task, blockers, tested commands, known failures, and relevant commit if one exists.
- State remaining uncertainty clearly. Do not claim automatic background maintenance or synchronisation.

Keep instructions tool-neutral. Do not add mandatory paid tools or needless abstractions. Ask before substantial scope changes; routine reversible implementation choices can proceed within the approved task.
