# Data knowledge base (`docs/`)

A convention for projects that build dashboards, reports, or query-driven features over a shared
database. It holds what has been learned about the data, how each dashboard is defined, and where
its code lives — so the next person (or agent session) doesn't rediscover table traps from scratch.

## Layout

```
docs/
  README.md                   "where to look" table for the whole knowledge base
  conventions.md              how any dashboard/report is built in this codebase
  data/                       shared by every dashboard; durable facts about the data
    README.md                 how to query the local/dev database
    tables/<schema>.<table>.md   one file per table: grain, keys, mandatory filters, traps
    joins.md                  verified join paths across tables/schemas
    glossary.md               business terms, codes, abbreviations
    data-quality-log.md       known data problems, each with a stable id (DQ-###) and status
  dashboards/
    <name>/
      README.md               purpose, audience, status, tables used
      kpis.md                 KPI id -> definition -> SQL file
      queries/<ID>_<slug>.sql SQL verified against the real database
      implementation.md       KPI id -> endpoint -> data-access method -> result record -> chart
      decisions.md            locked decisions, each with an id (D-##), date, and why
      open-questions.md       what only the business can answer; who was asked, when
      findings-<YYYY-MM-DD>.md   dated analysis; frozen once written
```

## Rules

- **One fact, one place.** Table rules live in `data/tables/`. Dashboard docs link to them and
  never copy them — a copied rule goes stale in one place and not the other.
- **Figures are dated.** Numbers appear only in `findings-<date>.md` files, which are never edited
  after their date. A re-run gets a new file; the old one stays as the record of what was true then.
- **Ids link the layers.** A KPI id (e.g. `INV-03`) appears in `kpis.md`, the SQL filename
  (`queries/INV-03_stock_on_hand.sql`), a one-line comment on the data-access method
  (`// INV-03`), and the result record's doc comment — so one search finds every piece. If the
  code's SQL and the `.sql` file differ, update the doc in the same change.
- **Data-quality issues get a stable id** (`DQ-###`) in the log; table docs and findings reference
  the id rather than re-describing the problem. Status changes (open → mitigated → fixed) are
  recorded with a date and evidence.
- **Decisions get ids too** (`D-##` per dashboard). The newest recorded decision wins; a decision
  changes only through a new recorded entry that names the one it supersedes.
- **Open questions are business questions**, not engineering TODOs — each names who can answer it.
- **Verify SQL against the real database** before saving it under `queries/`; note the date and
  row count of the verifying run in the findings file, not in the SQL.

## Per-table doc skeleton (`data/tables/<schema>.<table>.md`)

```
# <schema>.<table>
Grain: one row per <...>
Keys: <primary / natural keys>
Mandatory filters: <filters every query must apply, and why>
Columns that matter: <name — meaning — units — traps>
Known issues: DQ-### (link), ...
Used by: <dashboards / features>
Other consumers: <other applications sharing this table, if known>
```
