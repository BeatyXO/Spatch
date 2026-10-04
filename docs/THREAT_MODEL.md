# Threat model

## Protected consequence

A software component should only become `VULNERABLE` when validators agree that an exact GHSA advisory applies to the exact locked component version. Only deterministic contract logic may then propagate `RECHECK_REQUIRED` to dependents.

## Attacker controls

- project title and component metadata they submit;
- call timing and transaction ordering;
- which supported GHSA identifier they ask Spatch to assess;
- inert text present in upstream advisory descriptions;
- repeated, stale and cross-object transactions.

## Attacker does not control

- the authority hosts and URL shapes used for deps.dev, OSV and GitHub Advisory Database;
- the exact component revision bound into an assessment;
- independent validator source fetches;
- the contract's deterministic dependency traversal;
- bounded state transitions and replay key construction.

## Core invariants

1. The deployer receives no privileged assessment power.
2. Project construction is creator-only; identity and advisory assessment are permissionless.
3. User input can select a bounded GHSA ID but cannot supply an arbitrary evidence URL.
4. A project cannot seal until every component has exact, current identity proof and the graph contains a dependency edge.
5. Advisory consensus is bound to component ID, component revision, exact version and exact GHSA ID.
6. Source failure, malformed identity, model-schema failure or validator disagreement must not optimistically mark a component safe.
7. A vulnerable component causes deterministic downstream recheck state; dependents are not automatically declared vulnerable.
8. A patch retires the previous version into history and clears identity proof before the replacement can become active.
9. Replay protection is version-revision-scoped, allowing the same advisory to be legitimately reassessed after a version change.
10. Graph writes are bounded and cycles are unreachable because a dependency must have an older component ID than the component that consumes it.
11. Spatch holds no funds and does not claim to replace professional security review.
