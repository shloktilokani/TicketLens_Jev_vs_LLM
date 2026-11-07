# TC-001: Create a ticket and find it again

- **Mode**: mock
- **Customer voices**: any
- **Analysts**: any
- **Preconditions**: none

## Ticket intent

The customer was charged twice for one order and wants the extra payment refunded.

> Reference wording: "I was charged twice for order ORD-48213. Please refund the extra payment."

## Expected labels (real mode only, never typed into the app)

- Category: Payments & Billing
- Subcategory: Duplicate Charge
- Priority / sentiment / escalation: not checked

## Steps

1. Open New Ticket.
2. Enter a title and the ticket text in the persona's voice. Enter a customer name and an `example.com` email, plus an order ID. Choose a submission channel.
3. Create the ticket.
4. Open it from the confirmation. Then find it again from the Tickets list using search.

## Expected results

- The confirmation shows a ticket ID, and the ticket is saved as Open.
- The detail page shows the description exactly as typed, including line breaks, emoji and spacing.
- Search by title, order ID and customer email each finds the ticket.
- Invalid input (blank title or description, a bad email, no channel) shows a field-level message and creates nothing.

## Visual checkpoints

- The New Ticket form, empty and filled, on desktop and mobile.
- The confirmation panel.
- The detail page with long or multi-line text: no overflow or clipped text.
- The list row: the title is truncated sensibly, and the ID and status are readable.
