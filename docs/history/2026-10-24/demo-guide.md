# Agent of Odds — college demonstration

Start here after extracting the demo ZIP. Open a PowerShell terminal in the extracted project root (the folder containing pyproject.toml).

## What is demonstrated

React/Vite research workspace → cited fundamental/news reports → explicit stock-selection rules → constrained minimum-variance allocation → independent reviews → human paper approval → exact local ledger → price-only historical replay. Five-company and twenty-company synthetic profiles exercise the same contracts.

The separate comparison report demonstrates a reproducible experiment: equal weighting, numerical-only allocation, combined research and separate research, with decisions frozen before evaluation-only prices. It establishes no strategy winner or investment advantage.

## Setup

Prerequisites: uv, Python 3.14 (uv may manage it), Node.js and npm. The verification record lists the versions exercised on Windows. Package installation may require internet access on a new machine; fixture execution requires no credentials or provider network calls. Prepare dependencies before presenting. The ZIP does not contain Python/Node, .venv, node_modules or compiled frontend assets.

```powershell
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run --locked python -m backend.app.ui --port 8765
```

Open http://127.0.0.1:8765. Leave the terminal running. Stop with Ctrl+C. If the port is occupied, use --port 8768 and open that port; do not stop someone else's server.

An expanded demo can run in a separate terminal:

```powershell
uv run --locked python -m backend.app.ui --fixture-set twenty --port 8766
```

Open http://127.0.0.1:8766. Five/twenty profile state is isolated under data/ui_runs and data/ui_runs_20. Fresh extraction provides empty state. Existing state is preserved; there is no destructive reset command. **Load demo policy** explicitly fills test values; blank initial form values are intentional.

## Offline replay and proof

```powershell
uv run --locked python -m backend.app.compare_experiments --replay evidence/m5_2_comparison.json --output data/demo_replay.json
uv run --locked python -m unittest discover -s backend/tests -q
```

The replay writes JSON and Markdown beside each other. It verifies archived source/decision identities and recalculates outcomes without model calls or current price fixtures. Open evidence/m5_2_comparison.md for the short comparison table. No annualised return, Sharpe ratio or ranking is claimed.

If time permits, regenerate the experiment and audit:

```powershell
uv run --locked python -m backend.app.compare_experiments --output data/demo_comparison.json
uv run --locked python -m backend.app.universe_audit --output data/demo_audit.json
```

## Presenter materials and evidence

- report.md: concise contribution, comparison findings, historical live proofs and evidence/financial limits.
- walkthrough.md: an approximately seven-minute sequence and expected screen behavior.
- presenter_notes.md: scope, architecture and short answers to likely questions.
- ../evidence/m5_3_refresh_verification.json: current-package setup/tests/replay checks; historical browser checks remain separately dated.
- ../evidence/m5_3_verification.json: actual setup/rehearsal checks and their limits.
- ../evidence/m5_2_comparison.json and .md: archived experiment and readable result.
- ../evidence/m5_1_fixture_audit.json: recorded local scaling samples and per-company synthetic coverage.
- BUNDLE_MANIFEST.json at project root: SHA256 and byte size of every packaged file. Verification detects accidental corruption, not malicious reauthoring.

Verify the ZIP before extraction from a working checkout:

```powershell
uv run --locked python -m backend.app.demo_bundle --verify data/agent-of-odds-demo.zip
```

From inside the extracted project, use the same command with the actual path to the ZIP. Rebuild it from a checkout with:

```powershell
uv run --locked python -m backend.app.demo_bundle --output data/agent-of-odds-demo.zip --manifest evidence/m5_3_bundle_manifest.json
```

## Troubleshooting

An absent frontend build returns frontend_not_built: run npm ci/build before starting. An unavailable package cache requires an internet connection for dependency installation, not a provider subscription. Scripted quota interruption waits for **Retry failed stage**; read-only reload does not retry. Old unfinished workflows using an earlier solver need a new run. A crash may leave a run lock: verify that no writer is active before manually removing that specific stale lock.

The browser smoke script requires an existing Playwright installation and browser runtime; it is optional for presenting and not shipped as a hidden dependency. See the verification record for the available runtime used here. Core Python tests use temporary frontend assets and can run before npm installation.
