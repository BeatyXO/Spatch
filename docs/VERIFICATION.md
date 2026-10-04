# Verification status

Status after the security-state refactor and fresh Studionet deployment.

## Green checks

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **19 passed**.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) — **10 passed** on Linux CI.
- GenVM lint — **3 checks passed**; GenVM SDK/schema validation passed on Linux CI.
- Frontend — `npm test` **3 passed**; `npm run build` passed; lockfile install uses `npm ci` in CI.
- Final GitHub Actions run: [37229332642](https://github.com/BeatyXO/Spatch/actions/runs/37229332642) — **success** for source commit `a64b1fee698aa9112b150d28921552825a5cc30e`.
- Fresh Studionet deployment (chain 61999) — finalized; schema verified and deployed source SHA-256 matches current `contracts/spatch.py` after newline normalization. Address/source relationship is in `deployments/studionet.json`.
- Fresh two-wallet lifecycle — **PASS**. All listed writes were finalized and read back, including unauthorized/stale no-ops, identity, seal, vulnerable finding, replay protection, blocked recovery, patch/history/proof clearing, same-GHSA new-version reassessment, identity-vs-recheck proof, and downstream recovery. See `docs/LIVE_EVIDENCE.md`.
- The GenLayer JS browser adapter uses finalized reads and waits for finalized writes; no-op contract returns are surfaced as failures. Wallet change and wrong-network handling are implemented and frontend tests/build pass.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 active; Flask 3.0.0 active)
- Edges: **1** (active)
- Assessments: **6**

## Remaining limitations

- Injected-wallet browser E2E was not run: the available in-app browser has no `window.ethereum` provider or wallet extension. Wallet-signed UI journeys, wrong-network/account switching in an extension, and mobile browser-wallet checks remain unverified. SDK live-chain tests are not called browser E2E.
- Production frontend hosting is the owner's task. No production URL or HTTP 200 check is claimed. Build/deploy using `VITE_CONTRACT_ADDRESS=0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`.
- Local Windows GenVM lint passes lint, but local SDK validation cannot access its cached extraction due a Windows access-denied condition. Linux CI validation passed.
- Local Windows Vite/Vitest startup is blocked by sandbox access denial when esbuild attempts to read above the workspace. Linux CI ran `npm ci`, tests and build successfully.
- The live runner encountered a transient RPC HTML response while waiting on the post-patch assessment. The already-submitted tx was separately confirmed FINALIZED and the runner resumed from finalized state without resubmission; the complete lifecycle passed.

## Security-state proofs

- A NOT_AFFECTED finding for one GHSA cannot clear another advisory's AFFECTED finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode and live reads pass.
- Patch identity alone does not establish security safety: live state remained `SECURITY_REASSESS_REQUIRED` until the same GHSA was reassessed.
- UNRESOLVED findings can be safely retried; terminal findings remain replay-protected: Direct Mode coverage passes.
- Downstream recovery remains blocked until every direct dependency is ACTIVE: Direct Mode and live lifecycle pass.
