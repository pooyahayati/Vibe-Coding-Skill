# Payments Capability Pack

## Activation
Payment, checkout, charge, refund, gateway, or payment-provider behavior is touched.

## Constraints
- Treat provider state and local order/business state as separate systems that must reconcile safely.
- Require idempotency or equivalent duplicate protection for retried state-changing operations.
- Authenticate and verify callbacks/webhooks before applying state transitions.
- Keep money/currency precision and authoritative amount source explicit.
- Do not store raw payment credentials or sensitive payment data unless the architecture and compliance requirements explicitly require and protect it.
- Make failure, cancellation, timeout, refund, and asynchronous completion states explicit.

## Risks
Double charge/refund, order-payment divergence, replayed callbacks, incorrect amounts/currency, sensitive-data exposure, and irreversible state transitions.

## Integration points
Checkout ↔ payment adapter; gateway ↔ callback/webhook; payment state ↔ order/business state.

## Required checks
Success/failure/cancel/retry paths, duplicate callback/write handling, authorization, amount/currency integrity, and reconciliation with local state.

## Avoid
Assuming synchronous success, trusting client-supplied payment state, non-idempotent retries, and marking business state final before authoritative provider evidence.
