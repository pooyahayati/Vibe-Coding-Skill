# Security

## Private reporting

Use GitHub's private vulnerability-reporting/security-advisory flow when **Report a vulnerability** is available. Otherwise contact the maintainer through [Pooyahayati.com](https://Pooyahayati.com) and establish a private channel before sharing exploit details, credentials or sensitive proof of concept. Public issues are only for non-sensitive hardening requests.

## Security scope

The Skill does not guarantee secure generated code. The Head retains security decisions; the selected security specialist supplies scoped methods and findings.

- During development, use native application controls, relevant allow/deny and integrity checks, and the applicable package manager's audit.
- Before authorized software publication/release/deployment, require installed native Trivy and actual scans bound to the final delivery target. Missing, failed or unverified required scans block publication. Trivy is the only additional scanner in the Head workflow.
- Assess scan coverage/findings and retain behavioral security evidence; clean output does not prove application authorization, business logic or data safety. Graphify supports impact analysis, not security approval; registries/OSV supply dependency evidence.
- Keep raw scan reports private outside product source and redact shared summaries. Installation warnings do not waive publication controls.

Commands, finding handling and evidence requirements are canonical in the [native release gate](references/security-and-dependencies.md#native-release-gate). Tooling does not grant host permissions or authorization.

## Supported line

Security fixes target the current maintained release line. Upgrade older versions unless a specific backport is published.
