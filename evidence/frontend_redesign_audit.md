# React frontend redesign audit

Date: 2026-09-30. Scope: presentation and interaction feedback for the existing local fixture workspace. No API, authentication, database, domain arithmetic, workflow policy, fixture or route changes. No dependency added.

## Inspection and implementation plan

Inspected every frontend source/stylesheet, index, Vite configuration, package/lock metadata and existing smoke script before editing. The application has one root page, no client router, and three main React modules: main.jsx (configuration/results/reports), PaperLedger.jsx (preview/approval/journal), Monitoring.jsx (valuation/replay). Styling previously used a dark green canvas, lime accent, serif headlines, compact labels and separate ledger overrides. State is controlled React state with explicit API actions and localStorage run restoration. There is no existing authentication UI or other hidden page to redesign. Existing desktop/mobile screenshots were inspected.

Plan carried out: retain the existing page/workflow structure; apply DESIGN.md tokens; consolidate repeated presentation; improve empty/loading/error/form/focus states; verify both fixture profiles and all responsive breakpoints; review final visuals and record evidence.

Primary design source: [frontend/DESIGN.md](../frontend/DESIGN.md). Applied [installed Taste skill](../frontend/.agents/skills/design-taste-frontend/SKILL.md) and [installed Vercel skill](../frontend/.agents/skills/web-design-guidelines/SKILL.md). Retrieved [current Vercel guidelines](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md) for the initial and final reviews.

Taste design read: existing research workspace for students/reviewers, using the supplied Apple-inspired utility/configurator language. DESIGN_VARIANCE=3, MOTION_INTENSITY=1, VISUAL_DENSITY=5. Predictable data layout, no decorative animation; only a pending-request indicator. Marketing imagery, carousels, hero motion and table-removal prescriptions are inapplicable to this product UI. DESIGN.md takes precedence over Taste defaults for system fonts, white/black surfaces, deliberate dark context tile, radii and light-dominant theme. No unrelated design library or dark-mode feature was introduced.

## Coverage

| Existing view/state | Final treatment |
| --- | --- |
| Workspace and navigation | Existing root URL/brand retained; semantic in-page navigation and keyboard skip link; subdued black header/parchment subnav |
| Configuration and saved runs | Labeled reusable fields, selectable company capsules, paired bounds, unchanged field order and constraints; editable policy stays separate from saved results |
| Initial empty/loading/connection error | Useful setup guidance; announced loading and actionable reload error |
| Native/backend policy errors | Inline validity messages, hidden required controls revealed, first invalid control/error summary focused; no invalid native-form POST |
| Research progress/recovery | Original continue/retry/pause/download actions, saved counts/history and unknown-usage disclosure; pending controls indicated |
| Reviewed allocation/failed proposal | Numeric columns and reviews grouped clearly; allocation/approval still withheld on unsuccessful outcomes |
| Selection/reports/citations | Original eligibility reasons and evidence preserved; reusable tables, native disclosures, readable dates, full source/hash details |
| Paper preview/approval/reload | Exact journal/quantity details preserved; unchanged consent wording, proposal binding and durable receipt; pending approval feedback |
| Historical valuation/replay | Grouped original timestamps, readable date options retaining ISO values, exact archived inputs, unchanged price-only actions and history |
| All screen sizes | Two-column desktop workspace, single-column tablet/phone, smaller typography, wrapping metrics, keyboard-scrollable wide ledger table |

Reusable components in src/ui.jsx: Button, Field, SectionHeading, Notice, Metrics, DataTable, Timestamp. Currency/percent/date/count functions format existing values for display only. Raw timestamps remain available in time datetime/title attributes and archived JSON; fractional quantities and exact arithmetic remain backend-owned.

## Final design and Vercel review

