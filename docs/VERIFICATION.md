# Verification status

Status after the security-state refactor and fresh Studionet deployment.

## Green checks

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **19 passed**.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) — **10 passed** on Linux CI.
- GenVM lint — **3 checks passed**; GenVM SDK/schema validation passed on Linux CI.
- Frontend — `npm test` **6 passed** (action-state and Studionet wallet-switch cases); `npm run build` passed; lockfile install uses `npm ci` in CI.
- GitHub Actions validates the exact submitted `main` commit. The final run includes Python tests, GenVM lint and validation, Direct Mode, frontend tests and build: [Actions runs](https://github.com/BeatyXO/Spatch/actions).
- Fresh Studionet deployment (chain 61999) — finalized; schema verified and deployed source SHA-256 matches current `contracts/spatch.py` after newline normalization. Address/source relationship is in `deployments/studionet.json`.
- Fresh two-wallet lifecycle — **PASS**. All listed writes were finalized and read back, including unauthorized/stale no-ops, identity, seal, vulnerable finding, replay protection, blocked recovery, patch/history/proof clearing, same-GHSA new-version reassessment, identity-vs-recheck proof, and downstream recovery. See `docs/LIVE_EVIDENCE.md`.
- The GenLayer JS browser adapter uses finalized reads and waits for finalized writes; no-op contract returns are surfaced as failures. Wallet change and wrong-network handling are implemented and frontend tests/build pass.
- Production frontend: [https://spatch-rosy.vercel.app](https://spatch-rosy.vercel.app) returned HTTP 200 in the production check. Chrome rendered the branded app, loaded Project 1 from finalized reads, and showed 1 sealed project, 2 components, 1 edge, 6 assessments. Jinja2 3.1.5 and Flask 3.0.0 are ACTIVE; Jinja2 3.1.4 and its AFFECTED finding appear under historical state. The contract link points to the canonical Studionet explorer address.
- Responsive browser checks: desktop 1440px and tablet 900px; mobile 390px after fixing the hidden wrong-network switch control. All checked sizes have no horizontal page overflow. The injected account menu could not be opened because there was no usable wallet account.
- Production JavaScript was checked for the canonical contract address and the wallet menu / Studionet switch UI. Browser console errors came from the MetaMask extension failing to inject `window.ethereum` in the presence of another provider; no Spatch runtime exception or failed app asset was observed.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 active; Flask 3.0.0 active)
- Edges: **1** (active)
- Assessments: **6**

## Remaining limitations

- Wallet-signed browser E2E remains **not run**. Chrome had no usable injected `window.ethereum` provider; MetaMask logged a provider-injection conflict. Account connection, copy/disconnect against a live wallet, actual chain switching/add-chain and rejection prompts, account changes, signature rejection, no-op transaction UX, and a browser-signed finalized write therefore remain unverified. Unit cases cover Studionet chain configuration and the add/switch/rejection branches. SDK live-chain tests are not browser E2E.
- The production host currently serves the canonical contract bundle. Future deploys must preserve `VITE_CONTRACT_ADDRESS=0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`.
- Local Windows GenVM lint passes lint, but local SDK validation cannot access its cached extraction due a Windows access-denied condition. Linux CI validation passed.
- Local Windows Vite/Vitest required running outside the restricted sandbox; the frontend tests and build passed there and in Linux CI.
- The live runner encountered a transient RPC HTML response while waiting on the post-patch assessment. The already-submitted tx was separately confirmed FINALIZED and the runner resumed from finalized state without resubmission; the complete lifecycle passed.

## Security-state proofs

- A NOT_AFFECTED finding for one GHSA cannot clear another advisory's AFFECTED finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode and live reads pass.
- Patch identity alone does not establish security safety: live state remained `SECURITY_REASSESS_REQUIRED` until the same GHSA was reassessed.
- UNRESOLVED findings can be safely retried; terminal findings remain replay-protected: Direct Mode coverage passes.
- Downstream recovery remains blocked until every direct dependency is ACTIVE: Direct Mode and live lifecycle pass.
