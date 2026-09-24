# WordPress REST Capability Pack

## Activation
A WordPress REST route/client or REST task is involved.

## Constraints
- Define explicit `permission_callback` behavior; public access must be intentional.
- Validate/sanitize request data according to semantics and escape/shape response output at the correct boundary.
- Keep route namespaces/versioning and error contracts compatible with existing consumers.
- Separate authorization from input validity.

## Risks
Unauthorized mutation, data exposure, route collisions, contract drift, and expensive unauthenticated endpoints.

## Integration points
Client ↔ WordPress REST route; permission callback ↔ domain mutation.

## Required checks
Authorized and unauthorized paths, invalid input, expected response contract, and query/request cost for hot endpoints.

## Avoid
Permissive callbacks by accident, hidden state mutation in read routes, and duplicating an existing WordPress/WooCommerce API without need.
