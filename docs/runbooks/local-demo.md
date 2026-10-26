# Local demo and recovery

## Prepare and run

Work in the checkout or extracted bundle root containing `pyproject.toml`. Prerequisites are uv, Python 3.14 (uv can manage it), Node.js and npm. Locks declare the versions; dated verification records identify exercised environments. Installation may require internet and does not imply provider usage. The bundle excludes dependencies and compiled frontend assets.

```sh
uv sync --locked
npm --prefix frontend ci
npm --prefix frontend run build
uv run --locked python -m backend.app.ui --port 8765
```

Open http://127.0.0.1:8765. Use **Load demo policy**, inspect the labelled test values and run fixture research. No credentials or provider connection is required. Leave the server terminal running and stop it with Ctrl+C. If a port is occupied, choose another with `--port`; do not terminate another user's process.

For the separate expanded profile:

```sh
uv run --locked python -m backend.app.ui --fixture-set twenty --port 8766
```

Open http://127.0.0.1:8766. State is isolated under `data/ui_runs` and `data/ui_runs_20`. Fresh extraction starts empty; existing state is preserved. Paper approvals during rehearsal are synthetic test actions, not actual investment approvals.

For frontend development, keep the Python server on 8765 and run `npm --prefix frontend run dev`; open http://127.0.0.1:5173. Rebuild before using the production static server after frontend edits.

## Offline commands

```sh
uv run --locked python -m backend.app
uv run --locked python -m backend.app --as-of 2025-01-30T22:00:00Z
uv run --locked python -m backend.app.compare_experiments --replay evidence/m5_2_comparison.json --output data/demo_replay.json
uv run --locked python -m backend.app.compare_experiments --output data/demo_comparison.json
uv run --locked python -m backend.app.universe_audit --output data/demo_audit.json
```

The fixture CLI defaults to `config/universe.toml` and `fixtures/prices.json`; flags include `--universe`, `--prices`, `--start`, `--end`, `--as-of`. Exit codes are 0 for at least one eligible observation per symbol, 1 for partial coverage and 2 for invalid input; success is not complete trading-session coverage.

Comparison replay needs neither current research fixtures nor models. It writes JSON and Markdown to the output stem. The audit performs temporary synthetic approvals and records local timings/coverage; neither command measures investment quality or actual inference cost. Use ignored `data/` for new exploratory outputs so historical evidence is not overwritten.

## Recovery

| Symptom | Procedure |
| --- | --- |
| `frontend_not_built` / HTTP 503 | Complete npm installation/build, then reload. |
| Dependency absent from offline cache | Use locked installation with network access when available; do not change pins to make setup pass. Record unavailable verification if installation cannot complete. |
| Scripted quota interruption | Inspect saved status, then explicitly use Retry failed stage within its existing budget. Reload does not retry. |
| Paused/interrupted run | Reopen saved state and use Continue or the permitted retry; completed stages are reused only with compatible identities. |
| Changed fixture/model/prompt/solver/budget | Start a new run. Do not edit checkpoints to bypass identity checks. |
| Possible stale lock after process crash | Identify the run and establish that no writer is active. Preserve its checkpoint; remove only the confirmed stale lock, then explicitly resume/retry. Never blanket-delete runtime data. |
| Approval response uncertain | Read-only reload first; retry only the same proposal ID if needed. Never fund another book merely because the response was lost. |
| Missing current valuation fixture | Read saved history; archived valuation inputs remain available. An unsaved date needs valid price inputs. |
| Checksum/reconciliation failure | Preserve the original files and record the failure. Do not repair balances by hand or claim successful approval. |

No server process is guaranteed to survive a coding session. Back up permitted runtime data separately, while writers are stopped, before storage changes. Git and the demo ZIP are not backups of paper books.

## Demo packaging

```sh
uv run --locked python -m backend.app.demo_bundle --output data/agent-of-odds-demo.zip --manifest data/demo-bundle-manifest.json
uv run --locked python -m backend.app.demo_bundle --verify data/agent-of-odds-demo.zip
```

Use a new output manifest for current checks. `evidence/m5_3_bundle_manifest.json` remains the dated October 1 inventory unless a separately recorded refresh replaces it. The archive's root `BUNDLE_MANIFEST.json` lists every payload hash/size. Verify before extracting; dependencies must be installed afterward. Build/verification does not publish the archive.

The packager's explicit documentation list must be updated when adding durable documents referenced by the demo. Do not replace that list with unrestricted recursive inclusion. Historical snapshots deliberately preserve old relative references; read them through the history index. Optional installed frontend skill references and the checkout-only UI audit are not part of the demonstration payload.

For distribution verification after packaging changes, inspect the extracted documentation/source inventory and run affected tests there. A complete fresh-machine/browser rehearsal is a separate route and must not be inferred from checksum verification.

## Explicit live probes

The modules `sec_probe`, `alpaca_probe`, `evidence_probe`, `index_probe`, `model_probe` and `research_probe` are separate opt-in integration commands under `backend.app`. Do not run them for routine development or a fixture demonstration. `index_probe` fetches documents when building its live index; it is not a wholly offline setup step.

Before an authorized integration check, inspect configured symbols/cutoff/destinations and limits, confirm needed credentials locally without printing them, and record actual coverage/errors/usage. Shell configuration takes precedence over ignored `.env`. Prior successful records do not guarantee current availability. Credential rotation from the historical example-file incident remains unconfirmed.
