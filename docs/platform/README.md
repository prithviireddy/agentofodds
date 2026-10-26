# Agent of Odds platform

This directory is the integrated current reference for Agent of Odds. It consolidates the existing repository foundation as of 2026-10-24, without turning earlier implementation choices into retrospective ADRs or completed FEATs.

## Reading map

| Chapter | Owns |
| --- | --- |
| [01 Product and scope](01-product-and-scope.md) | Purpose, vocabulary, supported journey and exclusions |
| [02 Architecture](02-architecture.md) | Runtime, source ownership and dependency boundaries |
| [03 Data and persistence](03-data-and-persistence.md) | Entities, identities, provenance, time semantics and physical storage |
| [04 Research and workflow](04-research-and-workflow.md) | Retrieval, roles, selection, budgets, review and resume |
| [05 Allocation and simulation](05-allocation-and-simulation.md) | Numerical conventions, approval, ledger and valuation invariants |
| [06 Interface](06-interface.md) | HTTP/UI behavior, explicit user actions and presentation ownership |
| [07 Security and budget](07-security-and-budget.md) | Trust boundary, external access, secrets and spending |
| [08 Evaluation and evidence](08-evaluation-and-evidence.md) | Experiment design, recorded proofs and limits on conclusions |

## Authority and status

Platform chapters own durable product and architecture contracts. The source tree is inspected to determine implementation; recorded checks establish verification only for their stated inputs, date and environment. When they disagree, record the discrepancy in the affected task and resolve it explicitly. Do not call a documented target implemented merely because it appears here.

Use these labels precisely:

- **Implemented:** present in source, with its scope stated. Link recorded verification separately.
- **Verified:** a named check actually ran with a recorded result and limitations.
- **Target:** agreed work not yet implemented; name its delivery FEAT and acceptance criteria.
- **Deferred:** an option outside current delivery, held in `docs/deferred/`; no promise or authorization follows.

No unimplemented target delivery is silently introduced by this consolidation. The pending presentation rehearsal is an operational task. Broader evaluation and infrastructure options need separate scope agreement.

`docs/adrs/` owns new decision rationale, `docs/feats/` owns delivery scope, and `docs/runbooks/` owns procedures. Completed features fold enduring behavior back into these chapters. `tasks.md` indexes work, `handoff.md` holds the latest checkpoint, and `changes.md` records history. Neither history nor deferred material can override active contracts. [AGENTS.md](../../AGENTS.md) owns contributor operating rules; [frontend/DESIGN.md](../../frontend/DESIGN.md) owns visual tokens.

## Change process

1. Read the owning chapters, inspect code and define the requested outcome. Keep routine fixes within their accepted scope.
2. For material behavior changes, create or update a [FEAT](../feats/README.md) before coding: problem, scope, contracts, exclusions, acceptance and verification route. A typo, navigation correction or narrow bug fix can use an existing FEAT or a bounded task record instead.
3. Write an [ADR](../adrs/README.md) before changing a hard module boundary, persistent identity/relationship, trust or access model, numerical convention, external provider choice, runtime contract or deployment shape. Routine internal refactors preserving those contracts do not need an ADR. Record the actual acceptance basis; a proposed document is not an approved decision.
4. Update every affected platform chapter when a decision is accepted. An unimplemented accepted requirement is marked **Target** with a FEAT link; describe existing behavior separately until delivery.
5. Implement and verify the complete affected scope using the [verification runbook](../runbooks/verification.md). Record unavailable/failed checks and classify encountered issues.
6. Fold shipped behavior into platform docs and procedures into runbooks. Update task evidence, change history and handoff. Do not keep a temporary implementation plan as a second specification.

Future storage changes follow [storage evolution](03-data-and-persistence.md#storage-evolution). Future security checks are scoped to this repository's actual trust boundary; commands and CI gates from another project do not exist here by implication.

## Writing contracts

Use present tense for implemented behavior; define terms before use. Separate product entities from their physical representation. State each entity's owner, identity, lifecycle, relationships and access boundary. Name useful non-entities where an apparent abstraction would mislead. Link to authoritative rules instead of copying them into every document. Keep historical rationale in decision/history records and deferred options outside current architecture.
