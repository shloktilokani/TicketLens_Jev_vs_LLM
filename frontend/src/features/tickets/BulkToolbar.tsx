import { useState } from "react"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/ConfirmDialog"
import { Button } from "@/components/ui/button"
import { useStartBulk } from "@/features/bulk/hooks"
import type { BulkProvider } from "@/types/api"

const MODES: { label: string; providers: BulkProvider[]; name: string }[] = [
  { label: "Run Jev", providers: ["jev"], name: "Jev" },
  { label: "Run LLM", providers: ["gpt"], name: "the LLM" },
  { label: "Compare both", providers: ["jev", "gpt"], name: "Jev and the LLM" },
]

type Mode = (typeof MODES)[number]

function confirmText(mode: Mode, selected: number, allEligible: boolean) {
  const calls = `Each side makes one AI call per ticket. Local models cost nothing; hosted models may charge.`
  if (allEligible) {
    return `Runs ${mode.name} on every Open or In Progress ticket. A side that already succeeded on a ticket with the same model is skipped. ${calls}`
  }
  return `Runs ${mode.name} on ${selected} selected ticket${selected === 1 ? "" : "s"}, even if they have been run before. ${calls}`
}

/** Bulk actions for the ticket list. Nothing starts until the operator confirms. */
export function BulkToolbar({
  selected,
  allEligible,
  onAllEligible,
  onClear,
}: {
  selected: string[]
  allEligible: boolean
  onAllEligible: () => void
  onClear: () => void
}) {
  const [mode, setMode] = useState<Mode | null>(null)
  const start = useStartBulk()
  const ready = allEligible || selected.length > 0

  const confirm = () => {
    if (!mode) return
    const target = allEligible
      ? { all_eligible: true }
      : { ticket_ids: selected }
    start.mutate(
      { ...target, providers: mode.providers },
      {
        onSuccess: () => {
          toast.success("Bulk run started")
          setMode(null)
          onClear()
        },
        onError: (error) => {
          toast.error(error.message)
          setMode(null)
        },
      },
    )
  }

  return (
    <div
      role="group"
      aria-label="Bulk actions"
      className="flex flex-wrap items-center gap-2 rounded-lg border p-2 text-sm"
    >
      <span className="px-1 font-medium">
        {allEligible ? "All eligible tickets" : `${selected.length} selected`}
      </span>
      {MODES.map((m) => (
        <Button
          key={m.label}
          size="sm"
          variant="outline"
          disabled={!ready}
          onClick={() => setMode(m)}
        >
          {m.label}
        </Button>
      ))}
      <Button
        size="sm"
        variant="ghost"
        aria-pressed={allEligible}
        onClick={onAllEligible}
      >
        Select all eligible
      </Button>
      <Button size="sm" variant="ghost" disabled={!ready} onClick={onClear}>
        Clear selection
      </Button>
      <ConfirmDialog
        open={mode !== null}
        onOpenChange={(open) => !open && setMode(null)}
        title={mode ? `${mode.label}?` : ""}
        description={
          mode ? confirmText(mode, selected.length, allEligible) : ""
        }
        confirmLabel="Start bulk run"
        variant="default"
        pending={start.isPending}
        onConfirm={confirm}
      />
    </div>
  )
}
