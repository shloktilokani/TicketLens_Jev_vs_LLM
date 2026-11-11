# frontend/

The React app: Vite, TypeScript, Tailwind 4, shadcn/ui, React Router and TanStack Query. It talks only to the TicketLens backend, never to an AI provider.

## Files

| Path | Purpose |
|---|---|
| `src/main.tsx` | Entry point: query client, theme (`ticketlens-theme` in local storage) and router |
| `src/app/` | `router.tsx` (every page and its title), `AppShell.tsx` (sidebar, header badges, search, theme toggle, bulk banner), the not-found page |
| `src/features/tickets/` | Ticket list (filters, bulk toolbar), new ticket, detail (run history, final answer), CSV import and export |
| `src/features/compare/` | Compare page: runs both sides in parallel with live timers, then saves the comparison |
| `src/features/comparisons/`, `executions/`, `bulk/`, `settings/` | Comparisons list and detail, the AI Executions log and detail, Bulk Runs and the banner, the Settings page |
| `src/features/dashboard/` | Overview: counts, agreement, charts, accuracy section (`EvaluationSection.tsx`) |
| `src/components/` | Shared UI: loading, error and empty states, the confirm dialog, `Detail`, `FilterSelect` and `Pager`; shadcn primitives in `ui/` |
| `src/services/api.ts` | The one HTTP client (`VITE_API_BASE_URL`, default `http://127.0.0.1:8000`) |
| `src/types/api.ts` | API response types |
| `src/lib/format.ts` | Dates, seconds, cost, side labels ("Jev" and "LLM") |
| `src/index.css` | Theme tokens, including the chart colours `--series-jev` and `--series-llm` |

## Run and check

```bash
npm install
npm run dev          # http://localhost:5173
npm run lint && npm run build
```

Browser tests live in `../e2e/`.

## Rules and gotchas

- **The UI changes only after the API confirms.** Mutations update the cache from the response; nothing is optimistic.
- **Enum values come from `GET /api/taxonomy`,** never hard-coded lists, so a taxonomy edit on the Settings page shows up everywhere.
- **Never put secrets in `VITE_` variables;** they end up in the public bundle.
- **ESLint limits** cyclomatic complexity to 10 per function. `react-refresh/only-export-components` means a component file may export only components, so shared helpers go in `.ts` files.
- **Several pages poll while work is running:** Overview every 5 s, and the bulk banner and pages every 2 s, but only while a job is active.
- **Date filters on AI Executions use UTC days,** while tables show local time.
