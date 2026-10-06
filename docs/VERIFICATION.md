# Verification status

Status after the advisory-scoped security-state refactor and fresh Studionet deployment.

## Checks and evidence

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **20 passed** locally, including full-capacity benign findings, relevant advisory admission at capacity, terminal replay retention after eviction, and same-GHSA reassessment after a version change.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) — **10 passed** on the previously submitted commit; this fix adds a capacity-boundary lifecycle case for the next CI run.
- GenVM lint — **3 static checks passed** locally. This Windows host could not complete SDK validation because the cached GenVM archive is unavailable; schema and Direct Mode results for this fix are pending CI.
- Frontend — `npm test` **6 passed**; `npm run build` passed. `npm audit` reports **0 vulnerabilities** after updating Vitest to 4.1.11.
- GenLayer SDK receipt inspection confirmed writes return JSON data in `leader_receipt[].result.payload.readable`. The frontend now decodes the leader return and treats known contract errors, missing results, and zero IDs as failures while retaining the finalized transaction link.
- GitHub Actions validates the submitted `main` commit with Python tests, GenVM lint and validation, Direct Mode, frontend tests, and build: [Actions runs](https://github.com/BeatyXO/Spatch/actions).
- Fresh Studionet deployment (chain 61999) — finalized; live `getContractCode` readback matches the tracked source after newline normalization. Source digest and deployment identity are in `deployments/studionet.json`.
- Fresh two-wallet lifecycle — **PASS**. All listed writes were finalized and read back, including unauthorized/stale no-ops, identity, seal, vulnerable finding, replay protection, blocked recovery, patch/history/proof clearing, same-GHSA new-version reassessment, identity-vs-recheck proof, and downstream recovery. See `docs/LIVE_EVIDENCE.md`.
- The requested production frontend [https://spatch-rosy.vercel.app](https://spatch-rosy.vercel.app) and alias [https://spatch-six.vercel.app](https://spatch-six.vercel.app) both returned HTTP 200 and served the same latest JavaScript/CSS assets with the canonical contract address. Chrome rendered the brand and loaded Project 1 from finalized reads: sealed, 2 active components, 1 dependency edge and 6 assessments. Historical Jinja2 3.1.4 AFFECTED state is distinguished from current 3.1.5 NOT_AFFECTED/ACTIVE state. The explorer link points to the canonical contract. This is a single-screen client app; non-root deep links are not implemented and return 404.
- Responsive checks at 1440px desktop and 900px tablet had no horizontal overflow. At 390px, the earlier production CSS also had no overflow but hid the wrong-network switch; the correction is in the current production CSS bundle. The 390px measurement was not repeated after that correction, so final mobile layout is not marked browser-verified.
- Production JavaScript includes the canonical contract and wallet menu / Studionet switch UI. No Spatch runtime exception or failed app asset was observed. A MetaMask provider-injection conflict appeared in the Chrome extension console during the session.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 active; Flask 3.0.0 active)
- Edges: **1** (active)
- Assessments: **6**

## Remaining limitations

- Chrome wallet smoke checks were partial: the wrong-network state and switch control were visible; clicking it changed the app to Studionet and displayed the connected account. The wallet menu showed the full address, Copy address produced “Wallet address copied”, Disconnect returned the UI to Connect wallet, and reconnect later reported “Wallet connected to Studionet.” Account switching, rejected chain switching, signature rejection, contract no-op messaging, and a browser-signed finalized transaction were not verified. No browser write transaction was sent. Unit tests cover Studionet chain configuration and add/switch/rejection branches; SDK live-chain tests are not browser E2E.
- The production host serves the canonical contract bundle. Future deploys must preserve `VITE_CONTRACT_ADDRESS=0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`.
- Local Windows GenVM lint passes static checks, but SDK validation cannot access its cached extraction due Windows access denied. Linux CI validation passes.
- Local Direct Mode is blocked on this Windows host by SDK temp-file cleanup (`PermissionError: [WinError 32]`); Linux CI Direct Mode passes.
- The live runner encountered a transient RPC HTML response while polling. The submitted transaction was separately confirmed `FINALIZED`; the runner resumed without resubmitting, and the complete lifecycle passed.

## Security-state proofs

- A `NOT_AFFECTED` result for one GHSA cannot clear another advisory's `AFFECTED` finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode and live reads pass.
- Patch identity alone does not establish security safety: the live component remained `SECURITY_REASSESS_REQUIRED` until reassessment of the same GHSA.
- `UNRESOLVED` findings can be retried safely; terminal findings remain replay-protected: Direct Mode coverage passes.
- Permissionless benign advisory traffic cannot permanently consume the finding bound: a full set of `NOT_AFFECTED` findings admits a new relevant advisory by evicting only a benign cache entry, while its assessment and replay key remain; a patch archives prior references and resets the replacement revision's findings. The 20-test local behavioral suite proves a vulnerable result and a same-GHSA post-patch reassessment across this boundary.
- Downstream recovery stays blocked until every direct dependency is `ACTIVE`: Direct Mode and live lifecycle pass.
