import { useQuery } from "@tanstack/react-query"
import { Link } from "react-router"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { ComparisonTable } from "@/features/comparisons/ComparisonsPage"
import {
  AXIS,
  FIELD_LABELS,
  percent,
  TOOLTIP,
} from "@/features/dashboard/chartStyles"
import { EvaluationSection } from "@/features/dashboard/EvaluationSection"
import { ChartCard, Stat } from "@/features/dashboard/parts"
import { useComparisons } from "@/features/comparisons/hooks"
import { formatCost, seconds } from "@/lib/format"
import { api } from "@/services/api"
import type { DashboardData, RunMetrics } from "@/types/api"

// Severity order, not alphabetical; other values keep alphabetical order.
const ORDER = ["Critical", "High", "Medium", "Low"]

function Stats({ data, m }: { data: DashboardData; m: RunMetrics }) {
  const { tickets } = data
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Stat value={tickets.total} label="Total tickets" />
      <Stat value={tickets.by_status.Open ?? 0} label="Open tickets" />
      <Stat value={tickets.by_status.Resolved ?? 0} label="Resolved tickets" />
      <Stat value={data.real_comparisons} label="Real comparisons" />
      <Stat value={percent(m.mean_agreement)} label="Mean agreement" />
      <Stat
        value={`${m.exact_matches} of ${m.comparisons.Completed ?? 0}`}
        label="Agree on all 5 fields"
      />
      <Stat value={seconds(m.latency.jev.median)} label="Jev median time" />
      <Stat value={seconds(m.latency.llm.median)} label="LLM median time" />
    </div>
  )
}

function AgreementChart({ m }: { m: RunMetrics }) {
  const rows = Object.entries(m.per_field).map(([field, d]) => ({
    field: FIELD_LABELS[field] ?? field,
    agreement: Math.round((d.rate ?? 0) * 100),
    detail: `${d.agreed} of ${d.compared}`,
  }))
  return (
    <ChartCard title="Agreement by field" height={230}>
      <BarChart data={rows} layout="vertical" margin={{ left: 16, right: 24 }}>
        <CartesianGrid horizontal={false} stroke="var(--border)" />
        <XAxis
          type="number"
          domain={[0, 100]}
          unit="%"
          tick={AXIS}
          stroke="var(--border)"
        />
        <YAxis
          type="category"
          dataKey="field"
          width={90}
          tick={AXIS}
          stroke="var(--border)"
        />
        <Tooltip
          {...TOOLTIP}
          formatter={(value, _name, item) => [
            `${value}% (${item.payload.detail})`,
            "Agreement",
          ]}
        />
        <Bar
          dataKey="agreement"
          fill="var(--muted-foreground)"
          radius={[0, 4, 4, 0]}
          barSize={16}
        />
      </BarChart>
    </ChartCard>
  )
}

function SideBySideChart({
  title,
  field,
  m,
}: {
  title: string
  field: string
  m: RunMetrics
}) {
  const jev = m.distributions.jev[field] ?? {}
  const llm = m.distributions.llm[field] ?? {}
  const rows = [...new Set([...Object.keys(jev), ...Object.keys(llm)])]
    .sort((a, b) => ORDER.indexOf(a) - ORDER.indexOf(b) || a.localeCompare(b))
    .map((name) => ({ name, Jev: jev[name] ?? 0, LLM: llm[name] ?? 0 }))
  return (
    <ChartCard title={title} height={Math.max(220, rows.length * 52 + 60)}>
      <BarChart
        data={rows}
        layout="vertical"
        margin={{ left: 16, right: 24 }}
        barGap={2}
      >
        <CartesianGrid horizontal={false} stroke="var(--border)" />
        <XAxis
          type="number"
          allowDecimals={false}
          tick={AXIS}
          stroke="var(--border)"
        />
        <YAxis
          type="category"
          dataKey="name"
          width={130}
          tick={AXIS}
          stroke="var(--border)"
        />
        <Tooltip {...TOOLTIP} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Bar
          dataKey="Jev"
          fill="var(--series-jev)"
          radius={[0, 4, 4, 0]}
          barSize={12}
        />
        <Bar
          dataKey="LLM"
          fill="var(--series-llm)"
          radius={[0, 4, 4, 0]}
          barSize={12}
        />
      </BarChart>
    </ChartCard>
  )
}

function Reliability({ m }: { m: RunMetrics }) {
  const row = (name: string, side: "jev" | "llm") => {
    const out = m.outcomes[side]
    return (
      <li key={side}>
        <span className="font-medium">{name}:</span> {out.counts.Succeeded ?? 0}{" "}
        of {out.total} succeeded · slowest {seconds(m.latency[side].max)} ·
        estimated cost {formatCost(m.cost[side].total)} (
        {m.cost[side].priced_runs} of {out.total} runs priced)
      </li>
    )
  }
  return (
    <ul className="grid gap-1 text-sm text-muted-foreground">
      {row("Jev", "jev")}
      {row("LLM", "llm")}
    </ul>
  )
}

function Recent() {
  const list = useComparisons(10)
  if (!list.data?.items.length) return null
  return (
    <section className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h2 className="font-medium">Latest comparisons</h2>
        <Link
          to="/comparisons"
          className="text-sm underline underline-offset-4"
        >
          View all
        </Link>
      </div>
      <ComparisonTable items={list.data.items} />
    </section>
  )
}

function NoRealRuns({ fake }: { fake: number }) {
  return (
    <EmptyState
      title="No real runs yet"
      action={
        <Button asChild>
          <Link to="/compare">Open Compare</Link>
        </Button>
      }
    >
      Run Jev and the LLM on a ticket from the Compare page, and the results
      appear here.
      {fake > 0 && ` ${fake} fake-AI comparisons are saved but not counted.`}
    </EmptyState>
  )
}

export function DashboardPage() {
  const dashboard = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<DashboardData>("/api/dashboard"),
    refetchInterval: 5000, // numbers update while a test is in progress
  })
  if (dashboard.isPending) return <LoadingState label="Loading dashboard…" />
  if (dashboard.isError)
    return <ErrorState error={dashboard.error} onRetry={dashboard.refetch} />

  const data = dashboard.data
  const m = data.metrics
  if (!m)
    return (
      <div className="flex flex-col gap-6">
        <NoRealRuns fake={data.fake_comparisons_excluded} />
        <EvaluationSection />
      </div>
    )
  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-1 text-sm text-muted-foreground">
        <p>
          Jev side: {data.models.jev.join(", ") || "—"} · LLM side:{" "}
          {data.models.llm.join(", ") || "—"}
        </p>
        <p>
          Agreement shows how often the two sides gave the same answer. It is
          not accuracy: accuracy is measured separately below, only on tickets
          with labelled answers.
          {data.fake_comparisons_excluded > 0 &&
            ` ${data.fake_comparisons_excluded} fake-AI comparisons are not counted here.`}
        </p>
      </div>
      <Stats data={data} m={m} />
      <Reliability m={m} />
      <div className="grid gap-4 lg:grid-cols-2">
        <AgreementChart m={m} />
        <SideBySideChart title="Priority by side" field="priority" m={m} />
        <SideBySideChart title="Category by side" field="category" m={m} />
        <SideBySideChart title="Sentiment by side" field="sentiment" m={m} />
      </div>
      <Recent />
      <EvaluationSection />
    </div>
  )
}
