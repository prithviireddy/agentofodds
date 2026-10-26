# Handoff — Agent of Odds

## Current checkpoint: documentation relocation, 2026-10-26

The user requested moving the remaining old root documents into `docs/`. Last completed task: DOCS-001. Handoff/tasks/changes now live here; architecture/requirements already belong to platform chapters, and their redundant root pointers are removed. README.md and AGENTS.md remain at the root. The original eight-file history snapshot is unchanged. Base commit: `069828f`; the worktree was clean when this follow-up began.

Verification passed: seven packaging tests in checkout and extraction; 30 active Markdown files/193 links and anchors; eight byte-identical history snapshots; previously built legacy ZIP acceptance; new 140-payload ZIP with all 32 docs and no old root files; source hashes and whitespace checks. Commands: `uv run --locked --offline python -m unittest backend.tests.test_m5_demo_bundle -v`, `uv run --locked --offline python /tmp/agentofodds-doc-relocation-check.py`, and `git diff --check`. The new temporary ZIP is `/tmp/agentofodds-doc-relocation.zip`; historical evidence remains unchanged. Author review only, no new known failure.

This follow-up changes documentation paths and packaging only. At implementation closeout it was uncommitted; the user subsequently requested committing and pushing DOCS-001 to `origin/main`. The delivery commit is identified in Git history, and remote equality is checked after push. No domain/UI/fixture/dependency change, full-suite/browser rerun or live call is introduced by this Git delivery. No implementation blocker remains for DOCS-001; the next operational task is OPS-001 presentation-machine rehearsal. Prior implementation/delivery context and known product limitations follow below with their original dates.

## Previous checkpoint: Git delivery

Checkpoint: 2026-10-26, user-authorized Git delivery of FEAT-0001. Branch: `main`; implementation base commit `7c0ff8b` (`docs: record GitHub upload and verification`). The worktree was clean before the October 24 implementation. Work from the current checkout, not the historical Windows path.

The user requested committing and pushing the completed changes to `origin/main`. Implementation commit `964c87c` was pushed successfully after the user unlocked the personal SSH key and verified authentication as `prithviireddy`. The earlier public-key failure and the alternate GitHub CLI account's missing write permission no longer block delivery through SSH. Git author settings were absent, so commits use the identity from existing repository commits through command-local overrides; no global configuration was changed. This follow-up records the resolved delivery status.

Delivery review confirms the documentation and packaging scope; the six-test and bundle/link evidence below remains dated October 24. `git diff --check` and staged active-document whitespace checks passed October 26; preserved history retains original bytes. No application changes or additional test runs are introduced by this delivery. Git history identifies the implementation commit and this delivery-status follow-up.

## Current stage

M0–M5.3 and UI.1 remain complete at recorded proof/fixture scopes. The product is a local React/Vite workspace with Python research/selection/allocation, bounded checkpointed review, explicit paper approval, exact ledger and manual valuation replay. Full flows are synthetic. Independent financial/model-quality evaluation and production/live automation remain unimplemented.

The preceding completed task was [FEAT-0001](feats/FEAT-0001-documentation-foundation.md), documentation consolidation and demo-package portability. Platform authority is [docs/platform/README.md](platform/README.md). Earlier root records and the demo setup guide are preserved through [history](history/README.md). The later DOCS-001 follow-up removes the temporary root documentation/architecture pointers; AGENTS contains cross-task rules only.

## Last completed work and current verification

Implemented eight topical platform chapters, governance/templates/runbooks, concise navigation and contributor instructions, and an explicit supplemental packaging allowlist. Original schema-v1 bundles remain verifiable. The only executable changes are `backend/app/demo_bundle.py` and its tests; frontend/domain/fixtures/dependency locks and historical evidence are unchanged.

Completed checks: `uv run --locked --offline python -m unittest backend.tests.test_m5_demo_bundle -v` passed all six tests; temporary demo build/verification passed with 142 payloads and all 29 docs. Active-link/fence checks passed on 32 Markdown files and 193 local links/anchors in checkout and extracted ZIP. Eight snapshots match Git base bytes; bundle source hashes match checkout. `git diff --check` passed. Author review only; no independent panel. Full suite, React build/browser and live checks were not rerun.

Environment: Linux, uv 0.12.23, Python 3.14.4. `uv sync --locked --offline` first failed on sandbox cache permissions, then on an absent cached NumPy wheel. Authorized `uv sync --locked` downloaded/installed the existing locked NumPy 2.5.3 successfully; dependency declarations/locks are unchanged.

## Next work and limits

Next: OPS-001 presentation-machine rehearsal using [the local runbook](runbooks/local-demo.md) and [presenter walkthrough](../demo/walkthrough.md). No implementation blocker remains for FEAT-0001, and no new implementation milestone or paid inference is selected.

Known historical issue: October 1 `npm --prefix frontend run check` failed on existing `src/main.jsx` formatting. October 17 full Python tests/build passed, without a formatter/browser rerun. Broader browser/accessibility and cache-free presentation setup remain unverified. No actual user investment policy is configured.

The historical live corpus covers two MSFT documents; live price availability/corporate-action conventions are not sufficient for point-in-time evaluation. Current account entitlements and rotation of formerly exposed example credentials are unverified. Default fixture work needs no credentials. Runtime books/checkpoints are ignored local data; do not print `.env` or reset books. No server was started for this documentation task, and no old server session is presumed alive.

At the October 24 implementation checkpoint, no commit or push had occurred; the October 26 request authorizes that Git delivery. No application deployment, provider call, added provider spend or trade is involved. Historical ZIP evidence remains dated; verification used `/tmp/agentofodds-docs-demo.zip` and a separate temporary manifest. These files are local checks, not published artifacts or guaranteed long-term storage.
