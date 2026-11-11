import { useQuery } from "@tanstack/react-query"
import { Check, Copy } from "lucide-react"
import { useState } from "react"
import { Link, useParams } from "react-router"

import { Detail } from "@/components/Detail"
import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { formatCost, formatDateTime, seconds, SIDE_LABELS } from "@/lib/format"
import { ApiError, api } from "@/services/api"
import type { Execution } from "@/types/api"

function JsonBlock({
  title,
  value,
  open = false,
}: {
  title: string
  value: unknown
  open?: boolean
}) {
  const [copied, setCopied] = useState(false)
  const text = JSON.stringify(value, null, 2)
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }
  return (
    <details open={open} className="rounded-lg border p-3">
      <summary className="cursor-pointer text-sm font-medium">{title}</summary>
      {value === null || value === undefined ? (
        <p className="mt-2 text-sm text-muted-foreground">Nothing recorded.</p>
      ) : (
        <div className="mt-2 grid gap-2">
          <Button
            variant="outline"
            size="sm"
            className="justify-self-start"
            onClick={copy}
          >
            {copied ? <Check aria-hidden /> : <Copy aria-hidden />}
            {copied ? "Copied" : "Copy"}
          </Button>
          <pre className="max-h-96 overflow-auto rounded-md bg-muted p-3 text-xs">
            {text}
          </pre>
        </div>
      )}
    </details>
  )
}

function RatesNote({ saved }: { saved: boolean }) {
  return (
    <p className="mt-3 text-xs text-muted-foreground">
      {saved
        ? "The rates shown were saved with this run, so later price changes do not alter it."
        : "No rates were saved with this run, so it has no cost estimate."}
    </p>
  )
}

function UsageAndCost({ run }: { run: Execution }) {
  const rates = run.pricing_snapshot
  const usage = run.usage
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage and estimated cost</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-3 sm:grid-cols-3">
          <Detail label="Input tokens" value={usage?.input_tokens} />
          <Detail label="Output tokens" value={usage?.output_tokens} />
          <Detail label="Total tokens" value={usage?.total_tokens} />
          <Detail label="Token source" value={usage?.usage_source} />
          <Detail
            label="Estimated cost"
            value={formatCost(run.estimated_cost?.amount)}
          />
          <Detail label="Price version" value={rates?.pricing_version} />
          <Detail
            label="Input rate per million"
            value={rates ? `$${rates.input_per_million}` : null}
          />
          <Detail
            label="Output rate per million"
            value={rates ? `$${rates.output_per_million}` : null}
          />
          <Detail label="Currency" value={rates?.currency} />
        </dl>
        <RatesNote saved={rates !== null} />
      </CardContent>
    </Card>
  )
}

function Summary({ run }: { run: Execution }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          {SIDE_LABELS[run.provider]} run on{" "}
          <Link
            to={`/tickets/${run.ticket_id}`}
            className="font-mono underline underline-offset-4"
          >
            {run.ticket_id}
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid gap-3 sm:grid-cols-3">
          <Detail label="Status" value={run.status} />
          <Detail label="Requested model" value={run.requested_model} />
          <Detail label="Actual model" value={run.actual_model} />
          <Detail label="Started" value={formatDateTime(run.started_at)} />
          <Detail label="Duration" value={seconds(run.duration_ms)} />
          <Detail
            label="Comparison"
            value={
              run.comparison_id ? (
                <Link
                  to={`/comparisons/${run.comparison_id}`}
                  className="underline underline-offset-4"
                >
                  Open comparison
                </Link>
              ) : (
                "Not part of a comparison"
              )
            }
          />
          <Detail label="Prompt version" value={run.prompt_version} />
          <Detail label="Taxonomy version" value={run.taxonomy_version} />
        </dl>
      </CardContent>
    </Card>
  )
}

export function ExecutionDetailPage() {
  const { executionId = "" } = useParams()
  const query = useQuery({
    queryKey: ["executions", "detail", executionId],
    queryFn: () =>
      api<Execution>(`/api/executions/${encodeURIComponent(executionId)}`),
    retry: false,
  })

  if (query.isPending) return <LoadingState label="Loading AI run…" />
  if (query.error instanceof ApiError && query.error.status === 404) {
    return (
      <EmptyState
        title="AI run not found"
        action={
          <Link
            to="/executions"
            className="text-sm underline underline-offset-4"
          >
            Back to AI executions
          </Link>
        }
      />
    )
  }
  if (query.isError) return <ErrorState error={query.error} />

  const run = query.data
  return (
    <div className="flex flex-col gap-4">
      <Summary run={run} />
      {run.error && (
        <div
          role="alert"
          className="rounded-lg border border-destructive/40 p-4 text-sm"
        >
          <p className="font-medium text-destructive">{run.error.message}</p>
          <p className="mt-1 text-xs text-muted-foreground">
            Code: {run.error.code ?? "—"} · HTTP: {run.error.http_status ?? "—"}
          </p>
        </div>
      )}
      <UsageAndCost run={run} />
      <JsonBlock
        title="Result after validation"
        value={run.normalized_result}
        open
      />
      <JsonBlock title="Input given to the model" value={run.input_snapshot} />
      <JsonBlock
        title="Request sent (credentials removed)"
        value={run.request_payload_redacted}
      />
      <JsonBlock
        title="Raw response (credentials removed)"
        value={run.response_payload_redacted}
      />
    </div>
  )
}
