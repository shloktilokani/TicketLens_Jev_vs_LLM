import { keepPreviousData, useQuery } from "@tanstack/react-query"
import { Link, useSearchParams } from "react-router"

import { FilterSelect, Pager } from "@/components/ListControls"
import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  formatCost,
  formatDateTime,
  formatTokens,
  seconds,
  SIDE_LABELS,
} from "@/lib/format"
import { api, BASE_URL } from "@/services/api"
import { useTaxonomy } from "@/services/queries"
import type { ExecutionPage, ExecutionSummary } from "@/types/api"

const FILTER_KEYS = ["provider", "status", "ticket_id", "date_from", "date_to"]

/** Filters live in the URL so a filtered log can be bookmarked (design.md section 3). */
function useLogParams() {
  const [params, setParams] = useSearchParams()
  const update = (changes: Record<string, string>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (!("page" in changes)) next.delete("page") // a new filter starts at page 1
    setParams(next)
  }
  return { params, update }
}

function DateFilter({
  id,
  label,
  value,
  onChange,
}: {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <Label htmlFor={id} className="text-xs text-muted-foreground">
        {label}
      </Label>
      <Input
        id={id}
        type="date"
        className="w-36"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  )
}

function Filters({ params, update }: ReturnType<typeof useLogParams>) {
  const statuses = useTaxonomy().data?.execution_statuses ?? []
  return (
    <div className="flex flex-wrap items-center gap-2">
      <FilterSelect
        label="Sides"
        value={params.get("provider") ?? undefined}
        options={["jev", "gpt"]}
        optionLabels={SIDE_LABELS}
        onChange={(provider) => update({ provider })}
      />
      <FilterSelect
        label="Statuses"
        value={params.get("status") ?? undefined}
        options={statuses}
        onChange={(status) => update({ status })}
      />
      <form
        onSubmit={(event) => {
          event.preventDefault()
          const id = new FormData(event.currentTarget).get("ticket_id")
          update({
            ticket_id: String(id ?? "")
              .trim()
              .toUpperCase(),
          })
        }}
      >
        <Input
          key={params.get("ticket_id") ?? ""}
          name="ticket_id"
          defaultValue={params.get("ticket_id") ?? ""}
          placeholder="Ticket ID + Enter"
          aria-label="Filter by ticket ID"
          className="w-40"
        />
      </form>
      <DateFilter
        id="date_from"
        label="From (UTC)"
        value={params.get("date_from") ?? ""}
        onChange={(date_from) => update({ date_from })}
      />
      <DateFilter
        id="date_to"
        label="To (UTC)"
        value={params.get("date_to") ?? ""}
        onChange={(date_to) => update({ date_to })}
      />
    </div>
  )
}

function LogTable({ items }: { items: ExecutionSummary[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            {[
              "When",
              "Ticket",
              "Side",
              "Model",
              "Status",
              "Tokens in / out",
              "Estimated cost",
              "Duration",
            ].map((h) => (
              <TableHead key={h}>{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((run) => (
            <TableRow key={run.execution_id}>
              <TableCell className="whitespace-nowrap">
                <Link
                  to={`/executions/${run.execution_id}`}
                  className="underline underline-offset-4"
                >
                  {formatDateTime(run.started_at)}
                </Link>
              </TableCell>
              <TableCell className="font-mono text-xs">
                {run.ticket_id}
              </TableCell>
              <TableCell>{SIDE_LABELS[run.provider]}</TableCell>
              <TableCell>{run.actual_model ?? run.requested_model}</TableCell>
              <TableCell className="whitespace-nowrap">{run.status}</TableCell>
              <TableCell className="whitespace-nowrap tabular-nums">
                {formatTokens(run.usage)}
              </TableCell>
              <TableCell className="tabular-nums">
                {formatCost(run.estimated_cost?.amount)}
              </TableCell>
              <TableCell className="whitespace-nowrap tabular-nums">
                {seconds(run.duration_ms)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function Body({
  query,
  filtered,
  onClear,
  onPage,
}: {
  query: ReturnType<typeof useLog>
  filtered: boolean
  onClear: () => void
  onPage: (page: number) => void
}) {
  if (query.isPending) return <LoadingState label="Loading AI runs…" />
  if (query.isError)
    return <ErrorState error={query.error} onRetry={query.refetch} />
  if (query.data.total === 0) {
    return filtered ? (
      <EmptyState
        title="No AI runs match these filters"
        action={
          <Button variant="outline" onClick={onClear}>
            Clear filters
          </Button>
        }
      />
    ) : (
      <EmptyState
        title="No AI runs yet"
        action={
          <Button asChild>
            <Link to="/compare">Open Compare</Link>
          </Button>
        }
      >
        Every Jev and LLM attempt is logged here, including failures.
      </EmptyState>
    )
  }
  return (
    <>
      <LogTable items={query.data.items} />
      <Pager
        total={query.data.total}
        page={query.data.page}
        pageSize={query.data.page_size}
        noun="run"
        onPage={onPage}
      />
    </>
  )
}

function useLog(params: URLSearchParams) {
  return useQuery({
    queryKey: ["executions", params.toString()],
    queryFn: () => api<ExecutionPage>(`/api/executions?${params}`),
    placeholderData: keepPreviousData,
  })
}

export function ExecutionsPage() {
  const { params, update } = useLogParams()
  const query = useLog(params)
  const filtered = FILTER_KEYS.some((key) => params.get(key))
  return (
    <div className="flex flex-col gap-4">
      <Filters params={params} update={update} />
      <div className="flex items-center justify-between gap-2">
        <p className="min-w-0 text-xs text-muted-foreground">
          Costs are estimates from the rates saved with each run. Local models
          cost nothing per call. Fake-AI runs and runs from before cost logging
          show —. Date filters use UTC; the table shows your local time.
        </p>
        <Button asChild variant="ghost" size="sm">
          <a href={`${BASE_URL}/api/exports/executions.csv`}>Download CSV</a>
        </Button>
      </div>
      <Body
        query={query}
        filtered={filtered}
        onClear={() =>
          update(Object.fromEntries(FILTER_KEYS.map((key) => [key, ""])))
        }
        onPage={(page) => update({ page: String(page) })}
      />
    </div>
  )
}
