import type { ReactNode } from "react"

/** One labelled value inside a <dl>. Missing values show as a dash. */
export function Detail({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm break-words">{value ?? "—"}</dd>
    </div>
  )
}
