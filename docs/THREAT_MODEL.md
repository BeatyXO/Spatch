# Threat model

## Protected consequence

Spatch records advisory-scoped judgments for exact package versions and propagates recheck obligations deterministically through a bounded dependency graph. It must not turn a narrow non-applicability result or package identity check into a global safety claim.

## Attacker controls

- project titles and package metadata supplied during creator-controlled construction;
- transaction ordering, stale revisions, repeated calls, and GHSA choice;
- untrusted advisory descriptions and source responses;
- a leader's proposed semantic output.

## Invariants

1. The deployer has no privileged project review role.
2. Construction and dependency mutation are creator-only; identity verification and advisory assessment are permissionless.
3. Users provide only a bounded GHSA identifier, never arbitrary evidence URLs.
4. Sealing requires exact current identity proof for every component.
5. Advisory output binds component ID, component revision, version revision, GHSA, verdict, reason, and fixed version.
6. Custom validators independently fetch and re-evaluate; disagreement or malformed evidence fails closed.
7. Findings are bounded and advisory/version scoped. A later `NOT_AFFECTED` cannot clear an `AFFECTED` or unresolved finding for another GHSA.
8. Identity verification cannot clear security findings, patch obligations, or dependency recheck state. Patch identity alone is not patch safety.
9. Unresolved findings are retryable; terminal verdicts are immutable for the same version/advisory replay scope.
10. Patch staging preserves old evidence, clears identity proof, increments the version revision, and carries outstanding advisories to the replacement.
11. Downstream recovery requires every direct dependency to have current identity and aggregate `ACTIVE` state.
12. Graph size, source responses, history, findings and carried obligations are bounded. Component ordering makes dependency cycles unreachable.

## Evidence trust and limits

deps.dev provides exact-version identity data. OSV and GitHub Advisory Database provide two structured views of a GHSA, but OSV may derive its entry from GitHub; they are not asserted as independent primary authorities. The independent security check is the custom validator's separate retrieval and semantic re-evaluation. Advisory text is inert input. Spatch does not replace maintainers' emergency response or professional security review.
