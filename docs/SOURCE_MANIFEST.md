# Evidence source manifest

Spatch never accepts arbitrary evidence URLs. It constructs URLs from bounded package metadata or a validated GHSA identifier.

| Purpose | Authority | Constructed endpoint | Consensus role |
| --- | --- | --- | --- |
| exact package/version identity | Google Open Source Insights / deps.dev | `https://api.deps.dev/v3/systems/<system>/packages/<name>/versions/<version>` | strict structured identity |
| vulnerability record | OSV | `https://api.osv.dev/v1/vulns/<GHSA-ID>` | semantic advisory evidence |
| advisory record | GitHub Advisory Database | `https://api.github.com/advisories/<GHSA-ID>` | semantic advisory evidence |

## Source-handling rules

- HTTP status, body size and JSON shape are checked before evidence is used.
- The returned OSV ID and GitHub `ghsa_id` must equal the requested advisory ID.
- Advisory text is explicitly treated as inert evidence, never as instructions.
- Validators independently retrieve the evidence and independently derive the decision.
- A validator accepts the leader only when decision-critical fields match exactly.
- Source digests are recorded for auditability but are not treated as permanent identities of mutable web responses.

## Why these sources

deps.dev provides a structured exact-version identity surface. OSV provides machine-readable affected-package/range data. GitHub Advisory Database provides a separate structured advisory representation for the same GHSA object. The combination lets Spatch validate identity deterministically and reserve AI consensus for the genuinely contextual task of applying advisory ranges to locked versions across ecosystems.
