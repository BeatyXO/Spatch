# GenLayer Studionet live evidence

## Current canonical deployment

The capacity-boundary fix is deployed on stable GenLayer Studionet, chain ID 61999. The deployment transaction finalized successfully. Deployed source and schema were read back and verified against the pushed source commit. The fresh two-wallet lifecycle below completed successfully, with finalized receipts and state readbacks.

### Deployment identity

- Contract: [`0x2e517eE9ABCB8f71bD3B8251315A3013C3e69cd6`](https://explorer-studio.genlayer.com/address/0x2e517eE9ABCB8f71bD3B8251315A3013C3e69cd6)
- Deployment transaction: [`0xd4feff8ae226ca9198ce503182fdcbac4e3b47997a15f317a289f2681c5fbdbd`](https://explorer-studio.genlayer.com/tx/0xd4feff8ae226ca9198ce503182fdcbac4e3b47997a15f317a289f2681c5fbdbd)
- Deployer: `0x7876e9f76f32925c212528d57bc9dfe5e34bcc07`
- Source SHA-256 (newline-normalized UTF-8): `492f7f7ee8508039312dc63e049519cbfb7d4a765835e5ac0e7656f2c3eafc56`
- Git blob: `e4cbc2c387aee9ddcafb6dc965c3a2f2eb495ead`
- Source commit: `02677b85fa7b3f3f9311583611bb4cc1c4919825`
- `genlayer code` returned source that exactly matches `contracts/spatch.py` after newline normalization. `genlayer schema` exposed all 9 public writes (`create_project`, `add_component`, `add_dependency`, `verify_component`, `seal_project`, `assess_advisory`, `patch_component`, `verify_patch`, `reassess_dependency`) and the read methods. `get_protocol` reports version 2 and chain ID 61999. Finalized reads report initial counts of zero projects, components, edges, and assessments.
- The production frontend still points at the superseded contract until the Vercel environment variable is updated to this address and redeployed.

## Current fresh two-wallet lifecycle

**Result: PASS.** This lifecycle ran on the current contract above using distinct author and observer wallets; the deployer was a third wallet. Every write listed below reached `FINALIZED`, and the runner asserted latest-finalized readbacks. Temporary encrypted keystore exports were removed after the run; no private keys were printed or committed.

### Wallet roles and fixture

- Deployer: `0x7876e9f76f32925c212528d57bc9dfe5e34bcc07`
- Author/project creator: `0x6b476bf35c4968f3f1775c0ca2110591b4b5fcbe`
- Observer: `0x77e2edbb43277bf772e207c517dde731935ffba5`
- Fixture: PyPI `jinja2` **3.1.4 → 3.1.5**, [GHSA-gmj6-6f8f-6699](https://github.com/advisories/GHSA-gmj6-6f8f-6699); dependent PyPI `flask` **3.0.0**. deps.dev identity checks passed for all package/version pairs. The exact GHSA was fetched from OSV and GitHub Advisory Database; the independent validator agreed that 3.1.4 is affected and 3.1.5 is outside the range.

### Finalized transactions

| Operation | Finalized transaction | Readback |
| --- | --- | --- |
| Deploy capacity-fix contract | `0xd4feff8ae226ca9198ce503182fdcbac4e3b47997a15f317a289f2681c5fbdbd` | Source/schema verified; initial counts zero |
| Create project | `0xda7a7933ca4f8908e691d195c7750b89cd887e23a035ef9b1726aa0018901295` | Project 1, author is creator |
| Unauthorized observer edit | `0xf512e34c53cdf845bf9b9b73f1cf6f76422b2652d23e949f7e36eb17ec07079c` | `ONLY_PROJECT_CREATOR`; component count unchanged |
| Add Jinja2 3.1.4 | `0xa54029d33540fc1a2c899a89099b0356ba4d8ee694f64b43f69e2e36bee4a11d` | Component 1 |
| Add Flask 3.0.0 | `0x6bcc5e4a184ac8b0af8607556d5f6ee215a8d66a52a124027f2affe4aadda91c` | Component 2 |
| Add dependency edge | `0xca53e4d0de6848521fcfefcb0c8bf02e51bdbc71e9c4dd486a89d3912577cfbd` | Flask depends on Jinja2 |
| Observer verifies Jinja2 identity | `0x1338718c7bf637ecb6d002eb7f725278b8f7f87a7065536a618ca4010c144af6` | Version revision 1 verified |
| Observer verifies Flask identity | `0xe359bb8e96e15c1e4b9ee8c1bf74323f0e1755c6c974f017c9df06019c8027b2` | Version revision 1 verified |
| Stale identity revision attempt | `0xc5d72ea519b130ba04496fa1fca3da2dc2d93f738c594a0cfc47c5a420e8616a` | `STALE_COMPONENT_REVISION`; Jinja2 unchanged |
| Seal project | `0x7ee8d2da3fc61873db685cbeb84e3e3cfdb385a6c3ffb5bcf13931ac896f3efc` | Project `SEALED` |
| Assess vulnerable GHSA | `0x2befc36d583f74aaeaf4e933121f4a7b51c7f751fe51279e3a053e02d5ead285` | Assessment 3: Jinja2 `AFFECTED`; Flask `NOT_AFFECTED` and `RECHECK_REQUIRED` |
| Replay same GHSA/version revision | `0x5b7b94a090bc026efdd0608a301c3d27bebdbe65f31ffab24f4ce6400a34eae8` | Replay rejected; assessment count stayed 3; Jinja2 remained vulnerable |
| Refuse recovery while upstream vulnerable | `0xe4267f2284782aa06a073ca51705d6ca40e3b2a6471cc60d2f9b63b182999c4c` | Flask remained `RECHECK_REQUIRED` |
| Stage Jinja2 3.1.5 patch | `0x47c6799ee8bf4aeb2c27fd655fdc9761ba6a8fd8e7c02592700eeefc6bdbd2af` | `PATCH_PENDING`; history retains vulnerable 3.1.4; identity proof cleared |
| Verify patched identity | `0x42ba952112f0efe12f3ddffa5f2db2464265c8572fb3ce2b323c8e58d503e3f3` | Version revision 2 verified; security remains `SECURITY_REASSESS_REQUIRED` |
| Reassess same GHSA after version change | `0xfb4ca2e4d9ae04a39735b2e8b57edc4f70e6953d476b58427487d91fe76c8e1b` | Assessment 5: Jinja2 3.1.5 `NOT_AFFECTED`, revision 2 |
| Recover downstream Flask | `0xa21d055442f85117906a47bf4faed8a4514408f7ddfa573eaa3bd8b99581f916` | Assessment 6; Flask `ACTIVE` |

Final reads: 1 sealed project, 2 components, 1 active edge, and 6 assessments. Jinja2 3.1.5 and Flask 3.0.0 are `ACTIVE`; the historical Jinja2 3.1.4 `AFFECTED` finding remains preserved under version revision 1.

## Previous deployment lifecycle (historical)

This earlier lifecycle applies only to contract `0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`, deployed before the finding-capacity fix. It is retained for auditability and does not replace the current lifecycle evidence above.

### Wallet roles

- Deployer: `0x7876e9f76f32925c212528d57bc9dfe5e34bcc07`
- Author/project creator: `0x1Ca1D8F506c82d14f994Fea88fCF93D9a90587f0`
- Observer: `0x4D4759Ea6adCCf0f05De68317fbBbB8F0942099A`
- Temporary test wallet keys were not printed or committed and were removed after the run.

### Fixture and finalized transactions

Fixture: PyPI `jinja2` **3.1.4 → 3.1.5**, [GHSA-gmj6-6f8f-6699](https://github.com/advisories/GHSA-gmj6-6f8f-6699); dependent PyPI `flask` **3.0.0**. Sources mark 3.1.4 affected and 3.1.5 fixed. Exact deps.dev identities and OSV/GitHub Advisory Database records were checked before the lifecycle. The shared-upstream-authority limitation is documented in `docs/SOURCE_MANIFEST.md`.

| Operation | Finalized transaction | Readback |
| --- | --- | --- |
| Deploy current contract | `0x6704d8c446543fa1b2d635ae113ebb4f1de5cd5ca2f1a400fbac4232c158c380` | Deployed source/schema verified |
| Create project | `0xda556eda1d6b6f38ea0ead28e410cf23495ee02fe0aa23c4843f8fe9c5cbfec9` | Project 1, author is creator |
| Unauthorized observer component edit | `0xcf6a58d432aae3d4f7bdef3d791fdd169a18f21e1c98cf2dc508849a667fc378` | `ONLY_PROJECT_CREATOR`; counts unchanged |
| Add Jinja2 3.1.4 | `0x5b188c420a7c6d34adc04e74a4302744560b92111836fb8e2a63c15ab0b3dce3` | Component 1 |
| Add Flask 3.0.0 | `0x6c5a8bdc18a5ee04442a38de5c59ea09f1d7f18b41cfee0aedc200cf1b64c572` | Component 2 |
| Add dependency edge | `0x9f98b5956a384222468305bdadc9cceecc2981d74807850705457999dda5c1b2` | Flask depends on Jinja2 |
| Observer verifies Jinja2 identity | `0x3fe66965d90b9b7b9cbaee7d248dbd805ed85149daf0e0762ef93500767b2697` | Version revision 1 verified |
| Observer verifies Flask identity | `0x0a02981d5ed85d9e0faed2ae62be876f81255a0b7ce6d460d14d7592d63a836a` | Version revision 1 verified |
| Stale identity revision attempt | `0x8eb5dd57a016206cb1175d5d33c66af224670a4b016750c0cb67ac5c1c2dc585` | `STALE_COMPONENT_REVISION`; unchanged |
| Seal project | `0x776aacaac7da581e0d6474ef31b59aed2a9b59858f84e3258f9ae1ebbc8bf710` | Project SEALED |
| Assess vulnerable GHSA | `0xf3c6ff39b7ff5d57f7e76f8dd0d3207456d2f5684df3e2708e75def6ff056a06` | Assessment 3: Jinja2 AFFECTED; Flask not targeted |
| Same-version replay | `0x18e72a5ea51680fcad70095aa7494cc19ba4dc999c73fb9b7a28d71bfe961c9a` | Replay rejected; count stayed 3 |
| Refuse downstream recovery while vulnerable | `0x4c38126b6cfcc8653baad9ee8e00d93642b1502aad2dedf5f79d070dbe70235e` | `UPSTREAM_STILL_VULNERABLE`; unchanged |
| Stage Jinja2 3.1.5 | `0xbd6db32db8206f7fb617bab74b1a7d1543ffd4b1463bf5e0f5df3462961e846a` | 3.1.4 AFFECTED history preserved; proof cleared |
| Verify patched identity | `0x128468b75a123eafa956d733721ed611f89c6b9d479866846b120abac2362da6` | Identity verified; security remains SECURITY_REASSESS_REQUIRED |
| Reassess same GHSA after version change | `0x408fe06f19cd2b6864f833f8af84db3f05a25890ca8a7621dbf52ba4dde6886a` | Separately checked receipt: FINALIZED; assessment 5 says 3.1.5 NOT_AFFECTED, revision 2 |
| Identity cannot clear downstream recheck | `0xd5a49eb5c2dfa7899377b9cfab9db0259ee8f6ff9cb9c683883214ea3032f895` | `COMPONENT_IDENTITY_ALREADY_CURRENT`; Flask remained RECHECK_REQUIRED |
| Downstream recovery | `0x71bcc8e72a5828d9407fca340bfecf78b99b10e09abfdc18a5599163a0b9d585` | Assessment 6; Flask ACTIVE |

Final readbacks: 1 sealed project, 2 components, 1 active edge, 6 assessments. Jinja2 3.1.5 and Flask 3.0.0 are ACTIVE; the old 3.1.4 AFFECTED finding remains historical. The post-patch assessment runner hit a transient RPC HTML error while polling; the submitted transaction was not repeated, its receipt was confirmed FINALIZED separately, and the lifecycle resumed from that finalized checkpoint to `e2e.result=PASS`.

## Historical evidence archive

Superseded deployment and lifecycle evidence is preserved separately in [HISTORICAL_EVIDENCE.md](HISTORICAL_EVIDENCE.md). It is retained only for auditability and is not part of the canonical reviewer path.
