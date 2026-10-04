# Verification status

Final verification status for 2026-10-04. This records verified results and explicit gaps; it is not a claim that browser-wallet and frontend hosting work has been completed.

## Green checks

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **15 passed**.
- Official GenLayer Direct Mode suite (`genlayer-test==0.29.2`, Linux CI) — **8 passed**. Covers full lifecycle, identity/source failures, validator agreement/disagreement, malformed model output, graph ordering/bounds, and history bounds.
- GenVM lint — **3 checks passed**. CI also ran GenVM SDK validation successfully on Linux.
- Frontend: `npm test` — **2 passed**; `npm run build` — **passed**. Vite reports a large JavaScript chunk advisory.
- GitHub Actions — **passed**: [run 37223117765](https://github.com/BeatyXO/Spatch/actions/runs/37223117765).
- Python compilation and `node --check scripts/run_live_e2e.mjs` — passed.
- Final source deployed to Studionet chain ID 61999; deployed source SHA-256 matches `contracts/spatch.py` exactly after newline normalization. See `docs/LIVE_EVIDENCE.md`.
- Fresh two-wallet live lifecycle — **PASS**: assessment, propagation, same-version replay protection, patch history/proof clearing, patch identity verification, same-GHSA reassessment at version revision 2, and deterministic downstream recovery all finalized and read back.
- Local browser preview loaded the final contract's finalized project and rendered the 1/2/1/6 counts, versions, history, edge and active statuses. The Connect action showed the expected “Install or enable an injected wallet such as Rabby or MetaMask” message; `window.ethereum` was absent.
- Production build with `VITE_CONTRACT_ADDRESS` set to the final address — passed; verified that canonical address is embedded in generated bundle.

## Final live counts

- Projects: **1** (sealed)
- Components: **2** (Jinja2 3.1.5 active; Flask 3.0.0 active)
- Edges: **1**
- Assessments: **6**

## Limits and caveats

- Local Windows GenVM lint invocation passes lint but cannot complete SDK validation because the local cache does not contain the expected SDK archive. Linux CI completed validation successfully.
- Local Windows Direct Mode execution remains blocked by `genlayer-test`'s stdin temp-file unlink behavior. The official suite ran and passed on Linux CI.
- Browser-wallet E2E was not run: the connected in-app browser has no injected provider or available wallet extension. Do not treat SDK/live-chain runner results as browser-wallet evidence. Responsive viewport breakpoints, wallet network/account changes, and wallet-signed write methods were not exercised in a wallet-enabled browser.
- Frontend production hosting is not done. The user requested to perform that deployment; set `VITE_CONTRACT_ADDRESS` to the final address in the production host.
- No production URL or HTTP 200 check is claimed.
- Earlier failed/diagnostic deployments are non-canonical; only the address and deployment transaction in `deployments/studionet.json` and `docs/LIVE_EVIDENCE.md` are final.
