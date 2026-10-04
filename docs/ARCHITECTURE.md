# Spatch architecture

Spatch is a bounded, version-aware dependency security graph. It separates package identity, advisory applicability, and deterministic dependency recovery. Identity proves that an exact package version exists; it does not prove security.

## Lifecycle and aggregate state

```text
DRAFT → exact package identity current → SEALED graph
  → advisory evidence + independent validator judgment
  → immutable terminal finding or retryable UNRESOLVED finding
  → deterministic RECHECK_REQUIRED propagation
  → creator stages replacement, old version/findings retained in history
  → replacement identity verified (still SECURITY_REASSESS_REQUIRED)
  → every carried advisory reassessed for the new version revision
  → ACTIVE only after security obligations clear
  → dependent recovery only after all direct dependencies are ACTIVE
```

Each finding is bounded and scoped to component ID, `version_revision`, GHSA, verdict, reason, assessment ID, fixed version, and retry attempts. For the current version, aggregate precedence is `VULNERABLE` if any finding is `AFFECTED`, then `UNRESOLVED`, then `SECURITY_REASSESS_REQUIRED` for carried patch obligations, then `RECHECK_REQUIRED`, then `ACTIVE` only when identity is current. A `NOT_AFFECTED` result applies only to its GHSA and cannot clear another finding.

Identity and security are exposed independently (`identity_status`, `verified_version_revision`, `security_status`, and lifecycle `status`). Calling identity verification cannot clear findings or dependency recheck state. `verify_patch` only establishes replacement identity; it never establishes advisory safety.

Terminal AFFECTED/NOT_AFFECTED results are immutable per project/component/version revision/GHSA. UNRESOLVED outcomes remain visible and may be retried; each retry updates the single finding and increments its bounded-in-practice attempt counter. Terminal outcomes cannot be overwritten by an unresolved retry or another result. A real version change creates a new replay scope.

## Three evidence layers

1. **Identity:** constructed deps.dev endpoint, strict equality against ecosystem/name/version.
2. **Applicability:** constructed OSV and GitHub Advisory Database endpoints. Leader and custom validators independently fetch and re-evaluate both records; decision-critical outputs must match exactly. Validator judgment is independent work, while the upstream records are not necessarily independent authorities.
3. **Blast radius:** deterministic bounded graph traversal after consensus. It does not call a model or network source.

OSV may import or derive a GHSA record from GitHub Advisory Database. The two records are useful structured surfaces, not a claim of two independent primary sources. The independent check is the validator's separate fetch and semantic decision.

## Replay and history

Replay key:

```text
project_id : component_id : version_revision : advisory_id
```

An unresolved result does not consume a terminal replay key. Staging a patch appends the prior version, lifecycle state, finding references, advisory and assessment IDs to bounded history, increments `version_revision`, clears exact identity proof and carries affected/unresolved advisories into a pending list. Reassessing the same GHSA against the new revision is therefore eligible.

## Bounds

- 16 components and 32 edges per project;
- 8 retired versions per component;
- 32 findings and 16 carried advisory obligations per component;
- source-body and user-text limits are explicit in `contracts/spatch.py`.

Dependencies must point from a later-created dependent to an earlier-created dependency, making cycles unreachable by construction.
