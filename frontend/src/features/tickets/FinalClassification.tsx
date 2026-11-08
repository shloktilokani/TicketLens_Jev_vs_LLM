import { useId, useState } from "react"
import { Link } from "react-router"
import { toast } from "sonner"

import { Detail } from "@/components/Detail"
import { ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useSetFinal } from "@/features/tickets/hooks"
import { formatDateTime, formatEscalation, SIDE_LABELS } from "@/lib/format"
import { useTaxonomy } from "@/services/queries"
import type {
  Classification,
  ExecutionSummary,
  FinalClassification as Final,
  Taxonomy,
  Ticket,
} from "@/types/api"

const EMPTY = {
  category: "",
  subcategory: "",
  priority: "",
  sentiment: "",
  escalation: "", // no default: the operator must decide, not inherit "Not required"
}
const ESCALATION_OPTIONS = [formatEscalation(true), formatEscalation(false)]

function startingValues(answer: Classification | null | undefined) {
  if (!answer) return EMPTY
  return {
    category: answer.category,
    subcategory: answer.subcategory,
    priority: answer.priority,
    sentiment: answer.sentiment,
    escalation: formatEscalation(answer.escalation_required),
  }
}

function Field({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: string
  options: string[]
  onChange: (value: string) => void
}) {
  const id = useId()
  return (
    <div className="grid gap-1">
      <Label htmlFor={id}>{label}</Label>
      <Select
        value={value}
        onValueChange={onChange}
        disabled={options.length === 0}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder="Choose…" />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

function FinalForm({
  ticket,
  taxonomy,
  run,
  onClose,
}: {
  ticket: Ticket
  taxonomy: Taxonomy
  run: ExecutionSummary | null
  onClose: () => void
}) {
  const final = ticket.final_classification
  const [form, setForm] = useState(() =>
    startingValues(run?.normalized_result ?? final),
  )
  const save = useSetFinal(ticket.ticket_id)
  const set = (field: keyof typeof EMPTY) => (value: string) =>
    setForm((f) => ({ ...f, [field]: value }))

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    const { escalation, ...fields } = form
    save.mutate(
      {
        ...fields,
        escalation_required: escalation === formatEscalation(true),
        selected_from_execution_id:
          run?.execution_id ?? final?.selected_from_execution_id ?? null,
      },
      {
        onSuccess: () => {
          toast.success("Final classification saved")
          onClose()
        },
        onError: (error) => toast.error(error.message),
      },
    )
  }

  return (
    <form className="grid gap-4" onSubmit={submit}>
      <p className="text-sm text-muted-foreground">
        {run &&
          `Starting from ${SIDE_LABELS[run.provider]}'s answer of ${formatDateTime(run.started_at)}. `}
        Change anything you need. Nothing is saved until you press Save.
      </p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Field
          label="Category"
          value={form.category}
          options={Object.keys(taxonomy.categories)}
          onChange={(category) =>
            // A subcategory only fits its own category, so changing category clears it.
            setForm((f) => ({ ...f, category, subcategory: "" }))
          }
        />
        <Field
          label="Subcategory"
          value={form.subcategory}
          options={taxonomy.categories[form.category] ?? []}
          onChange={set("subcategory")}
        />
        <Field
          label="Priority"
          value={form.priority}
          options={taxonomy.priorities}
          onChange={set("priority")}
        />
        <Field
          label="Sentiment"
          value={form.sentiment}
          options={taxonomy.sentiments}
          onChange={set("sentiment")}
        />
        <Field
          label="Escalation"
          value={form.escalation}
          options={ESCALATION_OPTIONS}
          onChange={set("escalation")}
        />
      </div>
      <div className="flex gap-2">
        <Button
          type="submit"
          disabled={!Object.values(form).every(Boolean) || save.isPending}
        >
          {save.isPending ? "Saving…" : "Save final classification"}
        </Button>
        <Button type="button" variant="outline" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </form>
  )
}

function SavedFinal({ final }: { final: Final | null }) {
  if (!final) {
    return (
      <p className="text-sm text-muted-foreground">
        Not chosen yet. Use an answer from the AI results below, or set it by
        hand. It is never set automatically.
      </p>
    )
  }
  const runId = final.selected_from_execution_id
  return (
    <dl className="grid gap-3 sm:grid-cols-3">
      <Detail label="Category" value={final.category} />
      <Detail label="Subcategory" value={final.subcategory} />
      <Detail label="Priority" value={final.priority} />
      <Detail label="Sentiment" value={final.sentiment} />
      <Detail
        label="Escalation"
        value={formatEscalation(final.escalation_required)}
      />
      <Detail
        label="Source"
        value={
          runId ? (
            <Link
              to={`/executions/${runId}`}
              className="underline underline-offset-4"
            >
              {final.manually_edited
                ? "AI answer, then edited"
                : "AI answer, unchanged"}
            </Link>
          ) : (
            "Set by hand"
          )
        }
      />
      <Detail
        label="Saved"
        value={final.updated_at && formatDateTime(final.updated_at)}
      />
    </dl>
  )
}

function FormLoader(props: {
  ticket: Ticket
  run: ExecutionSummary | null
  onClose: () => void
}) {
  const taxonomy = useTaxonomy()
  if (taxonomy.isError)
    return <ErrorState error={taxonomy.error} onRetry={taxonomy.refetch} />
  if (!taxonomy.data) return <LoadingState label="Loading choices…" />
  return <FinalForm {...props} taxonomy={taxonomy.data} />
}

/** The operator's final answer. It changes only when the operator presses Save. */
export function FinalClassificationPanel({
  id,
  ticket,
  run,
  onDone,
}: {
  id: string
  ticket: Ticket
  run: ExecutionSummary | null
  onDone: () => void
}) {
  const [editing, setEditing] = useState(false)
  const final = ticket.final_classification
  const open = editing || run !== null
  const close = () => {
    setEditing(false)
    onDone()
  }
  return (
    <Card id={id} tabIndex={-1} className="outline-none">
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle>Final classification</CardTitle>
        {!open && (
          <Button variant="outline" size="sm" onClick={() => setEditing(true)}>
            {final ? "Edit" : "Set by hand"}
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {open ? (
          // The key restarts the form when a different AI answer is chosen.
          <FormLoader
            key={run?.execution_id ?? "by-hand"}
            ticket={ticket}
            run={run}
            onClose={close}
          />
        ) : (
          <SavedFinal final={final} />
        )}
      </CardContent>
    </Card>
  )
}
