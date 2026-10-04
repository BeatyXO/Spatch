# Verification status

Verification snapshot for the supplied Spatch tree in the Codex sandbox on 2026-10-04. This is not a release or deployment claim.

## Completed

- `python -m pytest tests -q`: **15 passed**.
- `python -m py_compile contracts/spatch.py`: passed.
- `genvm-lint check contracts/spatch.py` (with `PYTHONUTF8=1`): lint passed (**3 checks**).

## Blocked or not run

- GenVM SDK validation: the linter could not extract its SDK archive; Windows returned `Access denied` under `%LOCALAPPDATA%\\.cache\\genvm-linter\\extracted`.
- GitHub: `gh auth status` reports both configured GitHub tokens are invalid. No remote repository was created and no push or Actions run occurred.
- Local Git commits: the ZIP folder and newly created `.git` directory are owned by the host account. The sandbox account cannot write `.git/config` or `.git/index`; therefore the supplied baseline could not be committed and this worktree cannot be certified clean.
- Direct Mode: no additional `genlayer-test` tests were added or executed.
- Frontend: `npm install` did not complete in this environment. `npm test` and `npm run build` were attempted but failed because `vitest` and `tsc` are not installed. No lockfile was generated.
- Real GHSA fixture, Studionet deployment (chain ID 61999), fresh two-wallet lifecycle, browser-wallet E2E, production hosting, and GitHub Actions: not performed. There are no wallet/provider/hosting credentials available in the process environment.

The deployment manifest remains `pre-deployment` and `docs/LIVE_EVIDENCE.md` remains an explicit not-run placeholder. No address, transaction hash, test result, or production URL has been fabricated.