- White/parchment, #1d1d1f ink, #0066cc actions; #0071e3 focus/hover. System sans at 17px body, 600 headings, consistent 8/12/17/24/32/48 spacing. Rectangular context tile, 18px utility cards, 8px inputs and pill actions. No gradients, shadows, serif, decorative image, external font or added color family.
- Calculated token contrast ratios: ink/white 16.83:1; secondary text/parchment 11.60:1; primary button white/blue 5.57:1; white/hover blue 4.70:1; dark secondary text/tile 9.28:1. Input border/white 4.29:1 meets the 3:1 nontext target. Disabled text is intentionally muted; no inactive-control text compliance claim.
- Native buttons/links/labels/checks/details; scoped table headers/captions; named focusable scroll regions; structured definition lists and heading hierarchy. Visible focus, 44px action/summary/company hit targets, reduced-motion pending indicator, safe-area gutters and no zoom restriction.
- Explicit loading, disabled, success and failure feedback; unsaved edited policy gets a beforeunload guard with cleanup. Read-only saved-run opening does not dispatch work. Native validation never changes backend constraints.
- Final code findings addressed: main.jsx native controls lacked names/inline errors and hidden invalid fields could stay collapsed; repeated tables/metrics lacked consistent semantics; Monitoring/PaperLedger had crowded dates and repeated markup. All now use the shared presentation primitives.
- Browser verification found a pause control offered while a new run was still being created. Gated it on a continuable saved run; preserved executor/retry/pause behavior and reran both smoke flows successfully.
- Visual review refined narrow-screen numeric wrapping, input typography, date-option labels and clipping of an unfocused skip link in tall screenshots. Inspected final desktop paper panel and 320px/1024px monitoring views; expanded 390px screen inspected separately.

## Verification actually performed

Windows, existing locked Node/React/Vite and Python environment. Existing bundled Playwright/Chromium; no new packages or provider calls.

- `npm --prefix frontend run build`: passed. Production output about 247.38 kB JS (76.41 kB gzip), 13.86 kB CSS (3.68 kB gzip); these are build artifact sizes, not performance scores.
- `npm --prefix frontend run check`: passed. Uses the already installed Prettier; this is formatting, not semantic lint/type checking. No separate lint/typecheck configuration exists.
- Compared SHA256 against the recorded M5.3 inventory: all 84 backend, fixture, configuration and dependency files matched, including the unchanged frontend package lock. `node --check` passed for both browser scripts. No backend/input change was inferred solely from an untracked Git tree.
- `uv run --locked python -m unittest backend.tests.test_m4_ui backend.tests.test_m4_paper backend.tests.test_m4_monitoring backend.tests.test_m5_demo_bundle -q`: 34 passed in 9.040s. The full 168-test result remains the earlier M5.3 evidence; it was not claimed as rerun for this frontend-only change.
- `node frontend/smoke.cjs`: final production five-company :8772 and twenty-company :8773 passed. Research/citations, approval consent and exact reconciliation, receipt reload, two saved valuations and earlier replay, unchanged research, rejected proposal suppression, quota retry, pause/reload/resume, 390px document width and no page errors. Optional UI_SCREENSHOT_DIR isolates profile screenshots.
- `node frontend/design-audit.cjs`: loading/connection error, native/backend validation, skip link/focus, unsaved policy guard, read-only saved run, missing-evidence suppression, named/labeled controls, 44px targets, long-number containment and no document overflow at 320/390/640/768/834/1024/1440/1920px. Machine-readable results and screenshots under ignored data/ui-redesign-audit and data/ui-redesign-audit-twenty.

## Limits and next step

Chromium and fixture data only; Safari/Firefox, screen-reader device testing, automated axe and Lighthouse/CWV scoring were not performed. No installed Lighthouse/axe runtime was available; no compliance certification or performance score is claimed. Existing local-server/security/research limitations are unchanged. URL-synchronised run/filter state and localisation remain outside this visual task; existing localStorage restoration and explicit controls are preserved.

M5.3's ZIP and verification describe the earlier frontend snapshot; they remain historical evidence. Rebuild the demo ZIP from the current checkout before sharing the new UI. DESIGN.md, skill installation metadata and the optional standalone design-audit script are not part of the existing package allowlist; no packaging/backend interface was expanded for this redesign.

Next: review the updated workspace and rehearse it on the presentation machine. Before any production deployment, separately scope server/authentication and wider browser/accessibility/performance validation.
