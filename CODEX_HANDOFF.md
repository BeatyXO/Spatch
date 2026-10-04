# Codex handoff — finish Spatch for submission

You are taking over a prebuilt GenLayer project named **Spatch**. Work from this repository as the canonical starting point. Do not redesign it into a different project and do not weaken the security invariants just to make tests pass.

## Goal

Finish Spatch into a submission-grade GenLayer Intelligent Contract project, push it to a new GitHub repository named `Spatch` under the authenticated GitHub account, deploy the final contract to **stable GenLayer Studionet (chain ID 61999)**, complete live and browser evidence, deploy the frontend, and leave `main` clean and fully documented.

Spatch is a version-aware dependency security graph. It verifies exact package versions with deps.dev, assesses exact GHSA advisories using OSV + GitHub Advisory Database evidence with custom validator consensus, deterministically propagates security recheck state through dependency edges, preserves retired vulnerable versions in history, requires fresh identity proof after a patch, allows the same GHSA again only after the component's `version_revision` changes, and lets downstream nodes clear `RECHECK_REQUIRED` deterministically once dependencies are stable.

## Current pre-handoff state

- Main contract: `contracts/spatch.py`
- Local mock/architecture suite: **15 passed** with `python -m pytest tests -q`
- Stable SDK target in frontend: `genlayer-js==1.1.8`
- Stable Direct Mode package target: `genlayer-test==0.29.2`
- Frontend: React/Vite, full lifecycle UI, shades-of-blue design, glass panels, **Comic Sans** globally
- Evidence/docs already present: architecture, threat model, source manifest, verification status, live evidence placeholder, Studionet deployment placeholder
- Live runner template: `scripts/run_live_e2e.mjs`
- CI workflow present
- No contract address, tx hash, production URL or live evidence has been fabricated

## Non-negotiable architecture invariants

Preserve these unless a real GenLayer SDK/linter limitation forces a narrowly documented implementation change:

1. No deployer/admin security-review privilege.
2. Project/graph construction is creator-only; verification and security assessments are permissionless.
3. No arbitrary evidence URLs from users.
4. Exact package identity must be verified before project sealing.
5. Advisory IDs are bounded GHSA IDs.
6. Advisory evidence comes from both OSV and GitHub Advisory Database.
7. Semantic advisory applicability uses independent validator work; do not reduce it to trusting a leader schema check.
8. Decision-critical fields must be bound to component ID, overall component revision, `version_revision`, exact version and advisory ID.
9. Blast-radius traversal stays deterministic outside nondeterministic blocks.
10. Same-GHSA replay is keyed by `project_id:component_id:version_revision:advisory_id`. Repeating the same GHSA against the same version revision must not create a new assessment.
11. `patch_component` must preserve the previous version/security state in history, increment `version_revision`, clear identity proof, and require `verify_patch` before the replacement is active.
12. The same GHSA must become eligible again after a true version change.
13. Downstream `RECHECK_REQUIRED` recovery must be explicit through `reassess_dependency`; do not silently auto-clear it.
14. Fail closed on malformed/unavailable source data, model-schema failure and validator disagreement.
15. Keep graph/history/source-body bounds explicit.

## Work sequence

### A. Repository and audit

1. Create/use a GitHub repository named `Spatch` under the authenticated account. Do not touch unrelated repositories.
2. Commit the supplied tree first so the handoff baseline is preserved.
3. Run `python -m pytest tests -q`; baseline expectation is **15 passed**.
4. Install current stable tooling for the Studionet stack. Start with the pinned stable lines already present (`genlayer-test==0.29.2`, `genlayer-js==1.1.8`) unless current official GenLayer docs show a newer stable release compatible with chain 61999. Do not switch the final deployment to Studio-dev 61997.
5. Run `genvm-lint check contracts/spatch.py`. Fix every lint/SDK validation error. Re-run until clean.
6. Run Python compilation and any GenVM schema validation available.

### B. Real GenLayer Direct Mode tests

Add official `genlayer-test` Direct Mode coverage in addition to the existing lightweight mock tests. Cover at minimum:

- project creation;
- creator-only component/dependency mutation;
- exact component identity success and source failure;
- unsupported ecosystem / malformed inputs;
- acyclic dependency ordering;
- seal rejection before all component identities are current;
- successful sealing;
- positive advisory applicability;
- unrelated/not-affected component;
- custom-validator agreement;
- custom-validator disagreement/fail-closed behavior;
- deterministic blast-radius propagation;
- stale revision rejection;
- same-version GHSA replay rejection with no new assessment;
- patch history preservation;
- identity proof cleared on patch;
- patch verification;
- same GHSA allowed after `version_revision` changes;
- patched version judged not affected using evidence;
- downstream `reassess_dependency` blocked while upstream remains vulnerable;
- downstream recovery once dependencies are active;
- bounded component/edge/history behavior.

Do not delete the existing 15-test suite unless equivalent/better coverage replaces it.

### C. Frontend verification

