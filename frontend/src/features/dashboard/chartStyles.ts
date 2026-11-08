export const FIELD_LABELS: Record<string, string> = {
  category: "Category",
  subcategory: "Subcategory",
  priority: "Priority",
  sentiment: "Sentiment",
  escalation_required: "Escalation",
}

export const TOOLTIP = {
  contentStyle: {
    background: "var(--popover)",
    border: "1px solid var(--border)",
    borderRadius: 8,
    color: "var(--popover-foreground)",
  },
  cursor: { fill: "var(--muted)", opacity: 0.5 },
}

export const AXIS = { fill: "var(--muted-foreground)", fontSize: 12 }

export const percent = (rate: number | null) =>
  rate === null ? "—" : `${Math.round(rate * 100)}%`
