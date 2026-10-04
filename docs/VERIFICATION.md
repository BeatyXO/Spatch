# Verification status

Snapshot of the current `main` worktree on 2026-10-04. This is not a release or deployment claim. Changes after baseline commit `22fefe8` are being validated and are not yet pushed.

## Completed locally

- Existing lightweight suite: `python -m pytest tests -q` — **15 passed**.
- Python compilation: `python -m py_compile contracts/spatch.py` — passed.
- GenVM lint: `genvm-lint check contracts/spatch.py` — lint passed (**3 checks**). SDK validation could not finish because the Windows linter cache returned `Access denied` for the extracted runner.
- Frontend dependencies: installed from the manifest; `frontend/package-lock.json` was generated.
- Frontend tests: `npm test` — **2 passed**.
- Frontend production build: `npm run build` — passed with the configured pre-deployment build. Vite reports a large JavaScript chunk advisory.
- Fixture research: [GHSA-gmj6-6f8f-6699](https://github.com/advisories/GHSA-gmj6-6f8f-6699), Jinja2 3.1.4 affected and 3.1.5 fixed, independently confirmed from deps.dev, OSV and GitHub Advisory Database. Flask 3.0.0 is recognized by deps.dev as the dependent candidate. Details are in `docs/SOURCE_MANIFEST.md`.
- Official GenLayer Direct Mode tests: **5 cases added** under `integration/test_direct_mode.py`, covering the core lifecycle, replay, patch and recovery, creator/order checks, failed identity sources, stale revisions, custom-validator agreement/disagreement, malformed model output, and graph bounds. The local `gltest` run is blocked before contract loading by `genlayer-test==0.29.2` raising a Windows `PermissionError` while unlinking its stdin temp file. The test cases are wired into CI for its Linux runner; they are not claimed as locally passing.
- Repository: `https://github.com/BeatyXO/Spatch`; baseline commit `22fefe8` is pushed to `main`.

## Not completed or verified

- The current SDK fixes and test additions are still uncommitted/unpushed; CI has not yet run on them.
- Full GenVM SDK validation/schema verification remains unresolved.
- No final contract has been deployed. `deployments/studionet.json` remains pre-deployment.
- No fresh two-wallet Studionet lifecycle, transaction hashes, browser-wallet E2E, or final explorer readbacks exist.
- No frontend production deployment exists; no final contract address is configured.
- GitHub Actions status for the final source is not yet available.

No address, transaction hash, deployment URL, or live PASS has been fabricated. The live evidence file remains a not-run placeholder.
