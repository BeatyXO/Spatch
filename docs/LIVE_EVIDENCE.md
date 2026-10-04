# Studionet live evidence

**Result: lifecycle PASS on GenLayer Studionet, chain ID 61999.** Evidence below was read from finalized transactions on 2026-10-04 against the fresh final deployment. Author and observer were separate wallets; the deployer was a third wallet.

## Deployment identity

- Contract: `0x3D8ac6480A830b0EC9cdE515D06F29F3364583B1`
- Deployment transaction: `0x4c85655ddccf8328c92bcfc691a9175e884e51538105b967b7e078e09a97e51a`
- Explorer: [Studionet contract](https://explorer-studio.genlayer.com/address/0x3D8ac6480A830b0EC9cdE515D06F29F3364583B1)
- Source SHA-256: `303a1738f0acea6a4358dc0ea44cad9670ae53935d4a1e62dc6458fb78324cd7` (deployed source equals local `contracts/spatch.py` byte-for-byte after newline normalization)
- Git blob: `a0fcc1327998fdb0263c364f993df5ef6d62f0b6`
- Deployment source commit: `3cb79e250965aace51cce14efa7f8369974f49c3` (contract source unchanged in later commits)
- GitHub main currently advances past the source commit for runner/docs/test fixture fixes; see repository history.
- Initial finalized `get_counts`: `projects=0, components=0, edges=0, assessments=0`.

## Wallet roles

- Deployer: `0x7876e9f76f32925c212528d57bc9dfe5e34bcc07`
- Author/project creator: `0xc63e2ca7246c9e784e35ead2238a699a693593d5`
- Observer (identity/advisory/recovery caller): `0x51f8101e212e8a5b71e654cbaad242165ce6ba4d`
- No private keys are included in the repository or this evidence.

## Fixture and finalized lifecycle

Fixture: PyPI `jinja2` 3.1.4 → 3.1.5 with [GHSA-gmj6-6f8f-6699](https://github.com/advisories/GHSA-gmj6-6f8f-6699); dependent: PyPI `flask` 3.0.0. Exact identity evidence was fetched from deps.dev. Advisory evidence came from OSV and GitHub Advisory Database. Independent validator agreement produced `ASSESSED`.

| Operation | Finalized transaction | Verified result |
| --- | --- | --- |
| Create project | `0x1aa197d64bf9b5d2cd1028a912fa0d7735c5439b2435a9e86e87b270c01c597e` | Project 1, creator wallet above |
| Unauthorized observer creator-only edit | `0x1e7249e6ab2a30a27623de9fd6424770f20de1e30e33d50e1fb5e2c96af33526` | Finalized; component count unchanged |
| Add Jinja2 3.1.4 | `0x0e1ed91d1f18af8d0405643e59eb82879da4e9b93fd65a8fb13e3ef15cf1e9e0` | Component 1 |
| Add Flask 3.0.0 | `0xbfefd2c42f36ffb918ec6d3b0b40b22b572cd5de15b270b1ac6a776c2f23a8d0` | Component 2 |
| Add dependency edge | `0x439f9293adde1ff5e917fbf1bf15f642dcb044b6aac0b443f49d41e8a76d1597` | Flask depends on Jinja2 |
| Observer verifies Jinja2 identity | `0xfbdd0d3a11a980cae9a7f06343d6dc7aa9df047a6f96eeb5b51d510514cd4c68` | `VERIFIED`, exact version 3.1.4 |
| Observer verifies Flask identity | `0x0250dd5d1fb78f0d266d5364a51d75f86ce6a2fdfa7995cc9ce45e15c345403f` | `VERIFIED`, exact version 3.0.0 |
| Stale identity revision attempt | `0x118ef80ae1a76a8fe79aa0d7583c7734e729c8f9b5df71bfdc06ee104e4fbd59` | Finalized; Jinja2 state unchanged |
| Seal project | `0x70bb980677f7e27c17bbba346fcf3ad35622ea5500b78dc6e6c5f20081b6d007` | Project `SEALED` |
| Assess GHSA on vulnerable version | `0x208535841a01a88b569b78a4db772f9ba95760f8658f17b8191893fa5856c240` | Assessment 3; Jinja2 `VULNERABLE`, Flask `RECHECK_REQUIRED` |
| Replay same GHSA/version revision | `0x16473ee37d1da4ad443acc73f0e4bab4ad66dbeb99efaba05dd2ac1a12abf354` | Assessment count stayed 3; vulnerable state unchanged |
| Refuse recovery while upstream vulnerable | `0x6715dcc87ae863349c20105cfbf1f5d9b770b67756db52c75e58ee514d185787` | Flask remained `RECHECK_REQUIRED` |
| Stage Jinja2 3.1.5 patch | `0x0b4710cee01d534ad7bfab323b4d404928f7581be5ed5f31b47ae546d02496c0` | `PATCH_PENDING`; history retains vulnerable 3.1.4 and assessment 3 |
| Verify patched identity | `0x045945eb1e005e8d50397c9f70e2776a1fa9806de4b8f9114e67dbedfd408ab5` | Version revision 2, identity verified, `ACTIVE` |
| Reassess same GHSA after version change | `0x2f497cf74fb0f421f2665cc16a45de796d678f9b4ab34712c4d5e0dcc5653f9e` | Assessment 5; Jinja2 3.1.5 `NOT_AFFECTED`, outside range |
| Recover downstream Flask | `0x35b2d82ed4e10d5c26cdb98c570a54b31d1b2103b7ab082d668a7a71ce7a5833` | Assessment 6; Flask returned to `ACTIVE` |

Final finalized reads: 1 project (`SEALED`), 2 components (Jinja2 3.1.5 `ACTIVE`, Flask 3.0.0 `ACTIVE`), 1 active edge, 6 assessments. Jinja2 history retains 3.1.4 as `VULNERABLE`, scoped to version revision 1 and assessment 3. Full runner output and per-assessment readbacks were checked before this summary was written.

## Browser-wallet and production limits

No injected wallet provider/browser extension is available in the connected browser session (the available surface is the in-app browser without browser extensions). Therefore injected-wallet journeys, account/network switching through Rabby/MetaMask, and wallet-driven UI write E2E are **not run** and are not claimed as passing. The production frontend was not deployed; the user is deploying it separately. Configure `VITE_CONTRACT_ADDRESS=0x3D8ac6480A830b0EC9cdE515D06F29F3364583B1` in the production frontend environment.
