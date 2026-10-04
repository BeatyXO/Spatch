# Verification status

Status after the advisory-scoped security-state refactor and fresh Studionet deployment.

## Checks and evidence

- Lightweight contract/architecture suite: `python -m pytest tests -q` â€” **19 passed** locally.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) â€” **10 passed** on Linux CI.
- GenVM lint â€” **3 checks passed**; GenVM SDK/schema validation passed on Linux CI.
- Frontend — `npm test` **6 passed**; `npm run build` passed. `npm audit` reports **0 vulnerabilities** after updating Vitest to 4.1.11.
- GenLayer SDK receipt inspection confirmed writes return JSON data in `leader_receipt[].result.payload.readable`. The frontend now decodes the leader return and treats known contract errors, missing results, and zero IDs as failures while retaining the finalized transaction link.
- GitHub Actions validates the submitted `main` commit with Python tests, GenVM lint and validation, Direct Mode, frontend tests, and build: [Actions runs](https://github.com/BeatyXO/Spatch/actions).
- Fresh Studionet deployment (chain 61999) — finalized; live `getContractCode` readback matches the tracked source after newline normalization. Source digest and deployment identity are in `deployments/studionet.json`.
- Fresh two-wallet lifecycle — **PASS**. All listed writes were finalized and read back, including unauthorized/stale no-ops, identity, seal, vulnerable finding, replay protection, blocked recovery, patch/history/proof clearing, same-GHSA new-version reassessment, identity-vs-recheck proof, and downstream recovery. See `docs/LIVE_EVIDENCE.md`.
- The production frontend [https://spatch-rosy.vercel.app](https://spatch-rosy.vercel.app) returned HTTP 200. It rendered Project 1 from finalized reads with the canonical Studionet explorer address. Responsive checks at 1440px, 900px, and 390px showed no horizontal overflow.
- Production JavaScript was checked for the canonical contract address and the wallet menu / Studionet switch UI. Chrome had no usable `window.ethereum` provider, so injected-wallet E2E remains unverified.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 active; Flask 3.0.0 active)
- Edges: **1** (active)
- Assessments: **6**

## Remaining limitations

- Wallet-signed browser E2E remains **not run**. Chrome had no usable injected `window.ethereum` provider; account connection, live chain switching/add-chain and rejection prompts, account changes, signature rejection, and browser-signed finalized writes remain unverified. Unit cases cover Studionet chain configuration and add/switch/rejection branches. SDK live-chain tests are not browser E2E.
- The production host serves the canonical contract bundle. Future deploys must preserve `VITE_CONTRACT_ADDRESS=0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`.
- Local Windows GenVM lint passes static checks, but SDK validation cannot access its cached extraction due Windows access denied. Linux CI validation passes.
- Local Direct Mode is blocked on this Windows host by SDK temp-file cleanup (`PermissionError: [WinError 32]`); Linux CI Direct Mode passes.
- The live runner encountered a transient RPC HTML response while polling. The submitted transaction was separately confirmed `FINALIZED`; the runner resumed without resubmitting, and the complete lifecycle passed.

## Security-state proofs

- A `NOT_AFFECTED` result for one GHSA cannot clear another advisory's `AFFECTED` finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode and live reads pass.
- Patch identity alone does not establish security safety: the live component remained `SECURITY_REASSESS_REQUIRED` until reassessment of the same GHSA.
- `UNRESOLVED` findings can be retried safely; terminal findings remain replay-protected: Direct Mode coverage passes.
- Downstream recovery stays blocked until every direct dependency is `ACTIVE`: Direct Mode and live lifecycle pass.
