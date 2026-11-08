import { useQuery } from "@tanstack/react-query"
import { useState } from "react"
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  AXIS,
  FIELD_LABELS,
  percent,
  TOOLTIP,
} from "@/features/dashboard/chartStyles"
import { ChartCard, Stat } from "@/features/dashboard/parts"
import { api, BASE_URL } from "@/services/api"
import type { EvaluationScored, EvaluationSide, FieldScore } from "@/types/api"

type SideName = "jev" | "llm"

const SIDE_NAMES: Record<SideName, string> = { jev: "Jev", llm: "LLM" }
const SIDE_COLORS: Record<SideName, string> = {
  jev: "var(--series-jev)",
  llm: "var(--series-llm)",
}
const MAX_SHADE = 60 // percent of the series colour, so cell numbers stay readable

const score = (s: FieldScore) =>
  `${percent(s.accuracy)} (${s.correct} of ${s.scored})`
const f1 = (value: number | null) => (value === null ? "—" : value.toFixed(2))

function coverage(side: EvaluationSide) {
  return `${side.scored} of ${side.labelled} answered · ${side.failed} failed · ${side.not_run} not run`
}

function Tiles({ data }: { data: EvaluationScored }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {(["jev", "llm"] as const).map((name) => {
        const side = data.sides[name]
        return (
          <Stat
            key={name}
            value={percent(side.exact_match.accuracy)}
            label={`${SIDE_NAMES[name]}: all 5 fields right (${side.exact_match.correct} of ${side.exact_match.scored})`}
          />
        )
      })}
      {(["jev", "llm"] as const).map((name) => (
        <Stat
          key={name}
          value={data.sides[name].scored}
          label={`${SIDE_NAMES[name]}: ${coverage(data.sides[name])}`}
        />
      ))}
    </div>
  )
}

