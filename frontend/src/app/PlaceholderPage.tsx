import { Link } from "react-router"

import { EmptyState } from "@/components/states"

/** An honest stand-in for a page that a later build phase delivers. Shows no fake data. */
export function PlaceholderPage({
  phase,
  what,
}: {
  phase: number
  what: string
}) {
  return (
    <EmptyState title="Not built yet">
      {what} arrives in Phase {phase} of the build plan.
    </EmptyState>
  )
}

export function NotFoundPage() {
  return (
    <EmptyState
      title="Page not found"
      action={
        <Link to="/" className="text-sm underline underline-offset-4">
          Go to Overview
        </Link>
      }
    />
  )
}
