# Agent of Odds change log

Updated: 2026-10-26. This file records dated changes; [platform documentation](docs/platform/README.md) owns current contracts. Add new entries at the top and preserve previous outcomes without presenting them as fresh verification.

## 2026-10-26 — User-requested Git delivery

- Committed the completed FEAT-0001 documentation and packaging changes locally on `main`, as explicitly requested by the user. Refreshed handoff to record delivery authorization and the push blocker; application behavior and dependency locks are unchanged.
- Reviewed the diff/file inventory and passed active-file whitespace checks. October 24 tests/link/bundle checks remain the implementation evidence; no full-suite or browser rerun is claimed. Missing Git author settings were resolved using the existing repository author through command-local overrides.
- Push blocked: after the sandbox SSH configuration failure, unrestricted SSH failed public-key authentication. The existing GitHub CLI login is valid but has no push permission on this repository (`permissions.push=false`). No remote update is claimed; an account with write access or the intended unlocked SSH identity is required. Global Git settings and remote configuration were preserved.

## 2026-10-24 — Documentation foundation

- User requested a source-based repository mental model and contributor/documentation structure inspired by SaganAgents. Consolidated current product, architecture, entities, workflow, simulation, UI/API, security/budget and evaluation into `docs/platform/`.
- Separated ADRs, FEATs, runbooks, deferred options, history and review records. Added lightweight templates and behavior-based verification rules without imposing another project's tools, models, CI or architecture.
- Preserved eight original documents byte-for-byte under `docs/history/2026-10-24/`; root documentation/architecture are navigation pointers, and README/tasks/handoff now describe current state. Existing dated evidence, presenter reports and visual reference retain their roles.
- FEAT-0001 includes an explicit documentation packaging allowlist so future demo ZIPs retain the new context. Old bundle verification remains compatible. Scope excludes application/domain/UI/fixture/dependency changes.
- Verification: six packaging tests passed; 32 active Markdown files/193 local links and anchors checked in checkout and extraction; eight history snapshots match Git base; a temporary 142-payload ZIP contains all 29 docs and verifies against source hashes; `git diff --check` passed. Author review only. See [FEAT-0001](docs/feats/FEAT-0001-documentation-foundation.md) for commands and scope.
- Encountered environment failures: sandbox uv-cache writes and an absent offline NumPy wheel; approved cache access and locked online installation resolved them. No dependency version change. No full-suite/browser rerun, live provider call, added provider spend, publication, trade, commit or push. Presentation-machine rehearsal remains next.

## Earlier history

[The preserved change log](docs/history/2026-10-24/changes.md) contains the complete September 20–October 17 decisions, implementation notes and verification records, including the October 1 demo refresh and October 17 Git upload. Its earlier maintenance rules and provisional status statements are historical. No automatic synchronization or background maintenance is configured.
