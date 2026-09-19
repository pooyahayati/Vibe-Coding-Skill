# Security

Do not report security-sensitive findings in a public issue if disclosure could create risk.

## Private reporting

Preferred: use GitHub's private vulnerability-reporting / security-advisory flow for this repository when the **Report a vulnerability** option is available.

If that option is unavailable, contact the maintainer through https://Pooyahayati.com without posting exploit details, credentials, tokens, or proof-of-concept secrets publicly. Establish a private channel before sharing sensitive technical details.

Public issues are appropriate only for non-sensitive security hardening requests that do not disclose an exploitable condition.

## Scope

The skill does not guarantee that generated code is secure. Security claims require evidence from appropriate tests, scanners, review, and runtime validation.

Graphify is used for project intelligence, not as a security authority.

Trivy may be used for baseline vulnerability, secret, container, IaC, and license scanning.

OSV and package registries may be used as dependency evidence providers.

High-risk application code may require additional SAST or language-specific security tooling.

## Supported line

Security fixes are applied to the current maintained release line. Older pre-release versions should be upgraded before relying on a fix unless a specific backport is published.
