import { Link } from "react-router"

import { EmptyState } from "@/components/states"

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
