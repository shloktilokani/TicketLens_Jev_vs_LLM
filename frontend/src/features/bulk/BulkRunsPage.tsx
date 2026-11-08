import { Link, useParams } from "react-router"

import { Detail } from "@/components/Detail"
import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { attemptsDone, useBulkJob, useBulkJobs } from "@/features/bulk/hooks"
import { formatDateTime, SIDE_LABELS } from "@/lib/format"
import { ApiError } from "@/services/api"
import type { BulkJob } from "@/types/api"

const sides = (job: BulkJob) =>
  job.providers.map((p) => SIDE_LABELS[p]).join(" + ")

function Header({ labels }: { labels: string[] }) {
  return (
    <TableHeader>
      <TableRow>
        {labels.map((label) => (
          <TableHead key={label}>{label}</TableHead>
        ))}
      </TableRow>
    </TableHeader>
  )
}

export function BulkRunsPage() {
  const jobs = useBulkJobs(100)
  if (jobs.isPending) return <LoadingState label="Loading bulk runs…" />
  if (jobs.isError)
    return <ErrorState error={jobs.error} onRetry={jobs.refetch} />
  if (jobs.data.total === 0) {
    return (
      <EmptyState
        title="No bulk runs yet"
        action={
          <Button asChild>
            <Link to="/tickets">Open Tickets</Link>
          </Button>
        }
      >
        Select tickets on the Tickets page and choose which AI to run.
      </EmptyState>
    )
  }
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <Header
          labels={[
            "Created",
            "Sides",
            "Selection",
            "Status",
            "Done",
            "Failed",
            "Skipped",
          ]}
        />
        <TableBody>
          {jobs.data.items.map((job) => (
            <TableRow key={job.job_id}>
              <TableCell className="whitespace-nowrap">
                <Link
                  to={`/bulk-runs/${job.job_id}`}
                  className="underline underline-offset-4"
                >
                  {formatDateTime(job.created_at)}
                </Link>
              </TableCell>
              <TableCell>{sides(job)}</TableCell>
              <TableCell>
                {job.all_eligible ? "All eligible" : "Selected"} (
                {job.ticket_ids?.length ?? 0})
              </TableCell>
              <TableCell>{job.status}</TableCell>
              <TableCell className="tabular-nums">
                {attemptsDone(job)} of {job.total}
              </TableCell>
              <TableCell className="tabular-nums">{job.failed}</TableCell>
              <TableCell className="tabular-nums">{job.skipped}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

function Outcomes({ job }: { job: BulkJob }) {
  if (job.outcomes.length === 0)
    return <p className="text-sm text-muted-foreground">No results yet.</p>
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <Header labels={["Ticket", "Side", "Result", "Run"]} />
        <TableBody>
          {job.outcomes.map((outcome) => (
            <TableRow key={`${outcome.ticket_id}-${outcome.provider}`}>
              <TableCell className="font-mono text-xs">
                <Link
                  to={`/tickets/${outcome.ticket_id}`}
                  className="underline underline-offset-4"
                >
                  {outcome.ticket_id}
                </Link>
              </TableCell>
              <TableCell>{SIDE_LABELS[outcome.provider]}</TableCell>
              <TableCell>{outcome.status}</TableCell>
              <TableCell>
                {outcome.execution_id ? (
                  <Link
                    to={`/executions/${outcome.execution_id}`}
                    className="underline underline-offset-4"
                  >
                    Open run
                  </Link>
                ) : (
                  "—"
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function BulkRunDetailPage() {
  const { jobId = "" } = useParams()
  const query = useBulkJob(jobId)
  if (query.isPending) return <LoadingState label="Loading bulk run…" />
  if (query.error instanceof ApiError && query.error.status === 404) {
    return (
      <EmptyState
        title="Bulk run not found"
        action={
          <Link
            to="/bulk-runs"
            className="text-sm underline underline-offset-4"
          >
            Back to bulk runs
          </Link>
        }
      />
    )
  }
  if (query.isError) return <ErrorState error={query.error} />
  const job = query.data
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Bulk run: {job.status}</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          <dl className="grid gap-3 sm:grid-cols-3">
            <Detail label="Sides" value={sides(job)} />
            <Detail
              label="Done"
              value={`${attemptsDone(job)} of ${job.total} attempts`}
            />
            <Detail
              label="Succeeded / failed / skipped"
              value={`${job.completed} / ${job.failed} / ${job.skipped}`}
            />
            <Detail label="Created" value={formatDateTime(job.created_at)} />
            <Detail
              label="Finished"
              value={job.completed_at && formatDateTime(job.completed_at)}
            />
          </dl>
          {job.error_summary && (
            <p role="alert" className="text-sm text-destructive">
              {job.error_summary}
            </p>
          )}
        </CardContent>
      </Card>
      <Outcomes job={job} />
    </div>
  )
}
