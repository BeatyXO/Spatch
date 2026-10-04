# Evidence source manifest

Spatch never accepts arbitrary evidence URLs. It constructs URLs from bounded package metadata or a validated GHSA identifier.

| Purpose | Authority | Constructed endpoint | Consensus role |
| --- | --- | --- | --- |
| exact package/version identity | Google Open Source Insights / deps.dev | `https://api.deps.dev/v3/systems/<system>/packages/<name>/versions/<version>` | strict structured identity |
| vulnerability record | OSV | `https://api.osv.dev/v1/vulns/GHSA-<lowercase-id-groups>` | semantic advisory evidence |
| advisory record | GitHub Advisory Database | `https://api.github.com/advisories/<GHSA-ID>` | semantic advisory evidence |

## Source-handling rules

- HTTP status, body size and JSON shape are checked before evidence is used.
- The returned OSV ID and GitHub `ghsa_id` must equal the requested advisory ID.
- Advisory text is explicitly treated as inert evidence, never as instructions.
- Validators independently retrieve the evidence and independently derive the decision.
- A validator accepts the leader only when decision-critical fields match exactly.
- Source digests are recorded for auditability but are not treated as permanent identities of mutable web responses.

## Trust boundary

deps.dev provides a structured exact-version identity surface. OSV provides machine-readable affected-package/range data. GitHub Advisory Database provides another structured view of the same GHSA. These are two evidence surfaces, not necessarily two independent upstream authorities: OSV may import or derive its GHSA record from GitHub. The independent work occurs when each custom validator separately fetches both surfaces and re-evaluates applicability; agreement does not remove the shared-source trust limitation.

## Verified live-lifecycle fixture

The following public fixture was checked against the live sources on 2026-10-04 before any deployment transaction:

- Advisory: [GHSA-gmj6-6f8f-6699](https://github.com/advisories/GHSA-gmj6-6f8f-6699) (CVE-2024-56201), Jinja sandbox breakout through malicious filenames.
- Vulnerable component: PyPI `jinja2` **3.1.4**. deps.dev returns the exact `PYPI/jinja2/3.1.4` identity.
- Fixed component: PyPI `jinja2` **3.1.5**. deps.dev returns the exact `PYPI/jinja2/3.1.5` identity.
- OSV returns the exact GHSA and an ecosystem range introduced at 3.0.0 and fixed at 3.1.5; its listed affected versions end at 3.1.4.
- GitHub Advisory Database returns the same GHSA, affected range `>= 3.0.0, <= 3.1.4`, and first patched version 3.1.5.
- The proposed dependent node is PyPI `flask` **3.0.0**, also recognized by deps.dev.

This fixture has an explicit affected/fixed boundary shared by OSV and GitHub. The completed live result is recorded in `docs/LIVE_EVIDENCE.md`. OSV endpoint casing is case-sensitive: the `GHSA-` prefix stays uppercase while the three identifier groups are lowercase. Lowercasing the entire GHSA produced HTTP 404 during live diagnosis, so the contract now builds the provider's canonical path explicitly.
