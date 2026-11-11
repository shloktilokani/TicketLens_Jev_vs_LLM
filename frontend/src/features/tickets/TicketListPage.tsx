import { Search } from "lucide-react"
import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router"

import { FilterSelect, Pager } from "@/components/ListControls"
import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { BulkToolbar } from "@/features/tickets/BulkToolbar"
import { ExportLinks, ImportDialog } from "@/features/tickets/ImportExport"
import { type TicketQuery, useTickets } from "@/features/tickets/hooks"
import { formatDateTime, SIDE_LABELS } from "@/lib/format"
import { useTaxonomy } from "@/services/queries"
import type { Ticket, TicketPage } from "@/types/api"

const SORTS = [
  { value: "created_at:desc", label: "Newest first" },
  { value: "created_at:asc", label: "Oldest first" },
  { value: "priority:desc", label: "Most urgent first" },
  { value: "priority:asc", label: "Least urgent first" },
]
const FILTER_KEYS = ["q", "category", "priority", "status"] as const

/** Filters live in the URL so a filtered list can be bookmarked or shared (design.md section 3). */
function useListParams() {
  const [params, setParams] = useSearchParams()
  const query = Object.fromEntries(params) as TicketQuery
  const update = (changes: TicketQuery) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(changes)) {
      if (value) next.set(key, value)
      else next.delete(key)
    }
    if (!("page" in changes)) next.delete("page") // a new filter starts at page 1
    setParams(next)
  }
  return { query, update }
}

