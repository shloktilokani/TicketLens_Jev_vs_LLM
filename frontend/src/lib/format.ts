const dateTime = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
})

export const formatDateTime = (iso: string) => dateTime.format(new Date(iso))

export const seconds = (ms: number | null) =>
  ms === null ? "—" : `${(ms / 1000).toFixed(2)} s`

export const SIDE_LABELS: Record<string, string> = { jev: "Jev", gpt: "LLM" }

export const formatEscalation = (required: boolean) =>
  required ? "Required" : "Not required"

export function formatTokens(
  usage: {
    input_tokens: number | null
    output_tokens: number | null
    usage_source: string
  } | null,
): string {
  if (!usage || usage.usage_source === "unavailable") return "—"
  return `${usage.input_tokens ?? "?"} / ${usage.output_tokens ?? "?"}`
}

/** An estimated USD cost. Tiny amounts keep their digits: a Jev call costs fractions of a cent. */
export function formatCost(amount: string | number | null | undefined): string {
  if (amount === null || amount === undefined) return "—"
  const value = Number(amount)
  if (value === 0) return "$0.00"
  return `$${value < 0.01 ? value.toFixed(6) : value.toFixed(4)}`
}
