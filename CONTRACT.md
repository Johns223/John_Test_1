# Booking platform contract

A reservation service in Python and the booking widget that talks to it in
TypeScript. These are the rules both halves are required to follow. A change
that breaks one of them is a defect whether or not anything raises.

## Money

1. **Integer minor units everywhere.** Pence and cents, never fractions.
   Conversion to major units happens once, in `web/src/format.ts`, and nowhere
   else.
2. **Tax applies to the discounted subtotal**, never to the list price.
3. **Length-of-stay bands are marginal.** A seven-night stay is billed three
   nights at full rate and four at the band rate, the way tax bands work.
4. **A promotion is applied once.** A line-level discount and a cart-level
   promotion are not both applied to the same amount.
5. **Split amounts sum back to the original.** Instalments and deposits never
   lose a unit to rounding.
6. **Displayed components reconcile with the displayed total.**

## Availability

7. **Slots are half-open.** `[start, end)`. Two bookings that merely touch do
   not conflict.
8. **All datetimes are timezone-aware UTC.** Naive datetimes do not cross a
   module boundary.
9. **Capacity checks are atomic.** A check followed by a write takes the lock,
   so two concurrent bookings cannot oversell.
10. **Cancelled reservations release their capacity** immediately, and their
    holds with them.

## Reservations and access

11. **Every read and write is scoped to the caller's organisation.** No
    endpoint returns a record belonging to another org.
12. **Authorisation fails closed.** A missing record, a missing claim or an
    unknown role denies the action.
13. **No side effect precedes its validation.** Money moves and audit records
    are written only after the transition is known to be legal.
14. **Idempotency keys are scoped to the organisation and the operation**, and
    are required for anything that charges.

## Client

15. **Search is debounced and the newest response wins.** An older in-flight
    response never overwrites a newer one.
16. **Cache keys contain every input that changes the result.**
17. **Anything that starts a timer returns a way to stop it.**
18. **State updates are immutable.** Functions that return a cart return a new
    cart rather than mutating the one passed in.

## Known gaps

No persistence layer yet; state is in-process. Payment gateway is stubbed.
There is no staging environment, so review is the only gate.