function Filters({ query, update }: ReturnType<typeof useListParams>) {
  const taxonomy = useTaxonomy().data
  return (
    <div className="flex flex-wrap items-center gap-2">
      <form
        role="search"
        className="relative"
        onSubmit={(event) => {
          event.preventDefault()
          update({
            q: String(new FormData(event.currentTarget).get("q") ?? "").trim(),
          })
        }}
      >
        <Search
          className="absolute top-1/2 left-2 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          key={query.q ?? ""}
          name="q"
          type="search"
          defaultValue={query.q}
          placeholder="ID, title, customer, email, order"
          aria-label="Search tickets"
          className="w-72 pl-8"
        />
      </form>
      {taxonomy && (
        <>
          <FilterSelect
            label="Categories"
            value={query.category}
            options={Object.keys(taxonomy.categories)}
            onChange={(v) => update({ category: v })}
          />
          <FilterSelect
            label="Priorities"
            value={query.priority}
            options={taxonomy.priorities}
            onChange={(v) => update({ priority: v })}
          />
          <FilterSelect
            label="Statuses"
            value={query.status}
            options={taxonomy.statuses}
            onChange={(v) => update({ status: v })}
          />
        </>
      )}
      <Select
        value={`${query.sort ?? "created_at"}:${query.order ?? "desc"}`}
        onValueChange={(v) => {
          const [sort, order] = v.split(":")
          update({ sort, order })
        }}
      >
        <SelectTrigger className="w-48" aria-label="Sort">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {SORTS.map((s) => (
            <SelectItem key={s.value} value={s.value}>
              {s.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

type Selection = {
  selected: Set<string>
  disabled: boolean
  onChange: (ticketIds: string[], checked: boolean) => void
}

function TicketRow({
  ticket,
  selection,
}: {
  ticket: Ticket
  selection: Selection
}) {
  const navigate = useNavigate()
  const final = ticket.final_classification
  return (
    <TableRow
      className="cursor-pointer"
      onClick={() => navigate(`/tickets/${ticket.ticket_id}`)}
    >
      {/* Clicks here select the row; everywhere else opens the ticket. */}
      <TableCell onClick={(e) => e.stopPropagation()}>
        <input
          type="checkbox"
          className="size-4 accent-primary"
          aria-label={`Select ${ticket.ticket_id}`}
          disabled={selection.disabled}
          checked={selection.selected.has(ticket.ticket_id)}
          onChange={(e) =>
            selection.onChange([ticket.ticket_id], e.target.checked)
          }
        />
      </TableCell>
      <TableCell className="font-mono text-xs">
        <Link
          to={`/tickets/${ticket.ticket_id}`}
          onClick={(e) => e.stopPropagation()}
          className="underline-offset-4 hover:underline"
        >
          {ticket.ticket_id}
        </Link>
      </TableCell>
      <TableCell className="max-w-64 truncate">{ticket.title}</TableCell>
      <TableCell>{ticket.customer.name}</TableCell>
      <TableCell>{final?.category ?? "—"}</TableCell>
      <TableCell>{final?.priority ?? "—"}</TableCell>
      <TableCell>
        <Badge variant="outline">{ticket.status}</Badge>
      </TableCell>
      <TableCell className="whitespace-nowrap">
        {formatDateTime(ticket.created_at)}
      </TableCell>
      <TableCell className="text-muted-foreground">
        {ticket.latest_run
          ? `${SIDE_LABELS[ticket.latest_run.provider]}: ${ticket.latest_run.status}`
          : "Not run"}
      </TableCell>
    </TableRow>
  )
}

function NoTickets({
  filtered,
  onClear,
}: {
  filtered: boolean
  onClear: () => void
}) {
  if (filtered) {
    return (
      <EmptyState
        title="No tickets match these filters"
        action={
          <Button variant="outline" onClick={onClear}>
            Clear filters
          </Button>
        }
      />
    )
  }
  return (
    <EmptyState
      title="No tickets yet"
      action={
        <Button asChild>
          <Link to="/tickets/new">New Ticket</Link>
        </Button>
      }
    >
      Create a ticket by hand, or import the sample CSV with Import CSV above.
    </EmptyState>
  )
}

function TicketTable({
  data,
  selection,
}: {
  data: TicketPage
  selection: Selection
}) {
  const pageIds = data.items.map((t) => t.ticket_id)
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>
              <input
                type="checkbox"
                className="size-4 accent-primary"
                aria-label="Select all tickets on this page"
                disabled={selection.disabled}
                checked={pageIds.every((id) => selection.selected.has(id))}
                onChange={(e) => selection.onChange(pageIds, e.target.checked)}
              />
            </TableHead>
            {[
              "Ticket ID",
              "Title",
              "Customer",
              "Category",
              "Priority",
              "Status",
              "Created",
              "Latest AI run",
            ].map((h) => (
              <TableHead key={h}>{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.items.map((ticket) => (
            <TicketRow
              key={ticket.ticket_id}
              ticket={ticket}
              selection={selection}
            />
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function TicketListPage() {
  const params = useListParams()
  const tickets = useTickets(params.query)
  const filtered = FILTER_KEYS.some((key) => params.query[key])
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [allEligible, setAllEligible] = useState(false)
  const selection: Selection = {
    selected,
    disabled: allEligible,
    onChange: (ticketIds, checked) =>
      setSelected((current) => {
        const next = new Set(current)
        for (const id of ticketIds) {
          if (checked) next.add(id)
          else next.delete(id)
        }
        return next
      }),
  }

  let body
  if (tickets.isPending) body = <LoadingState label="Loading tickets…" />
  else if (tickets.isError)
    body = <ErrorState error={tickets.error} onRetry={tickets.refetch} />
  else if (tickets.data.total === 0)
    body = (
      <NoTickets
        filtered={filtered}
        onClear={() =>
          params.update({ q: "", category: "", priority: "", status: "" })
        }
      />
    )
  else
    body = (
      <>
        <TicketTable data={tickets.data} selection={selection} />
        <Pager
          total={tickets.data.total}
          page={tickets.data.page}
          pageSize={tickets.data.page_size}
          noun="ticket"
          onPage={(page) => params.update({ page: String(page) })}
        />
      </>
    )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <ImportDialog />
        <ExportLinks />
      </div>
      <Filters {...params} />
      <BulkToolbar
        selected={[...selected]}
        allEligible={allEligible}
        onAllEligible={() => {
          setAllEligible((on) => !on)
          setSelected(new Set())
        }}
        onClear={() => {
          setAllEligible(false)
          setSelected(new Set())
        }}
      />
      {body}
    </div>
  )
}
