# WooCommerce Capability Pack

## Activation
WooCommerce classes, hooks, APIs, metadata, or task intent are present.

## Constraints
- Treat the extension as a WordPress plugin first and preserve WordPress interoperability rules.
- Prefer public WooCommerce APIs/CRUD and extension points; do not depend on `Automattic\\WooCommerce\\Internal` or `@internal` implementation details.
- Check WooCommerce availability before extension behavior that depends on it.
- Treat HPOS, Cart/Checkout Blocks, WordPress/WooCommerce version compatibility, and coexistence with other extensions/themes as explicit compatibility dimensions when the touched feature intersects them.
- Keep order/product/customer state transitions observable and reversible where possible.

## Risks
Order-storage assumptions, checkout regressions, extension conflicts, internal API coupling, duplicate hooks/actions, expensive order queries, and incompatibility with modern WooCommerce features.

## Integration points
Extension ↔ WooCommerce public APIs; extension ↔ order/product storage; extension ↔ other WooCommerce extensions.

## Required checks
Relevant WooCommerce flow, public API use, compatibility surface touched by the change, and multi-plugin/theme regression where shared behavior is affected.

## Avoid
Direct assumptions about posts-based order storage, internal namespace APIs, bypassing CRUD for order mutations without a justified compatibility reason, and globally expensive hooks.
