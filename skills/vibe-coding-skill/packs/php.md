# PHP Capability Pack

## Activation
PHP source or Composer metadata is present.

## Constraints
- Follow the project's supported PHP range, coding conventions, autoloading, and existing architecture.
- Prefer platform/framework APIs over bypassing them with lower-level PHP when interoperability depends on the platform.
- Treat warnings, notices, type errors, and deprecations in touched code as compatibility evidence, not noise.

## Risks
Global symbols, runtime-version drift, hidden side effects, fatal errors, serialization/timezone differences, and dependency conflicts.

## Integration points
PHP runtime ↔ framework/platform lifecycle.

## Required checks
Choose the smallest relevant existing PHP test or static check; add compatibility smoke for affected runtime risks. Availability alone does not require every configured command. Follow the [stage policy](../references/execution-and-verification.md#testing-policy) and explicit project requirements.

## Avoid
New global state, duplicated framework facilities, silent error suppression, and version-specific features outside the declared support range.
