# Web Security Capability Pack

## Activation
The task changes authorization, state mutation, untrusted input/output, public endpoints, sensitive data, or is activated by a high-risk interaction.

## Constraints
Authorize the actor, validate semantics, sanitize where needed, escape at output, protect request intent where applicable, use prepared/parameterized data access, and minimize secret/data exposure.

## Risks
Broken access control, CSRF/replay, XSS, injection, privilege escalation, insecure direct object access, secret leakage, and over-broad logging.

## Integration points
Untrusted input ↔ privileged/state-changing operation.

## Required checks
Negative authorization case, malformed input, output encoding where relevant, sensitive logging review, and platform-specific security mechanisms.

## Avoid
Treating nonce/token possession as authorization, trusting stored/remote data automatically, string-built SQL, and security checks only in the UI.
