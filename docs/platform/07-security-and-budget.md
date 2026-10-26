# Security and budget

## Trust boundary

The current runtime assumes a trusted local operator and filesystem. Loopback-only HTTP, strict Host/Origin checks, bounded JSON input, static-path confinement and CSP reduce exposure; they do not constitute authentication, tenancy isolation or a production security assessment. Local checksums detect corruption, not hostile file replacement. Injected factories/transports and checkpoint files are trusted application inputs.

Retrieved passages and critic feedback are untrusted data. Research tools enforce company/date filters and fixed destinations; text cannot choose shell commands, arbitrary URLs or tools. The checkpoint decoder accepts a fixed type registry rather than dynamic imports or pickle. Evidence is rendered as escaped React text. Safe event metadata retains hashes, identities, timestamps and known usage; hidden model reasoning is not stored.

## External adapters

The fixture UI imports no live provider adapters or credentials. Explicit probes use standard-library HTTP adapters with destination allowlists, response-size/request/time bounds and no automatic retries/redirects. The source/configuration pins actual behavior; successful old access does not establish today's availability or entitlement.

| Adapter | Implemented proof boundary |
| --- | --- |
| SEC | Ticker/submissions/CompanyFacts JSON; declared contact identity, 12 requests/run, sequential one-second spacing, 20-second timeout, 25 MB response cap; configured CIK is issuer authority |
| Alpaca Market Data | One historical daily-bars request, default IEX with `adjustment=all`, 20-second timeout, 20 MB cap; no order endpoint |
| Evidence | At most two configured HTML documents: validated SEC filing and exact Microsoft release URL, 20-second timeout, 10 MB cap; visible text only |
| Gemini | Allowlisted generation transport and pinned model configuration; one request per client, schema output, no tools or paid fallback; workflow budgets bound repeated client construction |

HTTP 429 maps to quota handling and 503 to service unavailability in the Gemini adapter. Safe truncation diagnostics preserve finish reason, response shape/hash and known usage without storing invalid generated fragments. `config/model.toml` records the project's configured model and limits; it is not a claim of current provider availability.

## Credentials and cost

Explicit probe configuration can read ignored `.env`; shell values take precedence. `.env.example` is placeholders only. Credentials, personal financial data, restricted corpora and runtime books stay outside Git and demo payloads. Historical notes record credentials once placed in an example file; rotation status is unknown and must be resolved before reusing those credentials.

The zero-additional-spend and external-action authorization rules live in [AGENTS.md](../../AGENTS.md). Application inference and coding-tool access are separate. There is no guaranteed free entitlement, paid fallback, quota-evading key rotation or automatic top-up. Historical pricing estimates are not current budgets.

The [workflow contract](04-research-and-workflow.md) owns execution budgets. Token reservations bound dispatch but are not a monetary billing cap. Unknown actual inference usage/cost remains unknown; fixture call counts are not paid model measurements. Adapters own transport deadlines. No automatic background quota retry is implemented.

## Changes affecting this boundary

Changes to HTTP serving, origin/static confinement, evidence rendering, decoding, provider destinations, secrets, approval identity or persistence must verify the affected controls using the [verification runbook](../runbooks/verification.md). This repository has no `make security-check`, dependency-audit command, CI coverage floor or independent model-review gate. Do not cite another repository's checks as evidence here. A future deployment or access model requires its own ADR/FEAT and verification.
