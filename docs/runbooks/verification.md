# Verification and closeout

## Declare the route

Before coding, record affected behavior, dependencies, acceptance criteria and checks in the FEAT/task or work update. Select by behavior, not filenames alone; reassess against the final diff. Run narrow cases while developing, then the complete affected selection at closeout.

| Affected behavior | Relevant starting selection |
| --- | --- |
| Documents/navigation | Local link/heading checks, source/contract review, `git diff --check`; packaging checks if distribution references change |
| Data adapters/provenance | `test_fixtures`, `test_sec`, `test_alpaca`, `test_evidence` as affected; cutoff, units, missing coverage, HTTP failures |
| Models/retrieval/research | `test_gemini`, `test_m2_index`, `test_m2_research`, `test_m3_research`; schema/citations, evidence visibility, quota bounds |
| Policy/statistics/selection/optimiser | `test_m1_contracts`, `test_m1_numerical`, `test_m3_selection`, plus downstream workflow/ledger/comparison cases affected by changed values |
| Workflow/checkpoints | `test_m3_workflow`, affected UI/universe tests; fingerprint compatibility, reservations, interrupted/rejected/incomplete runs |
| Paper approval/valuation | `test_m4_paper`, `test_m4_monitoring`, affected HTTP/comparison tests; exact reconciliation, consent, idempotency, rollback, replay |
| HTTP/React interactions | `test_m4_ui` and affected services, frontend build/check; browser success/failure/recovery/consent flows when interaction changes |
| Experiment design/replay | `test_m1_evaluation`, `test_m5_comparison`, affected numerical tests; holdout isolation and archive replay |
| Fixture expansion | `test_m5_universe` plus affected workflow/ledger/monitoring/comparison checks; both profiles |
| Distribution | `test_m5_demo_bundle`, build/verify a fresh temporary ZIP, inspect extracted inventory and affected behavior |

Tests are Python unittest modules under `backend.tests`; combine the affected modules in one invocation where useful:

```sh
uv run --locked --offline python -m unittest backend.tests.test_m5_demo_bundle -v
npm --prefix frontend run check
npm --prefix frontend run build
git diff --check
```

Choose only applicable commands. `--offline` requires cached dependencies. Frontend `check` runs Prettier formatting, not semantic lint, type checking or accessibility certification. The repository has no CI configuration or coverage floor at this checkpoint; if CI is introduced, include checks affected by the change and distinguish pending CI from a pass.

A full suite is appropriate for an explicit request, fresh distribution rehearsal, broad dependency impact or an effect that cannot be bounded. Record that reason before `uv run --locked python -m unittest discover -s backend/tests -q`. Do not routinely rerun full suites or repeat passing checks without changed inputs/unresolved failures.

## Browser and security evidence

`node frontend/smoke.cjs` requires a running server and an available Playwright/Chromium runtime; set `PLAYWRIGHT_MODULE` if needed. `UI_BASE_URL`, `EXPECTED_COMPANIES` and optional `UI_SCREENSHOT_DIR` select the profile/output. Run five and twenty profiles when shared flows change. `node frontend/design-audit.cjs` covers the existing responsive/error/interaction audit. Use the actual final build under review.

For changes to the trust boundary, exercise relevant Host/Origin, static-path confinement, input limits, escaped evidence, fixed decoder types, provider allowlists, proposal binding and corruption/rollback tests. No generic command substitutes for the affected controls. No security certification is implied by historical browser evidence.

## Encountered issues

Classify every observed defect/failed check as introduced or affected, pre-existing but relevant, demonstrably unrelated, or unresolved. Pre-existing alone does not mean unrelated. Where feasible, reproduce on the untouched base, isolate the failing case and trace its relation to behavior/dependencies/required evidence. Record evidence, impact, disposition and what remains uncertain.

Fix regressions introduced by this delivery. Unrelated fixes need separate scope if material; record them without silently expanding the delivery. Surface security or data-integrity concerns promptly. Do not weaken checks, hide errors or relabel unavailable checks as passing.

A failing required check blocks a passing verdict unless equivalent evidence identifies the same base failure, isolates it outside affected behavior/dependencies and establishes the rest of the required route. Unresolved attribution touching required behavior stays blocked. An unrelated issue outside the required route does not block delivery.

## Review and completion

Review the final diff against scope, contracts and recorded checks. Author review is mandatory; independent review is used when requested or available within existing authorization, without a fixed vendor/model or extra spending. Record identities and distinguish author from independent review. If a requested independent review is unavailable, say so.

If using verdicts, `SHIP` means the defined scope meets its contracts and required verification, with non-blocking limitations recorded. `NO-SHIP` identifies a concrete correctness, safety, repository-rule or required-evidence blocker. Neither verdict authorizes a commit, merge, push, publication or trade. Any subsequent edit requires review of its affected scope and rerunning checks it invalidates. If an independent review loop is requested, stop after three unresolved rounds and hand the open findings to the user rather than looping indefinitely.

Update the FEAT/task with changed files, exact commands/results, environment, encountered issues, review scope and limits. Record concise review outcomes in [the ledger](../reviews/LEDGER.md); raw reviewer output and working plans can remain under ignored `data/` or temporary storage. When exact patch identity matters, record base commit and a saved patch digest; do not imply an exact-tree review if only selected files were inspected.

Fold enduring behavior into platform chapters and procedures into runbooks. Then update tasks, changes and handoff. Completion evidence is what actually ran; a historical 168-test result is not evidence of today's full suite.
