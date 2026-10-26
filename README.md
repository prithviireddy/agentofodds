# Agent of Odds

Evidence-backed company research, constrained mathematical portfolio allocation and paper simulation, built as a local student project with zero additional spend by default.

The implemented demo uses React/Vite, a Python modular monolith, a bounded checkpointed workflow, NumPy allocation and exact paper-ledger arithmetic. Five-company and twenty-company profiles use invented data and scripted model responses. Historical live probes are separate; synthetic results establish no investment advantage.

## Start here

- [Platform documentation](docs/platform/README.md): current product, architecture, contracts and limits.
- [Contributor instructions](AGENTS.md): how to work in this repository.
- [Handoff](handoff.md) and [tasks](tasks.md): current checkpoint and next work.
- [Local demo runbook](docs/runbooks/local-demo.md): setup, replay, recovery and packaging.
- [Presenter materials](demo/README.md): walkthrough, report and Q&A.
- [Documentation map](docs/README.md): ownership, delivery specs, decisions, evidence and history.

## Run locally

From the repository root, with uv and Node/npm installed:

```sh
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run --locked python -m backend.app.ui
```

Open http://127.0.0.1:8765 and explicitly choose **Load demo policy**. These are test settings, not an actual investor policy. Fixture execution needs no credentials or provider calls. Dependency installation may need network access.

Research, retry, paper approval and historical price updates are explicit actions. Reload reads saved results. The server is local and single-user; it has no live mode, automatic scheduler or real trading integration.

The planned M0–M5.3 proof milestones and UI.1 are complete at their recorded scopes. Presentation-machine rehearsal and independent financial/model-quality evaluation remain outstanding. See the [evidence register](docs/platform/08-evaluation-and-evidence.md) for dated checks and their limits; this documentation reorganization is not a new full application test.

The existing private repository is `prithviireddy/agentofodds`. Work from your current checkout; historical Windows paths are not setup requirements. Git commits, remote pushes and backups are explicit actions, with no automatic synchronization.
