# GenLayer Studionet live evidence

## Current canonical deployment and lifecycle

**Result: lifecycle PASS on GenLayer Studionet, chain ID 61999.** The fresh contract is the current source; listed state-changing transactions reached `FINALIZED`, and readbacks used latest finalized state. Author and observer wallets were distinct from each other and from the deployer.

### Deployment identity

- Contract: [`0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39`](https://explorer-studio.genlayer.com/address/0x2d531F147ad8EF488a5C01e2a9fF40dCC5fC8c39)
- Deployment transaction: [`0x6704d8c446543fa1b2d635ae113ebb4f1de5cd5ca2f1a400fbac4232c158c380`](https://explorer-studio.genlayer.com/tx/0x6704d8c446543fa1b2d635ae113ebb4f1de5cd5ca2f1a400fbac4232c158c380)
- Source SHA-256 (newline-normalized UTF-8): `a22c549fd0df48a312b93890d24f7cc3c8d2eb9e9d6140f146597156e12ac151`
- Git blob: `24ded26de8861205c6b51659f85a7516878c92fe`
- Source commit: `a64b1fee698aa9112b150d28921552825a5cc30e`
- A fresh `genlayer-js.getContractCode` read against finalized Studionet returned source that byte-for-byte matches `contracts/spatch.py` after CRLF→LF normalization; both SHA-256 digests are `a22c549fd0df48a312b93890d24f7cc3c8d2eb9e9d6140f146597156e12ac151`. `genlayer schema` exposed all 9 public writes plus `get_findings` and `get_security_findings`. Finalized `get_protocol` reported version 2 and chain ID 61999. Initial counts were zero.

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
