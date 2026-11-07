# Personas

Two axes, combined per run. A run pairs one **customer voice** (how the ticket text is written) with one **analyst** (how the app is used). Adapted from the `persona-ui-testing` library for ShopKart support tickets.

- `customers/`: who wrote the ticket. A persona **rephrases** each test case's ticket in their own voice with the **same intent**, so the test case's expected category and subcategory still hold. Fresh wording every run. The exact text typed is recorded in the run report.
- `analysts/`: the support analyst operating TicketLens (creating tickets, running Jev and GPT, comparing, picking the final answer).

Rules for every persona:
- English only, synthetic people only. Use `example.com` emails and made-up names and order IDs (`ORD-` plus 5 digits; never `SK-`, which is the app's ticket ID prefix).
- Stay within the taxonomy in `backend/app/core/taxonomy.py`. Never type the expected category, subcategory or any label hint into the app.
- Realism, never mockery.

Add a persona by copying any file here and keeping its four headings.
