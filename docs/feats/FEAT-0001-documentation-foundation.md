# FEAT-0001: Documentation foundation and portable demo docs

Status: done

Date: 2026-10-24

Authorization: user requested a repository mental model, adapted contributor instructions and migration of existing documentation to the proposed structure.

Owning chapters: [platform index](../platform/README.md), [distribution](../platform/08-evaluation-and-evidence.md#distribution-contract)

ADR: none; consolidate existing runtime behavior and introduce documentation governance directly.

## Problem and outcome

Root documents interleave initial proposals, superseded status and implemented milestones. Readers must reconstruct chronology to determine the actual stack and supported behavior. A demo ZIP currently packages only those root documents, so moving authority without updating its allowlist would leave extracted copies with missing references.

The result is one topical platform reference, separate delivery/decision/procedure/deferred/history layers, concise contributor rules and entry points, and new demo bundles that carry the documentation they reference.

## Scope and exclusions

- Reconcile product documents against source/configuration/tests; retain proof scope and known limits.
- Preserve original root documents and demo guide byte-for-byte in a dated history snapshot, with an explicit non-authority notice in its parent index.
- Add ADR/FEAT templates, scoped verification guidance and review ledger. Do not invent historical decisions, independent reviews, CI, paid-tool requirements or future product authorization.
- Keep root documentation/architecture pointers, refresh README/tasks/changes/handoff and route demo setup to a runbook.
- Add an explicit supplemental documentation allowlist to `demo_bundle.py`. New builds require those files; old schema-v1 bundles remain verifiable without them. Preserve all existing secret/runtime exclusions, source confinement and size/inventory limits.
- Leave UI, domain algorithms, fixtures, dependencies, historical evidence JSON/manifest, existing skill files and dated presenter reports unchanged. No provider call, publication, commit or push is part of this task.

## Acceptance criteria

1. Platform chapters describe actual modules, entity ownership/lifecycles/access, workflow limits, financial invariants, API, trust boundary and evaluation scope. Proposed infrastructure is explicitly deferred.
2. Every original product document has an owning destination or an explicitly preserved role; snapshots match pre-change Git bytes. Active local Markdown links and heading anchors resolve, with historical/tooling documents treated as scoped references.
3. Contributor instructions fit the local zero-spend project and define a practical change/verification/closeout process.
4. Newly generated bundles contain all explicitly listed new documentation and verify their hashes. An old-format inventory still verifies. Missing new build sources fail; arbitrary files under `docs/` remain excluded.
5. Complete the affected packaging tests, link checks, snapshot identity checks, temporary ZIP build/verification and final diff review. Report unavailable checks honestly. Broader application evidence remains historical.

## Verification route declared before code changes

Read all product documents, inventory supporting frontend skill references, and inspect source ownership, provider configuration, workflow, HTTP and storage code. Validate active documentation links/anchors and compare snapshots with Git HEAD. Run `uv run --locked --offline python -m unittest backend.tests.test_m5_demo_bundle -v`, adding focused regression coverage for document inclusion, missing sources and old-bundle compatibility. Build/verify a temporary bundle and inspect its inventory. Run `git diff --check` and inspect the final diff for unintended runtime/fixture/dependency changes.

The executable change is confined to packaging, so full numerical/UI suites, frontend build/browser tests and live provider probes are outside the affected route. Existing environments may need locked dependency setup; no dependency version change is authorized by this feature.

## Closeout evidence

Implemented files: root contributor/navigation/task/handoff/change documents, the demo entry point, 29 explicitly listed files under `docs/` (including eight preserved originals), `backend/app/demo_bundle.py` and `backend/tests/test_m5_demo_bundle.py`. Runtime behavior and dependency declarations/locks are unchanged.

Verification on 2026-10-24, Linux, uv 0.12.23 and Python 3.14.4:

- `uv sync --locked`: installed the existing locked NumPy 2.5.3 after offline/cache failures; no version changes.
- `uv run --locked --offline python -m unittest backend.tests.test_m5_demo_bundle -v`: all six tests passed. Covers repeatable packaging, documentation inclusion, missing documents, original schema-v1 inventory compatibility, corruption, path policy and exclusions.
- `uv run --locked --offline python -m backend.app.demo_bundle --output /tmp/agentofodds-docs-demo.zip --manifest /tmp/agentofodds-docs-manifest.json`: built and verified 142 payloads plus the bundle manifest, including all 29 explicitly listed documentation files.
- Temporary standard-library check `/tmp/agentofodds-doc-check.py`: 32 active Markdown files and 193 local links/anchors passed in both checkout and extracted bundle; code fences balanced. Historical snapshots and optional frontend tooling references are excluded from active-link checking by design. All eight preserved documents match base commit `7c0ff8b` byte-for-byte, and bundle payload hashes match checkout source bytes.
- `git diff --check`: passed. Author review checked current contracts against source and the final scope; no independent review is claimed. The preserved original documents retain historical wording intentionally.

Encountered issues: uv could not write its cache inside the sandbox (environment/verification-related), then the offline cache lacked the locked NumPy wheel (environment/verification-related). Approved cache access and locked online installation resolved both; offline packaging tests then passed. An extended whitespace check caught introduced Markdown hard-break trailing spaces in three new files; paragraph breaks replace them. Frozen history retains its original whitespace intentionally. The October 1 frontend formatting failure is a known historical issue outside this delivery; it was not rerun or repaired. No new required-check failure remains.

No full Python suite, React build/browser rehearsal, provider entitlement check, external literature verification or financial/model-quality experiment was run for this change. Old-bundle compatibility is verified with a regression inventory representing the original format, not a claim that an old ZIP was present locally. Temporary artifacts are not published and do not replace historical M5.3 evidence. Presentation-machine rehearsal remains OPS-001; no commit or push was made.
