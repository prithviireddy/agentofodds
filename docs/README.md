# Documentation map

Start with [the platform index](platform/README.md). It defines current documentation authority and the change process.

| Location | Owns |
| --- | --- |
| [platform/](platform/README.md) | Integrated current product and architecture, contracts, supported behavior and limitations |
| [adrs/](adrs/README.md) | New architectural decisions after this consolidation |
| [feats/](feats/README.md) | Bounded delivery specifications and acceptance evidence |
| [runbooks/](runbooks/README.md) | Repeatable setup, recovery, verification and packaging procedures |
| [deferred/](deferred/README.md) | Unimplemented options outside approved delivery; not contracts |
| [history/](history/README.md) | Preserved earlier repository records; not current authority |
| [reviews/](reviews/LEDGER.md) | Concise review outcomes and evidence |
| [tasks.md](tasks.md) / [handoff.md](handoff.md) | Delivery index / latest operational checkpoint |
| [changes.md](changes.md) | Dated change history |
| [evidence/](../evidence) | Recorded experiment and verification artifacts; each retains its original date/scope |
| [demo/](../demo/README.md) | Presenter narrative, report and walkthrough |
| [frontend/DESIGN.md](../frontend/DESIGN.md) | Visual tokens and design reference, applied within product behavior |

Only README.md and AGENTS.md remain as root Markdown discovery files. Current handoff, tasks and changes live here in `docs/`. The old root `documentation.md` and `architecture.md` pointers have been removed: use [product and scope](platform/01-product-and-scope.md) and [architecture](platform/02-architecture.md). Original substantive records remain in history; do not recreate parallel root specifications.

## Existing document disposition

The former root requirements, architecture, task log, handoff, change log, README and contributor instructions are preserved byte-for-byte in the [2026-10-24 snapshot](history/README.md). Their mixed proposals and implementation notes are reconciled into topical platform chapters. The old demo setup guide is preserved there too; current procedures live in runbooks.

Existing demo reports, evidence records and the frontend visual reference remain at their original paths. Historical statements inside dated evidence are not rewritten to appear current. JSON experiment archives and manifests remain unchanged by this consolidation.

The 15 Markdown files under `frontend/.agents/skills/` are bundled frontend tooling references, including a sample design system. They are inventoried as supporting material, not platform specifications or automatically invoked rules. Their design prescriptions can conflict with each other and with the product; the project visual reference and current task govern applicable choices. This task does not redesign those skills. The paper attachments mentioned in old notes are absent from this checkout; their summaries are historical, not newly validated literature findings.
