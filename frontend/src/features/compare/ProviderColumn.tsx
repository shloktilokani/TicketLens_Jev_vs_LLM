import {
  CircleCheck,
  CircleDashed,
  CircleX,
  Equal,
  EqualNot,
  FlaskConical,
  LoaderCircle,
  Timer,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  type ProviderName,
  type ProviderRun,
  formatElapsed,
  useElapsed,
} from "@/features/compare/useCompareRun"
import type { Comparison, Execution } from "@/types/api"

const LABEL: Record<ProviderName, string> = { jev: "Jev", gpt: "LLM" }
const FIELDS = [
  ["category", "Category"],
  ["subcategory", "Subcategory"],
  ["priority", "Priority"],
  ["sentiment", "Sentiment"],
  ["escalation_required", "Escalation"],
] as const

function StatusLine({ run }: { run: ProviderRun }) {
  const execution = run.execution
  if (run.state === "idle")
    return (
      <p className="flex items-center gap-1 text-muted-foreground">
        <CircleDashed className="size-4" aria-hidden /> Not run
      </p>
    )
  if (run.state === "running")
    return (
      <p className="flex items-center gap-1">
        <LoaderCircle className="size-4 animate-spin" aria-hidden /> Running…
      </p>
    )
  const ok = execution?.status === "Succeeded"
  const Icon = ok ? CircleCheck : CircleX
  return (
    <p className={`flex items-center gap-1 ${ok ? "" : "text-destructive"}`}>
      <Icon className={`size-4 ${ok ? "text-green-600" : ""}`} aria-hidden />{" "}
      {execution?.status ?? "Request failed"}
    </p>
  )
}

function Match({ match }: { match: boolean | null | undefined }) {
  if (match === true)
    return (
      <span className="flex items-center gap-0.5 text-xs">
        <Equal className="size-3" aria-hidden />
        Agree
      </span>
    )
  if (match === false)
    return (
      <span className="flex items-center gap-0.5 text-xs font-medium">
        <EqualNot className="size-3" aria-hidden />
        Differ
      </span>
    )
  return null
}

function show(value: string | boolean | undefined): string {
  if (typeof value === "boolean") return value ? "Required" : "Not required"
  return value ?? "…"
}

function Fields({
  provider,
  execution,
  comparison,
}: {
  provider: ProviderName
  execution?: Execution
  comparison?: Comparison
}) {
  const result = execution?.normalized_result
  return (
    <dl className="grid gap-2 text-sm">
      {FIELDS.map(([key, label]) => {
        const confidence = result?.confidence[key]
        return (
          <div
            key={key}
            className="grid grid-cols-[7rem_1fr_auto] items-baseline gap-2"
          >
            <dt className="text-muted-foreground">{label}</dt>
            <dd>
              {show(result?.[key])}
              {/* Jev's own confidence; not comparable with anything GPT reports (ai-evaluation.md 8) */}
              {provider === "jev" && confidence !== undefined && (
                <span className="ml-1 text-xs text-muted-foreground">
                  {Math.round(confidence * 100)}% conf.
                </span>
              )}
            </dd>
            <Match match={comparison?.field_comparison[key]?.match} />
          </div>
        )
      })}
    </dl>
  )
}

function FreeText({
  provider,
  execution,
}: {
  provider: ProviderName
  execution?: Execution
}) {
  const result = execution?.normalized_result
  if (!result) return null
  if (provider === "jev") {
    return (
      <p className="text-sm text-muted-foreground">
        Summary and suggested resolution: not supported by Jev.
      </p>
    )
  }
  return (
    <div className="grid gap-2 text-sm">
      <p>
        <span className="text-muted-foreground">Summary: </span>
        {result.summary}
      </p>
      <p>
        <span className="text-muted-foreground">Suggested resolution: </span>
        {result.suggested_resolution}
      </p>
    </div>
  )
}

function Usage({ execution }: { execution?: Execution }) {
  if (!execution) return null
  const usage = execution.usage
  const tokens =
    usage && usage.usage_source !== "unavailable"
      ? `${usage.input_tokens ?? "?"} in · ${usage.output_tokens ?? "?"} out`
      : "Tokens not reported"
  return (
    <p className="text-xs text-muted-foreground">
      {tokens} · cost not calculated yet (Phase 11)
      {execution.duration_ms !== null &&
        ` · server time ${(execution.duration_ms / 1000).toFixed(2)} s`}
    </p>
  )
}

function ColumnHeader({
  provider,
  run,
}: {
  provider: ProviderName
  run: ProviderRun
}) {
  const elapsed = useElapsed(run)
  const fake = run.execution?.requested_model.startsWith("mock-")
  return (
    <CardHeader className="flex flex-row items-center justify-between gap-2">
      <CardTitle className="flex items-center gap-2">
        {LABEL[provider]}
        {fake && (
          <Badge variant="outline" className="gap-1">
            <FlaskConical className="size-3" aria-hidden /> Fake AI
          </Badge>
        )}
      </CardTitle>
      <span
        className="flex items-center gap-1 font-mono text-lg tabular-nums"
        aria-label={`${LABEL[provider]} elapsed time`}
      >
        <Timer className="size-4" aria-hidden />
        {formatElapsed(elapsed)}
      </span>
    </CardHeader>
  )
}

function RunStatus({ run }: { run: ProviderRun }) {
  const execution = run.execution
  const error = run.error ?? execution?.error?.message
  return (
    <div aria-live="polite" className="text-sm">
      <StatusLine run={run} />
      {execution && (
        <p className="text-xs text-muted-foreground">
          Model: {execution.actual_model ?? execution.requested_model}
        </p>
      )}
      {error && <p className="mt-1 text-sm text-destructive">{error}</p>}
    </div>
  )
}

export function ProviderColumn({
  provider,
  run,
  comparison,
}: {
  provider: ProviderName
  run: ProviderRun
  comparison?: Comparison
}) {
  return (
    <Card>
      <ColumnHeader provider={provider} run={run} />
      <CardContent className="grid gap-4">
        <RunStatus run={run} />
        <Fields
          provider={provider}
          execution={run.execution}
          comparison={comparison}
        />
        <FreeText provider={provider} execution={run.execution} />
        <Usage execution={run.execution} />
      </CardContent>
    </Card>
  )
}
