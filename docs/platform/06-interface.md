# Interface

## HTTP contract

[backend.app.ui](../../backend/app/ui.py) serves the compiled React index/assets and a narrow same-origin JSON API. It binds to `127.0.0.1`, default port 8765. Requests require the exact loopback Host and, if present, matching Origin. POST requires `application/json` and a body between 1 and 16,384 bytes. Invalid inputs fail explicitly; domain paper errors use HTTP 409. Missing builds return HTTP 503 with setup instructions.

| Method and route | Behavior |
| --- | --- |
| `GET /api/settings` | Configured companies/cutoff, explicit demo values and execution bounds |
| `GET /api/runs` | Up to 30 saved-run projections |
| `POST /api/runs` | Validate complete policy/selection/scenario values and save a new input manifest; HTTP 201 |
| `GET /api/runs/{id}` | Read-only current snapshot |
| `POST /api/runs/{id}/advance` | Exactly `{"retry": boolean}`; advance one stage or explicitly retry |
| `GET /api/runs/{id}/paper` | Original receipt, or read-only reviewed proposal preview |
| `POST /api/runs/{id}/approve-paper` | Exactly `approved` and `proposal_id`; consent must be boolean true |
| `GET /api/runs/{id}/valuations` | Original dates, available fixture dates, saved history and limitations |
| `POST /api/runs/{id}/valuations` | Exactly `{"valuation_at": "timestamp"}`; explicit update or saved-date replay |

Run IDs are generated server-side and validated before filesystem access. Unexpected payload fields are rejected by relevant handlers/services. Static paths are confined to built assets. The service projects allocation as null unless the entire workflow succeeds, including downloadable JSON; failed-run diagnostic weights cannot become an actionable UI proposal.

## React behavior

[main.jsx](../../frontend/src/main.jsx) owns configuration, saved runs, progress, research, selection and reviews. [PaperLedger.jsx](../../frontend/src/PaperLedger.jsx) owns preview/consent/receipt presentation; [Monitoring.jsx](../../frontend/src/Monitoring.jsx) owns explicit historical updates and saved replay. There is one root workspace, no client router or authentication UI.

Initial policy fields are blank. **Load demo policy** fills labelled test settings. The mutable new-run form remains separate from saved-run settings. The normal, missing-evidence, quota and rejected-review scenarios are scripted demonstrations.

Starting/continuing a run dispatches sequential advance requests. Pause stops that browser loop after the current atomic stage; closing a tab does not undo the stage. Reload reopens a saved run without dispatch, consent or valuation writes. Retry is explicit and bounded by persisted limits. No polling scheduler or automatic research refresh exists.

## Presentation ownership

[frontend/DESIGN.md](../../frontend/DESIGN.md) owns the supplied visual reference and tokens. Its marketing examples are adapted to the research workspace, not a requirement to add storefronts, decorative photography or new routes. The current implementation uses a light/parchment surface, dark context tile, system sans typography and Action Blue with no external assets.

[ui.jsx](../../frontend/src/ui.jsx) provides Button, Field, SectionHeading, Notice, Metrics, DataTable and Timestamp. Formatting is presentation-only: original ISO values and exact archived amounts remain available. Numerical finance stays in Python. Labels/names, inline native validation, invalid-field reveal/focus, skip links, table semantics, keyboard scrolling, 44px targets, reduced-motion feedback and an unsaved-policy guard are implemented. Browser/accessibility verification limits belong to [the evidence register](08-evaluation-and-evidence.md).

Vite development uses loopback port 5173 and proxies `/api` to port 8765; production serves `frontend/dist`. The proxy removes Origin only for its own matching incoming origin. [The local runbook](../runbooks/local-demo.md) owns commands and recovery. Public or multi-user operation requires a separately designed server/access boundary.
