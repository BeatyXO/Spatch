# Verification status

Status after the security-state refactor. Historical deployment evidence applies only to the pre-refactor source; the current implementation is not deployed.

## Current checks

- Lightweight contract/architecture suite: `python -m pytest tests -q` — **19 passed** locally.
- GenVM lint and SDK/schema validation passed on Linux CI through commit `f1aff49`; that run's Direct Mode job failed. The latest pushed commit `e008b24` adds bounded result-count diagnostics; CI is pending.
- Frontend `npm ci`, `npm test`, and `npm run build` passed on Linux CI for the refactor commits. Windows Vite/Vitest startup is blocked by sandbox access denial while esbuild reads above the workspace.
- Local Windows GenVM lint passes its lint stage; its SDK validation cannot access the cached SDK extraction. Linux CI validation is authoritative.
- Direct Mode currently has a failing patch reassessment lifecycle case, so no current official Direct Mode pass is claimed.

## Historical deployment counts (pre-refactor)

The retired deployment recorded 1 sealed project, 2 components, 1 edge, and 6 assessments. These counts are not evidence for the current source.

## Outstanding verification

- Diagnose and pass the official Direct Mode post-patch same-GHSA reassessment case.
- Run the full two-wallet lifecycle on a fresh Studionet (61999) deployment of the current commit, then replace the historical-only evidence with fresh finalized hashes and readbacks.
- Browser-wallet E2E is not run because the available in-app browser has no injected wallet or extension. This is separate from SDK/live-chain verification.
- Production frontend hosting is the user's task. No production URL or HTTP 200 result is claimed. Build with `VITE_CONTRACT_ADDRESS` set to the eventual current deployment address.
- A final green Actions run and clean final commit remain outstanding.

See [historical live evidence](LIVE_EVIDENCE.md) for the retired deployment and its clearly labeled pre-refactor record.
