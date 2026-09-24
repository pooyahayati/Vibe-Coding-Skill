# WordPress Capability Pack

## Activation
A WordPress plugin/header/API signal is present.

## Constraints
- Do not modify WordPress core.
- Use WordPress APIs and lifecycle hooks when they provide the required behavior.
- Prefix or namespace plugin-owned symbols and storage identifiers to avoid collisions.
- Preserve activation/deactivation/uninstall semantics and existing multisite behavior when relevant.
- For state-changing operations, combine authorization/capability checks with request-intent protection where applicable; sanitize/validate input and escape output at the proper boundary.
- Load admin/frontend assets only where needed.
- Treat coexistence with other plugins/themes as a normal operating condition, not an edge case.

## Risks
Hook priority/order conflicts, global namespace collisions, option/autoload growth, cron duplication, REST/AJAX authorization gaps, broad asset loading, database-query regressions, and incompatible assumptions about other plugins/themes.

## Integration points
Plugin ↔ WordPress lifecycle; plugin ↔ other plugins/themes.

## Required checks
Relevant WordPress flow, permissions for mutations, activation/upgrade path when touched, and conflict/regression coverage for shared hooks or global UI.

## Avoid
Direct core edits, raw cURL when the WordPress HTTP API fits, unconditional site-wide assets/requests, unprepared SQL, and assuming another plugin/theme is always present.

## Deeper references
Official WordPress Plugin/Common APIs documentation. Specialist WordPress skills may add depth but are optional.
