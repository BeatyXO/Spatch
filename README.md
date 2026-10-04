# Spatch — Version-aware dependency security intelligence

Spatch is a GenLayer Intelligent Contract that maintains a bounded dependency graph of exact software component versions. It verifies package identity before a graph can be sealed, evaluates GHSA advisories against live OSV + GitHub Advisory Database evidence with independent validator reasoning, deterministically propagates security recheck state to dependent components, and preserves vulnerable version history when a patch is staged.

The design target is **stable GenLayer Studionet, chain ID 61999**. The deployer receives no admin or security-review power. Project creation and graph mutation are creator-only; package identity and security-advisory assessments are permissionless.

## Why Spatch is different

A one-shot vulnerability classifier is easy to build and easy to game. Spatch makes the security decision part of a stateful lifecycle:

```text
create dependency graph
→ independently verify every exact package version
→ seal graph
→ fetch exact GHSA from OSV + GitHub
→ validators judge exact-version applicability
→ deterministic blast-radius propagation
→ retire vulnerable version into history
→ stage replacement version
→ re-verify replacement identity
→ reassess the same GHSA on the new revision
```

The important detail is the final step. Replay protection is scoped to `project:component:version_revision:advisory`, not globally to the project. A patched component therefore gets a legitimate fresh assessment of the same advisory. The old vulnerable version remains auditable in history rather than being silently washed away by adding new evidence.

## Public write methods

- `create_project(title)`
- `add_component(project_id, ecosystem, name, version)`
- `add_dependency(dependent_component_id, dependency_component_id)`
- `verify_component(component_id, expected_revision)`
- `seal_project(project_id)`
- `assess_advisory(project_id, advisory_id)`
- `patch_component(component_id, new_version, expected_revision)`
- `verify_patch(component_id, expected_revision)`

Views: `get_project`, `get_component`, `get_edge`, `get_assessment`, `get_counts`, `get_protocol`.

## Evidence model

**deps.dev** is used for exact component identity. **OSV** and the **GitHub Advisory Database** are both fetched for a GHSA assessment. User input never supplies source URLs. Advisory descriptions are treated as inert evidence. A custom GenLayer validator independently re-runs the source fetch + semantic judgment and accepts only matching decision-critical projections.

See [architecture](docs/ARCHITECTURE.md), [threat model](docs/THREAT_MODEL.md), [source manifest](docs/SOURCE_MANIFEST.md), and [verification status](docs/VERIFICATION.md).

## Local checks

```bash
python -m pytest tests -q
# 15 tests currently pass in the pre-Codex package

pip install genvm-linter
genvm-lint check contracts/spatch.py

cd frontend
npm ci
npm test
npm run build
```

The final three commands require network-installed dependencies and are intentionally listed as Codex release gates. The current chat environment could run the Python mock suite but could not download npm/PyPI packages for linter/frontend execution.

## Frontend direction

The frontend is intentionally distinctive but readable: layered **shades of blue**, blue glassmorphism, compact evidence/status cards, responsive layouts, and **Comic Sans** as the requested application font. It exposes the full intended lifecycle instead of presenting a decorative landing page with disconnected contract controls.

## Deployment status

Pre-deployment. `deployments/studionet.json` and `docs/LIVE_EVIDENCE.md` are placeholders and must only be replaced with real final evidence after deployment. The frontend reads `VITE_CONTRACT_ADDRESS`; no fake contract address is committed.

## Final reviewer path after deployment

1. Create a project.
2. Add a dependency component first, then an application/framework component that depends on it.
3. Verify both exact versions via permissionless `verify_component` calls.
4. Seal the graph.
5. Assess a real GHSA known to affect the dependency version and confirm the dependency becomes `VULNERABLE` while dependents become `RECHECK_REQUIRED`.
6. Stage a fixed version with `patch_component`; confirm the old vulnerable version appears in `history` and the new version is `PATCH_PENDING` with no identity proof.
7. Verify the patch identity.
8. Assess the **same GHSA** against the new component revision and confirm the patched version is `NOT_AFFECTED`/`ACTIVE` when supported by the live evidence.
9. Confirm stale revisions and invalid source/ID paths do not create unsafe state.

Spatch is a security-evidence coordination demo, not a substitute for professional vulnerability management or emergency patch procedures.
