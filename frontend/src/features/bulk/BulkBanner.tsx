import { useQueryClient } from "@tanstack/react-query"
import { useEffect, useState } from "react"
import { Link } from "react-router"

import { attemptsDone, isActive, useBulkJobs } from "@/features/bulk/hooks"
import type { BulkJob } from "@/types/api"

const SHOW_FINISHED_MS = 10 * 60 * 1000

function isRecent(job: BulkJob, now: number) {
  return (
    job.completed_at !== null &&
    now - new Date(job.completed_at).getTime() < SHOW_FINISHED_MS
  )
}

/** Non-blocking progress on every page, so the operator can navigate away during a run. */
export function BulkBanner() {
  const job = useBulkJobs(1).data?.items[0]
  const [now] = useState(() => Date.now())
  const queryClient = useQueryClient()
  const done = job ? attemptsDone(job) : 0

  // Runs change other pages' data while they happen, so refresh those as progress moves.
  useEffect(() => {
    if (done === 0) return
    for (const queryKey of [
      ["tickets", "list"],
      ["executions"],
      ["comparisons"],
    ])
      queryClient.invalidateQueries({ queryKey })
  }, [done, queryClient])

  if (!job || !(isActive(job) || isRecent(job, now))) return null
  return (
    <div
      role="status"
      className="mb-4 grid gap-2 rounded-lg border p-3 text-sm"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span>
          <span className="font-medium">Bulk run: {job.status}.</span> {done} of{" "}
          {job.total} attempts done · {job.failed} failed · {job.skipped}{" "}
          skipped
        </span>
        <Link
          to={`/bulk-runs/${job.job_id}`}
          className="underline underline-offset-4"
        >
          View details
        </Link>
      </div>
      <progress
        className="h-2 w-full accent-primary"
        value={done}
        max={job.total}
        aria-label="Bulk run progress"
      />
    </div>
  )
}