function AccuracyChart({ data }: { data: EvaluationScored }) {
  const rows = Object.keys(FIELD_LABELS).map((field) => {
    const jev = data.sides.jev.per_field[field]
    const llm = data.sides.llm.per_field[field]
    return {
      field: FIELD_LABELS[field],
      Jev: Math.round((jev.accuracy ?? 0) * 100),
      LLM: Math.round((llm.accuracy ?? 0) * 100),
      detail: { Jev: score(jev), LLM: score(llm) },
    }
  })
  return (
    <ChartCard title="Accuracy by field" height={320}>
      <BarChart
        data={rows}
        layout="vertical"
        margin={{ left: 16, right: 24 }}
        barGap={2}
      >
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
          formatter={(_value, name, item) => [
            item.payload.detail[name as string],
            name,
          ]}
        />
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

function ScoreTable({ data }: { data: EvaluationScored }) {
  const { per_field: duel, compared_tickets: compared } = data.head_to_head
  return (
    <div className="grid gap-2">
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              {[
                "Field",
                "Jev accuracy",
                "LLM accuracy",
                "Jev F1",
                "LLM F1",
                "Both right",
                "Jev only",
                "LLM only",
                "Both wrong",
                "Agree",
              ].map((h) => (
                <TableHead key={h}>{h}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {Object.entries(FIELD_LABELS).map(([field, label]) => {
              const jev = data.sides.jev.per_field[field]
              const llm = data.sides.llm.per_field[field]
              const d = duel[field]
              return (
                <TableRow key={field} className="tabular-nums">
                  <TableCell>{label}</TableCell>
                  <TableCell className="whitespace-nowrap">
                    {score(jev)}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {score(llm)}
                  </TableCell>
                  <TableCell>{f1(jev.macro_f1)}</TableCell>
                  <TableCell>{f1(llm.macro_f1)}</TableCell>
                  <TableCell>{d.both_correct}</TableCell>
                  <TableCell>{d.jev_only}</TableCell>
                  <TableCell>{d.llm_only}</TableCell>
                  <TableCell>{d.both_wrong}</TableCell>
                  <TableCell>{percent(d.agreement)}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
      <p className="text-xs text-muted-foreground">
        Accuracy counts answered tickets only. The last five columns compare the{" "}
        {compared} tickets both sides answered. F1 is macro-F1, shown from 30
        answered tickets up.
      </p>
    </div>
  )
}

function Toggle<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: Record<T, string>
  value: T
  onChange: (value: T) => void
}) {
  return (
    <div role="group" aria-label={label} className="flex gap-1">
      {(Object.keys(options) as T[]).map((key) => (
        <Button
          key={key}
          size="sm"
          variant={key === value ? "default" : "outline"}
          aria-pressed={key === value}
          onClick={() => onChange(key)}
        >
          {options[key]}
        </Button>
      ))}
    </div>
  )
}

const MATRIX_FIELDS = {
  category: "Category",
  priority: "Priority",
  sentiment: "Sentiment",
  escalation_required: "Escalation",
}

function Matrix({ data }: { data: EvaluationScored }) {
  const [side, setSide] = useState<SideName>("jev")
  const [field, setField] = useState<keyof typeof MATRIX_FIELDS>("category")
  const { labels, counts } = data.sides[side].confusion[field]
  const largest = Math.max(1, ...counts.flat())
  return (
    <section className="grid gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-medium">Where each side goes wrong</h3>
        <div className="flex flex-wrap gap-2">
          <Toggle
            label="Side"
            options={SIDE_NAMES}
            value={side}
            onChange={setSide}
          />
          <Toggle
            label="Field"
            options={MATRIX_FIELDS}
            value={field}
            onChange={setField}
          />
        </div>
      </div>
      <div className="overflow-x-auto rounded-lg border">
        <Table>
          <caption className="p-2 text-left text-xs text-muted-foreground">
            Rows are the labelled answer, columns are what {SIDE_NAMES[side]}{" "}
            said. The diagonal, in bold, is correct.
          </caption>
          <TableHeader>
            <TableRow>
              <TableHead>Labelled answer</TableHead>
              {labels.map((name) => (
                <TableHead key={name} className="text-center">
                  {name}
                </TableHead>
              ))}
              <TableHead className="text-center">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {labels.map((name, row) => (
              <TableRow key={name} className="tabular-nums">
                <TableCell className="whitespace-nowrap">{name}</TableCell>
                {counts[row].map((count, column) => (
                  <TableCell
                    key={labels[column]}
                    className={`text-center ${row === column ? "font-semibold" : ""}`}
                    style={{
                      background: count
                        ? `color-mix(in oklab, ${SIDE_COLORS[side]} ${Math.round((count / largest) * MAX_SHADE)}%, transparent)`
                        : undefined,
                    }}
                  >
                    {count}
                  </TableCell>
                ))}
                <TableCell className="text-center text-muted-foreground">
                  {counts[row].reduce((a, b) => a + b, 0)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  )
}

function Scored({ data }: { data: EvaluationScored }) {
  const models = (["jev", "llm"] as const)
    .map(
      (name) =>
        `${SIDE_NAMES[name]}: ${data.sides[name].models.join(", ") || "—"}`,
    )
    .join(" · ")
  return (
    <>
      <p className="text-sm text-muted-foreground">
        {data.labelled_tickets} labelled tickets, scored on each side's latest
        finished real run. {models}. Failed runs are listed, not counted as
        wrong. The tickets are synthetic, so this is not real-world accuracy.
      </p>
      <Tiles data={data} />
      <AccuracyChart data={data} />
      <ScoreTable data={data} />
      <Matrix data={data} />
    </>
  )
}

/** Accuracy against labelled answers. Shows nothing misleading until real runs are scored. */
export function EvaluationSection() {
  const query = useQuery({
    queryKey: ["evaluation"],
    queryFn: () => api<EvaluationScored>("/api/evaluation"),
    refetchInterval: 5000, // numbers update while a bulk run is in progress
  })

  let body
  if (query.isPending) body = <LoadingState label="Loading accuracy…" />
  else if (query.isError)
    body = <ErrorState error={query.error} onRetry={query.refetch} />
  else if (query.data.labelled_tickets === 0)
    body = (
      <EmptyState
        title="No labelled tickets yet"
        action={
          <Button asChild variant="outline">
            <a href={`${BASE_URL}/api/imports/sample-dataset`}>
              Download the 100 labelled tickets
            </a>
          </Button>
        }
      >
        Accuracy needs tickets with known answers. Download the sample set and
        import it from the Tickets page. Nothing is added automatically.
      </EmptyState>
    )
  else if (!query.data.scored)
    body = (
      <EmptyState
        title="No labelled tickets scored yet"
        action={
          <Button asChild variant="outline">
            <Link to="/tickets">Open Tickets</Link>
          </Button>
        }
      >
        {query.data.labelled_tickets} labelled tickets are ready. Run them on
        real models from the Tickets page. Fake-AI runs are never scored.
      </EmptyState>
    )
  else body = <Scored data={query.data} />

  return (
    <section className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold">
        Accuracy against labelled answers
      </h2>
      {body}
    </section>
  )
}
