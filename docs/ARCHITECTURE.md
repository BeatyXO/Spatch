# Spatch architecture

Spatch is a version-aware dependency security graph for GenLayer. It deliberately separates objective source identity, semantic advisory applicability, and deterministic state propagation.

## State machine

```text
DRAFT PROJECT
  └─ component PENDING_IDENTITY
       └─ deps.dev strict identity consensus
            └─ ACTIVE

all components ACTIVE + at least one dependency edge
  └─ SEALED PROJECT
       └─ assess GHSA
            ├─ AFFECTED      → VULNERABLE → deterministic dependents RECHECK_REQUIRED
            ├─ NOT_AFFECTED  → ACTIVE
            └─ UNRESOLVED    → UNRESOLVED / no optimistic safety claim

VULNERABLE / RECHECK_REQUIRED / UNRESOLVED
  └─ patch_component(new_version)
       ├─ old version appended to bounded immutable history
       ├─ current version becomes PATCH_PENDING
       └─ all identity proof cleared
            └─ verify_patch
                 └─ ACTIVE only after exact deps.dev identity proof
                      └─ same GHSA may be assessed again at the new revision
```

## Three evidence layers

1. **Component identity** — exact ecosystem/name/version is checked against `api.deps.dev`. This uses strict equality on a canonical structured projection.
2. **Advisory applicability** — Spatch constructs exact OSV and GitHub Advisory Database URLs from a bounded GHSA identifier. Leader and validators independently fetch both sources and independently judge the exact locked component versions. A custom validator accepts only matching decision-critical projections.
3. **Blast radius** — after consensus, graph propagation is deterministic. No web or LLM call decides which dependent nodes are traversed.

## Why the replay key is revision scoped

The key is:

```text
project_id : component_id : component_revision : advisory_id
```

An advisory is not globally burned. If a vulnerable component is replaced with a new version, the component version revision changes and the exact same advisory can be reassessed against the replacement. This is necessary to prove that a patch actually moved the component outside the affected range.

## Why patch history is preserved

`patch_component` never overwrites the previous security state without trace. It appends the previous version, revision, status, advisory ID, assessment ID and retirement time to a bounded history before changing the current version. The new version then loses all identity proof until it is independently verified.

## Boundedness

- max components per project: 16
- max dependency edges per project: 32
- max retired versions per component: 8
- source bodies: 180 KB maximum
- user text and version fields are bounded

These limits keep traversal and storage growth explicit and reviewer-auditable.