1. In `frontend/`, install dependencies and generate/commit `package-lock.json`.
2. Run `npm test` and `npm run build`; fix all TypeScript/SDK issues.
3. If the stable `genlayer-js` API differs from the prebuilt adapter, update `frontend/src/genlayer.ts` while keeping finalized-state reads and fee estimation correct for Studionet.
4. Preserve the requested visual direction: **shades of blue**, pleasing/clean visual hierarchy, responsive layout, **Comic Sans** font. Improve usability if needed, but do not replace it with a generic template or another font.
5. Ensure every contract write in the final schema is reachable from the UI, including `reassess_dependency`.
6. After deployment, set `VITE_CONTRACT_ADDRESS` to the final canonical address and ensure the production bundle contains that address and no retired address.

### D. Choose a real live fixture before deployment evidence

Find a real public GHSA fixture with a clean affected → fixed lifecycle for a supported ecosystem (PyPI/npm/Cargo/etc.). Verify **before sending live transactions** that:

- deps.dev recognizes the vulnerable version;
- deps.dev recognizes the fixed version;
- OSV has the exact GHSA object;
- GitHub Advisory Database has the exact same GHSA;
- the vulnerable version is clearly in the affected range;
- the fixed version is clearly outside the affected range;
- the second component used as a dependent has a valid exact version.

Prefer a simple, stable advisory with unambiguous version ranges. Record the chosen fixture and why it is reliable in `docs/SOURCE_MANIFEST.md` or a dedicated fixture section. Do not invent an advisory just to satisfy the runner.

### E. Deploy final contract to stable Studionet 61999

1. Deploy only after lint + Direct Mode + frontend tests/build are green.
2. Final network: **GenLayer Studionet, chain ID 61999**.
3. Preserve the no-argument constructor unless a real SDK requirement forces otherwise.
4. Verify deployed schema includes all intended write/view methods.
5. Verify deployed source/code corresponds to the final tracked contract source. Record source hash/blob/commit evidence where available.
6. Update `deployments/studionet.json` with the real final address and status.

### F. Fresh live two-wallet lifecycle

Run from a fresh final deployment. Use separate author and observer wallets; if practical, keep deployer distinct from both. Never expose private keys in logs or commits.

Complete and record finalized transaction hashes/readbacks for:

1. create project;
2. add vulnerable dependency component;
3. add dependent application/framework component;
4. add dependency edge;
5. observer verifies dependency identity;
6. observer verifies dependent identity;
7. creator seals project;
8. unauthorized graph mutation attempt leaves state unchanged;
9. stale-revision path leaves state unchanged;
10. assess real GHSA: vulnerable dependency becomes `VULNERABLE` and dependent becomes `RECHECK_REQUIRED`;
11. repeat same GHSA on same version revision: no new assessment/state mutation;
12. creator stages fixed version: old vulnerable version is visibly preserved in `history`, replacement is `PATCH_PENDING`, identity proof is cleared;
13. observer verifies fixed-version identity;
14. observer assesses the **same GHSA** again: only the changed version revision is eligible and the fixed version returns to `ACTIVE`/not affected when live evidence supports that;
15. observer calls `reassess_dependency`: downstream component returns to `ACTIVE` once all direct dependencies are stable;
16. final counts/project/components/assessments read back correctly.

Use `scripts/run_live_e2e.mjs` as a starting runner, but audit its stable-SDK API before running. Fix it rather than blindly trusting the template.

### G. Browser-wallet E2E

Use the actual production-style injected wallet flow (Rabby/MetaMask or the available browser wallet environment) on Studionet. Test every final write method from the UI, not only the SDK runner:

- `create_project`
- `add_component`
- `add_dependency`
- `verify_component`
- `seal_project`
- `assess_advisory`
- `patch_component`
- `verify_patch`
- `reassess_dependency`

Confirm visible UI state against finalized contract reads after each important transition. Test wrong-network/account-change handling and responsive/mobile layout. Do not claim browser evidence if only adapter tests ran.

### H. Production deployment and evidence cleanup

1. Deploy the frontend to the available production host (Vercel is fine if already connected; Cloudflare Pages is also fine).
2. Verify production HTTP 200 and correct final contract address in the served bundle.
3. Replace `docs/LIVE_EVIDENCE.md` with real evidence only.
4. Update `docs/VERIFICATION.md` with exact final test counts and explicit remaining limitations, if any.
5. Update README reviewer path with final explorer and production links.
6. Ensure GitHub Actions is green on the final commit. If package-lock is committed, switch CI from `npm install` to `npm ci`.
7. Remove temporary artifacts, secrets, stale addresses and misleading failed-deployment claims. Keep useful historical debugging only if clearly labeled non-final.
8. Leave `main` clean and pushed.

## Final response required from Codex

Return a concise audit-style completion report containing:

- GitHub repository URL;
- final commit SHA;
- clean worktree confirmation;
- contract address and explorer link;
- stable network/chain ID;
- exact contract test / Direct Mode / frontend test counts;
- GenVM lint/validation result;
- GitHub Actions run link/status;
- production frontend URL;
- chosen real GHSA fixture and package vulnerable/fixed versions;
- key live transaction hashes for advisory impact, patch, same-GHSA post-patch reassessment and downstream recovery;
- browser-wallet E2E result;
- final counts/state summary;
- any remaining limitation that is genuinely unresolved.

Do not fabricate evidence. If a network/provider/browser step cannot be completed, say exactly which one and leave the repository truthful rather than writing a fake PASS.
