# Verification status

Status after the finding-capacity fix and fresh Studionet deployment.

## Checks and evidence

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **20 passed** locally, including full-capacity benign findings, relevant advisory admission at capacity, terminal replay retention after eviction, and same-GHSA reassessment after a version change.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) — **11 passed** on Linux CI, including the new capacity-boundary and version-change lifecycle case.
- GenVM lint and SDK validation — passed on Linux CI. Local Windows GenVM lint passes 3 static checks; local SDK validation remains blocked by access to its cached extraction.
- Frontend — `npm test` (**6 passed**) and `npm run build` passed on CI.
- GenLayer SDK receipt inspection confirmed writes return JSON data in `leader_receipt[].result.payload.readable`. The frontend now decodes the leader return and treats known contract errors, missing results, and zero IDs as failures while retaining the finalized transaction link.
- GitHub Actions for pushed commit `02677b85fa7b3f3f9311583611bb4cc1c4919825` — [run 37529700200](https://github.com/BeatyXO/Spatch/actions/runs/37529700200), **passed** (frontend and contract jobs).
- Fresh Studionet deployment (chain 61999) — finalized at `0xd4feff8ae226ca9198ce503182fdcbac4e3b47997a15f317a289f2681c5fbdbd`. The public deployed source exactly matches the pushed source after newline normalization; schema, protocol, and initial zero counts were verified. Details are in `deployments/studionet.json` and `docs/LIVE_EVIDENCE.md`.
- Fresh two-wallet lifecycle on the capacity-fix deployment — **pending**. The prior full live lifecycle remains archived evidence for the superseded contract only.
- Production frontend [https://spatch-rosy.vercel.app](https://spatch-rosy.vercel.app) and alias [https://spatch-six.vercel.app](https://spatch-six.vercel.app) remain available, but the Vercel environment must be updated to `VITE_CONTRACT_ADDRESS=0x2e517eE9ABCB8f71bD3B8251315A3013C3e69cd6` and redeployed before they target the new contract.
- Responsive checks at 1440px desktop and 900px tablet had no horizontal overflow. At 390px, the earlier production CSS also had no overflow but hid the wrong-network switch; the correction is in the current production CSS bundle. The 390px measurement was not repeated after that correction, so final mobile layout is not marked browser-verified.
- Production JavaScript includes the canonical contract and wallet menu / Studionet switch UI. No Spatch runtime exception or failed app asset was observed. A MetaMask provider-injection conflict appeared in the Chrome extension console during the session.

## Final live counts

- Projects: **0** on the fresh deployment at initial readback
- Components: **0**
- Edges: **0**
- Assessments: **0**

## Remaining limitations

- Chrome wallet smoke checks were partial: the wrong-network state and switch control were visible; clicking it changed the app to Studionet and displayed the connected account. The wallet menu showed the full address, Copy address produced “Wallet address copied”, Disconnect returned the UI to Connect wallet, and reconnect later reported “Wallet connected to Studionet.” Account switching, rejected chain switching, signature rejection, contract no-op messaging, and a browser-signed finalized transaction were not verified. No browser write transaction was sent. Unit tests cover Studionet chain configuration and add/switch/rejection branches; SDK live-chain tests are not browser E2E.
- Vercel must be redeployed with `VITE_CONTRACT_ADDRESS=0x2e517eE9ABCB8f71bD3B8251315A3013C3e69cd6` to serve the new contract.
- Local Windows GenVM lint passes static checks, but SDK validation cannot access its cached extraction due Windows access denied. Linux CI validation passes.
- Local Direct Mode is blocked on this Windows host by SDK temp-file cleanup (`PermissionError: [WinError 32]`); Linux CI Direct Mode passes all 11 tests.
- The full live lifecycle for the newly deployed capacity fix has not yet run. Existing funded author and observer accounts belong to other project aliases; use is awaiting explicit confirmation for those exact wallets.

## Security-state proofs

- A `NOT_AFFECTED` result for one GHSA cannot clear another advisory's `AFFECTED` finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode coverage passes; previous live evidence is for the superseded deployment.
- Patch identity alone does not establish security safety: Direct Mode covers the state transition; the prior live proof is archived for the earlier deployment.
- `UNRESOLVED` findings can be retried safely; terminal findings remain replay-protected: Direct Mode coverage passes.
- Permissionless benign advisory traffic cannot permanently consume the finding bound: the 11-test Direct Mode suite fills all 32 slots with `NOT_AFFECTED` records, admits a relevant affected GHSA by evicting a benign entry, preserves its replay key, stages a patch with history, and reassesses the same GHSA on the new version revision as `NOT_AFFECTED`.
- Downstream recovery stays blocked until every direct dependency is `ACTIVE`: Direct Mode coverage passes; the previous live proof is archived for the earlier deployment.
