# Verification status

Status after the finding-capacity fix and fresh Studionet deployment.

## Checks and evidence

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **20 passed** locally, including full-capacity benign findings, relevant advisory admission at capacity, terminal replay retention after eviction, and same-GHSA reassessment after a version change.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`) — **11 passed** on Linux CI, including the new capacity-boundary and version-change lifecycle case.
- GenVM lint and SDK validation — passed on Linux CI. Local Windows GenVM lint passes 3 static checks; local SDK validation remains blocked by access to its cached extraction.
- Frontend — `npm test` (**6 passed**) and `npm run build` passed on CI.
- GenLayer SDK receipt inspection confirmed writes return JSON data in `leader_receipt[].result.payload.readable`. The frontend now decodes the leader return and treats known contract errors, missing results, and zero IDs as failures while retaining the finalized transaction link.
- GitHub Actions for the final pushed commit — [run 37533335561](https://github.com/BeatyXO/Spatch/actions/runs/37533335561), **passed** (frontend and contract jobs).
- Fresh Studionet deployment (chain 61999) — finalized at `0xd4feff8ae226ca9198ce503182fdcbac4e3b47997a15f317a289f2681c5fbdbd`. The public deployed source exactly matches the pushed source after newline normalization; schema, protocol, and initial zero counts were verified. Details are in `deployments/studionet.json` and `docs/LIVE_EVIDENCE.md`.
- Fresh two-wallet lifecycle on the capacity-fix deployment — **PASS**. Finalized reads verify creator-only mutation, identity, seal, affected GHSA, deterministic blast radius, same-version replay rejection without assessment growth, patch history/proof clearing, same-GHSA reassessment on version revision 2, and downstream recovery. Transaction hashes and final state are in `docs/LIVE_EVIDENCE.md`.
- Production frontend: [https://spatch-rosy.vercel.app](https://spatch-rosy.vercel.app), alias [https://spatch-six.vercel.app](https://spatch-six.vercel.app). The owner reports redeploying after setting `VITE_CONTRACT_ADDRESS` to the canonical address. This environment could not access the host to verify its HTTP response or served bundle, so the production address is not independently confirmed here.
- In the prior browser session, responsive checks at 1440px desktop and 900px tablet had no horizontal overflow. At 390px, the then-current production CSS had no overflow but hid the wrong-network switch; a correction was subsequently built. The 390px measurement has not been repeated against the owner-reported latest Vercel deployment.
- The prior browser session observed the then-current production JavaScript, wallet menu, and Studionet switch UI without a Spatch runtime exception or failed app asset. That bundle observation predates the owner-reported latest Vercel deployment and does not verify its served address. A MetaMask provider-injection conflict appeared in that session's Chrome extension console.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 `ACTIVE`; Flask 3.0.0 `ACTIVE`)
- Edges: **1** (active)
- Assessments: **6**

## Remaining limitations

- The prior Chrome wallet smoke session verified wrong-network switching, wallet address display/copy, disconnect, and reconnect. It did not verify account switching, rejected chain switching, signature rejection, contract no-op messaging, or a browser-signed finalized transaction. No browser write transaction was sent in that session. Unit tests cover Studionet chain configuration and add/switch/rejection branches; SDK live-chain tests are not browser E2E. These checks have not been repeated against the owner-reported latest Vercel deployment.
- Local Windows GenVM lint passes static checks, but SDK validation cannot access its cached extraction due Windows access denied. Linux CI validation passes.
- Local Direct Mode is blocked on this Windows host by SDK temp-file cleanup (`PermissionError: [WinError 32]`); Linux CI Direct Mode passes all 11 tests.
- The capacity-boundary abuse scenario is proven by the Direct Mode behavioral test; the live run verified the full real-advisory patch lifecycle on the fresh deployment.

## Security-state proofs

- A `NOT_AFFECTED` result for one GHSA cannot clear another advisory's `AFFECTED` finding: Direct Mode coverage passes.
- Identity verification cannot clear vulnerability or dependency recheck state: Direct Mode and current live reads pass.
- Patch identity alone does not establish security safety: the current live component remained `SECURITY_REASSESS_REQUIRED` until the same GHSA was reassessed against version revision 2.
- `UNRESOLVED` findings can be retried safely; terminal findings remain replay-protected: Direct Mode coverage passes.
- Permissionless benign advisory traffic cannot permanently consume the finding bound: the 11-test Direct Mode suite fills all 32 slots with `NOT_AFFECTED` records, admits a relevant affected GHSA by evicting a benign entry, preserves its replay key, stages a patch with history, and reassesses the same GHSA on the new version revision as `NOT_AFFECTED`.
- Downstream recovery stays blocked until every direct dependency is `ACTIVE`: Direct Mode and the current live lifecycle pass.
