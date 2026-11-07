import { Play, TriangleAlert } from "lucide-react"
import { useState } from "react"
import { useSearchParams } from "react-router"
import { toast } from "sonner"

import { ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ProviderColumn } from "@/features/compare/ProviderColumn"
import {
  type ComparisonState,
  useCompareRun,
} from "@/features/compare/useCompareRun"
import { TicketForm } from "@/features/tickets/TicketForm"
import { useCreateTicket, useTicket } from "@/features/tickets/hooks"
import { useTaxonomy } from "@/services/queries"
import type { Ticket } from "@/types/api"

function ExistingTicket({ onLoad }: { onLoad: (id: string) => void }) {
  return (
    <form
      className="flex gap-2"
      onSubmit={(event) => {
        event.preventDefault()
        const id = String(new FormData(event.currentTarget).get("id") ?? "")
          .trim()
          .toUpperCase()
        if (id) onLoad(id)
      }}
    >
      <Input
        name="id"
        placeholder="Ticket ID, e.g. SK-1004"
        aria-label="Ticket ID"
        className="w-56"
      />
      <Button type="submit" variant="outline">
        Load
      </Button>
    </form>
  )
}

function NewTicket({ onCreated }: { onCreated: (id: string) => void }) {
  const channels = useTaxonomy().data?.channels ?? []
  const create = useCreateTicket()
  return (
    <TicketForm
      channels={channels}
      submitLabel="Save ticket"
      pending={create.isPending}
      onSubmit={(input) =>
        create.mutate(input, {
          onSuccess: (ticket) => ticket && onCreated(ticket.ticket_id),
          onError: (error) => toast.error(error.message),
        })
      }
    />
  )
}

function TicketPanel({ ticket }: { ticket: Ticket }) {
  return (
    <div className="grid gap-1 text-sm">
      <p className="font-medium">
        <span className="font-mono text-muted-foreground">
          {ticket.ticket_id}
        </span>{" "}
        {ticket.title}
      </p>
      <p className="max-h-32 overflow-auto break-words whitespace-pre-wrap text-muted-foreground">
        {ticket.description}
      </p>
    </div>
  )
}

function Agreement({
  comparison,
  ready,
}: {
  comparison: ComparisonState
  ready: boolean
}) {
  if (!ready) return null
  if (comparison.state === "running")
    return <p className="text-sm text-muted-foreground">Comparing…</p>
  if (comparison.error)
    return (
      <p className="text-sm text-destructive">
        Comparison failed: {comparison.error}
      </p>
    )
  const data = comparison.data
  if (!data) return null
  const text =
    data.status === "Completed"
      ? `Agree on ${data.agreement_count} of ${data.comparable_field_count} fields (${Math.round((data.agreement_rate ?? 0) * 100)}%).`
      : data.status === "Partial"
        ? "Only one provider returned a result, so this is a partial comparison. The successful result is kept."
        : "Neither provider returned a result."
  return (
    <div
      role="status"
      className="flex flex-wrap items-center gap-2 rounded-lg border p-3 text-sm"
    >
      {data.status !== "Completed" && (
        <TriangleAlert className="size-4 text-destructive" aria-hidden />
      )}
      <span className="font-medium">{text}</span>
      <span className="text-muted-foreground">
        Agreement is not accuracy, and no winner is chosen. Saved as{" "}
        {data.comparison_id}.
      </span>
    </div>
  )
}

function TicketChooser({ onChoose }: { onChoose: (id: string) => void }) {
  const [mode, setMode] = useState<"existing" | "new">("existing")
  return (
    <>
      <div className="flex gap-2" role="group" aria-label="Ticket source">
        {(["existing", "new"] as const).map((m) => (
          <Button
            key={m}
            size="sm"
            variant={mode === m ? "default" : "outline"}
            aria-pressed={mode === m}
            onClick={() => setMode(m)}
          >
            {m === "existing" ? "Existing ticket" : "New ticket"}
          </Button>
        ))}
      </div>
      {mode === "existing" ? (
        <ExistingTicket onLoad={onChoose} />
      ) : (
        <NewTicket
          onCreated={(id) => {
            setMode("existing")
            onChoose(id)
          }}
        />
      )}
    </>
  )
}

export function ComparePage() {
  const [params, setParams] = useSearchParams()
  const ticket = useTicket(params.get("ticket") ?? "")
  const compare = useCompareRun()

  const choose = (id: string) => {
    compare.reset()
    setParams({ ticket: id })
  }
  const bothDone =
    compare.runs.jev.state === "done" && compare.runs.gpt.state === "done"

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="grid gap-4 pt-6">
          <TicketChooser onChoose={choose} />
          {ticket.isFetching && <LoadingState label="Loading ticket…" />}
          {ticket.isError && <ErrorState error={ticket.error} />}
          {ticket.data && <TicketPanel ticket={ticket.data} />}
          <Button
            className="justify-self-start"
            disabled={!ticket.data || compare.running}
            onClick={() => ticket.data && compare.start(ticket.data.ticket_id)}
          >
            <Play aria-hidden />{" "}
            {compare.running ? "Running…" : "Run Jev + LLM"}
          </Button>
        </CardContent>
      </Card>
      <div className="grid gap-4 md:grid-cols-2">
        <ProviderColumn
          provider="jev"
          run={compare.runs.jev}
          comparison={compare.comparison.data}
        />
        <ProviderColumn
          provider="gpt"
          run={compare.runs.gpt}
          comparison={compare.comparison.data}
        />
      </div>
      <Agreement comparison={compare.comparison} ready={bothDone} />
    </div>
  )
}
