# Frontend Design Document

## 1. Design direction

A modern SaaS dashboard inspired by Linear:
- clean, calm, professional
- light and dark themes with a manual toggle
- clear hierarchy and compact information density
- minimal decoration; emphasize ticket status, classification, and model differences
- desktop-first, responsive down to tablet/mobile
- use Tailwind CSS + shadcn/ui
- use Lucide icons
- charts via Recharts

Avoid copying Linear branding or exact assets.

## 2. Application shell

### Sidebar navigation

- Overview
- Tickets
- Comparisons
- AI Executions
- Settings

Bottom of sidebar:
- theme toggle
- app version/build label (optional)

### Top header

- current page title and breadcrumb where useful
- global ticket search
- quick action: `New Ticket`
- compact provider connection indicators (Configured / Not configured), without exposing secrets

On small screens, collapse sidebar into a drawer.

## 3. Routes

- `/` — Dashboard
- `/tickets` — Ticket list
- `/tickets/new` — Create ticket
- `/tickets/:ticketId` — Ticket detail
- `/comparisons` — Comparison history/list
- `/comparisons/:comparisonId` — Comparison detail
- `/executions` — AI execution log list
- `/executions/:executionId` — Execution detail
- `/settings` — Settings

Use React Router. Preserve useful filters in URL query parameters where practical.

## 4. Dashboard (`/`)

### Metric cards
- Total tickets
- Open tickets
- Resolved tickets
- Average AI processing time
- Estimated AI spend (current filter/date range)

### Charts
- Tickets by category
- Priority distribution
- Jev vs GPT evaluation accuracy (only when labelled evaluation data/results exist)
- Model agreement vs disagreement

### Recent activity
- latest tickets
- latest AI executions
- recent failed executions with clear retry/manual action

Empty state: explain that the operator can create a ticket or import the sample CSV. Do not display misleading zero-accuracy charts before evaluation data exists.

## 5. Ticket list (`/tickets`)

Table columns:
- Ticket ID
- Title
- Customer
- Category (final classification if selected)
- Priority
- Status
- Created date
- Latest AI run indicator

Controls:
- search by ticket ID/title/customer/email/order ID
- filters: category, priority, status
- sort: created date, priority
- pagination
- row click opens ticket detail

Bulk toolbar appears when rows are selected:
- Run Jev
- Run GPT
- Compare both
- Select all eligible
- clear selection

Show bulk job progress in a persistent non-blocking panel/toast with a link to job details.

## 6. Create ticket (`/tickets/new`)

Form fields:
- title (required)
- description (required)
- customer name (required)
- customer email (required; validate format)
- order ID (optional)
- product name (optional)
- submission channel (required: Email, Chat, Phone, Website)

Behavior:
- do not run AI automatically on save
- save ticket as Open
- show generated ticket ID after successful creation
- offer next actions: Run Jev, Run GPT, Compare both
- provide clear validation messages
- preserve Hindi/Hinglish text exactly

## 7. Ticket detail (`/tickets/:ticketId`)

Header:
- ticket ID and title
- status selector
- edit action
- delete action with destructive confirmation

Main content:
- original description and customer/order context
- final classification panel (empty until operator selects)
- notes section
- AI action buttons: Run Jev, Run GPT, Compare both

History tabs or sections:
- Jev results
- GPT results
- comparison history
- complete execution timeline

For each execution show:
- provider/model
- status
- processing time
- token usage
- estimated cost
- timestamp
- view raw/normalized details

When choosing final classification, require explicit operator action. Provide a form to select one successful execution's classification and allow manual edits. Never auto-select.

## 8. Comparison detail (`/comparisons/:comparisonId`)

Display Jev and GPT in two aligned columns/cards.

Shared fields table:
- Category
- Subcategory
- Priority
- Sentiment
- Escalation

For each field:
- Jev value and confidence/probability if available
- GPT value
- agreement/disagreement indicator

Show summary and suggested resolution in GPT's panel. In Jev's panel display a clear `Not supported by Jev` state for free-text fields.

Show:
- input token usage
- output token usage
- processing duration
- estimated cost
- model names
- execution statuses

If one provider failed, show the successful result and a visible partial-comparison warning.

No automatic winner badge. The operator chooses the final result from the ticket detail page.

## 9. AI execution log pages

List columns:
- timestamp
- ticket ID
- provider
- model
- status
- input/output tokens
- estimated cost
- duration

Filters:
- provider
- status
- date range
- ticket ID

Execution detail:
- normalized input snapshot
- redacted request payload
- redacted raw response
- normalized result
- usage and cost calculation snapshot
- error detail if failed

Use collapsible JSON viewers with copy controls. Never show secrets.

## 10. Settings page

Sections:
1. Provider configuration status (keys are configured in backend `.env`; never display key values).
2. GPT model selection.
3. Jev model selection/refresh from TypeSafe model list.
4. Prompt configuration and prompt version.
5. Category/subcategory taxonomy management.
6. Pricing configuration per provider/model.
7. Jev escalation threshold (initial default 0.5).
8. Bulk processing concurrency setting.

Show warnings when a provider is not configured. API keys are not entered, displayed, or saved in the browser.

## 11. CSV import/export UX

Import dialog:
- choose CSV
- download template
- preview first rows
- show validation results
- summary cards: imported, invalid, duplicates skipped
- expandable row-level error table
- do not automatically execute AI after import

Exports:
- tickets CSV
- AI execution logs CSV
- comparisons CSV

Show a note that secrets are never exported. Avoid exporting raw payloads by default; provide a separate explicit export option for detailed execution payloads if implemented, with redaction.

## 12. Theme and design tokens

Use shadcn/ui semantic tokens for:
- background / foreground
- card
- muted
- border
- primary
- destructive
- accent
- ring

Default to light theme; remember selection locally in browser storage. Dark theme must maintain contrast.

Typography:
- use a clean sans-serif system or a single web-safe font stack
- clear page headings, compact table labels, readable body text
- avoid excessive font weights and gradients

Spacing:
- consistent 4/8px spacing rhythm
- restrained card shadows
- rounded corners, but not excessive pill styling

## 13. Interaction and accessibility

- Every async action has loading, success, and error feedback.
- Disable duplicate submission while a request is in progress.
- Confirm destructive deletion.
- Use semantic labels, keyboard-accessible dialogs, focus management, and visible focus states.
- Do not rely on color alone to communicate priority or status.
- Add accessible text labels to chart legends/tooltips.
- Tables must remain usable at narrower widths (horizontal scroll or responsive card layout).

## 14. Frontend non-goals

No customer-facing portal, login, role management, email inbox, notification center, payment features, or complex workflow builder.
