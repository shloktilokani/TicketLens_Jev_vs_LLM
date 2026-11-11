import { Play } from "lucide-react"
import { Link } from "react-router"
import { toast } from "sonner"

import { ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ComparisonTable } from "@/features/comparisons/ComparisonsPage"
import { useComparisons } from "@/features/comparisons/hooks"
import { useRunProvider, useTicketRuns } from "@/features/tickets/hooks"
import {
  formatCost,
  formatDateTime,
  formatEscalation,
  formatTokens,
  seconds,
  SIDE_LABELS,
} from "@/lib/format"
import type { ExecutionSummary } from "@/types/api"

function RunButton({
  ticketId,
  provider,
}: {
  ticketId: string
  provider: "jev" | "gpt"
}) {
  const run = useRunProvider(ticketId, provider)
  const side = SIDE_LABELS[provider]
  return (
    <Button
      variant="outline"
      size="sm"
      disabled={run.isPending}
      onClick={() =>
        run.mutate(undefined, {
          onSuccess: (execution) =>
            execution.status === "Succeeded"
              ? toast.success(`${side} finished`)
              : toast.error(
                  `${side}: ${execution.error?.message ?? execution.status}`,
                ),
          onError: (error) => toast.error(error.message),
        })
      }
    >
      <Play aria-hidden /> {run.isPending ? `Running ${side}…` : `Run ${side}`}
    </Button>
  )
}

function RunRow({
  run,
  onUse,
}: {
  run: ExecutionSummary
  onUse: (run: ExecutionSummary) => void
}) {
  const answer = run.status === "Succeeded" ? run.normalized_result : null
  const side = SIDE_LABELS[run.provider]
  const when = formatDateTime(run.started_at)
  return (
    <li className="flex flex-wrap items-start justify-between gap-2 rounded-md border p-3 text-sm">
      <div className="grid min-w-0 gap-1">
        <p className="font-medium">
          {side} · {run.actual_model ?? run.requested_model} · {run.status}
        </p>
        {answer && (
          <p>
            {answer.category} › {answer.subcategory} · {answer.priority} ·{" "}
            {answer.sentiment} · Escalation{" "}
            {formatEscalation(answer.escalation_required).toLowerCase()}
          </p>
        )}
        {run.error && <p className="text-destructive">{run.error.message}</p>}
        <p className="text-xs text-muted-foreground">
          {when} · {seconds(run.duration_ms)} · tokens in / out{" "}
          {formatTokens(run.usage)} · est. cost{" "}
          {formatCost(run.estimated_cost?.amount)} ·{" "}
          <Link
            to={`/executions/${run.execution_id}`}
            className="underline underline-offset-4"
          >
            Open run
          </Link>
        </p>
      </div>
      {answer && (
        <Button
          size="sm"
          variant="outline"
          aria-label={`Use ${side}'s answer from ${when}`}
          onClick={() => onUse(run)}
        >
          Use this answer
        </Button>
      )}
    </li>
  )
}

function RunHistory({
  ticketId,
  onUse,
}: {
  ticketId: string
  onUse: (run: ExecutionSummary) => void
}) {
  const runs = useTicketRuns(ticketId)
  if (runs.isPending) return <LoadingState label="Loading AI runs…" />
  if (runs.isError)
    return <ErrorState error={runs.error} onRetry={runs.refetch} />
  if (runs.data.total === 0)
    return (
      <p className="text-sm text-muted-foreground">
        No AI runs yet. Nothing runs until you press one of the buttons above.
      </p>
    )
  return (
    <div className="grid gap-2">
      <ul className="grid gap-2">
        {runs.data.items.map((run) => (
          <RunRow key={run.execution_id} run={run} onUse={onUse} />
        ))}
      </ul>
      {/* shortcut: shows the newest page only; add paging here if a ticket ever needs it. */}
      {runs.data.total > runs.data.items.length && (
        <Link
          to={`/executions?ticket_id=${encodeURIComponent(ticketId)}`}
          className="text-sm underline underline-offset-4"
        >
          See all {runs.data.total} runs
        </Link>
      )}
    </div>
  )
}

function ComparisonHistory({ ticketId }: { ticketId: string }) {
  const list = useComparisons(50, ticketId)
  if (list.isError)
    return <ErrorState error={list.error} onRetry={list.refetch} />
  if (!list.data?.items.length) return null
  return (
    <section className="grid gap-2">
      <h3 className="text-sm font-medium">Comparisons</h3>
      <ComparisonTable items={list.data.items} />
    </section>
  )
}

export function AiResults({
  ticketId,
  onUse,
}: {
  ticketId: string
  onUse: (run: ExecutionSummary) => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI results</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="flex flex-wrap gap-2">
          <RunButton ticketId={ticketId} provider="jev" />
          <RunButton ticketId={ticketId} provider="gpt" />
          <Button asChild variant="outline" size="sm">
            <Link to={`/compare?ticket=${encodeURIComponent(ticketId)}`}>
              Compare both
            </Link>
          </Button>
        </div>
        <RunHistory ticketId={ticketId} onUse={onUse} />
        <ComparisonHistory ticketId={ticketId} />
      </CardContent>
    </Card>
  )
}
