import { useQuery } from "@tanstack/react-query"
import { Link, useParams } from "react-router"

import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { ProviderColumn } from "@/features/compare/ProviderColumn"
import type { ProviderRun } from "@/features/compare/useCompareRun"
import { formatDateTime } from "@/lib/format"
import { ApiError, api } from "@/services/api"
import type { ComparisonDetail, Execution } from "@/types/api"

/** A stored run in the shape the live columns use, with the timer frozen at its real duration. */
function storedRun(execution: Execution | null): ProviderRun {
  if (!execution) return { state: "idle" }
  return {
    state: "done",
    startedAt: 0,
    finishedAt: execution.duration_ms ?? 0,
    execution,
  }
}

function verdict({ comparison }: ComparisonDetail): string {
  if (comparison.status === "Completed") {
    const rate = Math.round((comparison.agreement_rate ?? 0) * 100)
    return `Agree on ${comparison.agreement_count} of ${comparison.comparable_field_count} fields (${rate}%).`
  }
  return comparison.status === "Partial"
    ? "Only one provider returned a result, so this is a partial comparison."
    : "Neither provider returned a result."
}

export function ComparisonDetailPage() {
  const { comparisonId = "" } = useParams()
  const detail = useQuery({
    queryKey: ["comparisons", "detail", comparisonId],
    queryFn: () =>
      api<ComparisonDetail>(
        `/api/comparisons/${encodeURIComponent(comparisonId)}`,
      ),
    retry: false,
  })

  if (detail.isPending) return <LoadingState label="Loading comparison…" />
  if (detail.error instanceof ApiError && detail.error.status === 404) {
    return (
      <EmptyState
        title="Comparison not found"
        action={
          <Link
            to="/comparisons"
            className="text-sm underline underline-offset-4"
          >
            Back to comparisons
          </Link>
        }
      />
    )
  }
  if (detail.isError) return <ErrorState error={detail.error} />

  const { ticket, jev, llm, comparison } = detail.data
  return (
    <div className="flex flex-col gap-4">
      <div className="grid gap-1 text-sm">
        <p className="font-medium">
          <Link
            to={`/tickets/${ticket.ticket_id}`}
            className="font-mono text-muted-foreground underline underline-offset-4"
          >
            {ticket.ticket_id}
          </Link>{" "}
          {ticket.title}
        </p>
        {ticket.description && (
          <p className="break-words whitespace-pre-wrap text-muted-foreground">
            {ticket.description}
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Run {formatDateTime(comparison.created_at)}
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <ProviderColumn
          provider="jev"
          run={storedRun(jev)}
          comparison={comparison}
        />
        <ProviderColumn
          provider="gpt"
          run={storedRun(llm)}
          comparison={comparison}
        />
      </div>
      <div className="flex flex-wrap items-center gap-2 rounded-lg border p-3 text-sm">
        <span className="font-medium">{verdict(detail.data)}</span>
        <span className="text-muted-foreground">
          Agreement is not accuracy, and no winner is chosen.
        </span>
      </div>
    </div>
  )
}
