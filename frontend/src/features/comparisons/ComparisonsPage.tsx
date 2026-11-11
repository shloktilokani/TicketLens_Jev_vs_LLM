import { FlaskConical } from "lucide-react"
import { Link } from "react-router"

import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useComparisons } from "@/features/comparisons/hooks"
import { formatDateTime, seconds } from "@/lib/format"
import type { ComparisonListItem } from "@/types/api"

function agreement(item: ComparisonListItem) {
  if (item.status !== "Completed") return item.status
  return `${item.agreement_count} of ${item.comparable_field_count}`
}

export function ComparisonTable({ items }: { items: ComparisonListItem[] }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            {["Ticket", "Title", "Agreement", "Jev", "LLM", "When"].map((h) => (
              <TableHead key={h}>{h}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow key={item.comparison_id}>
              <TableCell className="font-mono text-xs">
                <Link
                  to={`/comparisons/${item.comparison_id}`}
                  className="underline underline-offset-4"
                >
                  {item.ticket_id}
                </Link>
              </TableCell>
              <TableCell className="max-w-64 truncate">{item.title}</TableCell>
              <TableCell>
                <span className="flex items-center gap-2 whitespace-nowrap">
                  {agreement(item)}
                  {item.fake && (
                    <Badge variant="outline" className="gap-1">
                      <FlaskConical className="size-3" aria-hidden /> Fake AI
                    </Badge>
                  )}
                </span>
              </TableCell>
              <TableCell className="whitespace-nowrap">
                {seconds(item.jev_ms)}
              </TableCell>
              <TableCell className="whitespace-nowrap">
                {seconds(item.llm_ms)}
              </TableCell>
              <TableCell className="whitespace-nowrap">
                {formatDateTime(item.created_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

export function ComparisonsPage() {
  const list = useComparisons(200)
  if (list.isPending) return <LoadingState label="Loading comparisons…" />
  if (list.isError)
    return <ErrorState error={list.error} onRetry={list.refetch} />
  if (list.data.total === 0) {
    return (
      <EmptyState
        title="No comparisons yet"
        action={
          <Button asChild>
            <Link to="/compare">Open Compare</Link>
          </Button>
        }
      >
        Run Jev and the LLM on a ticket from the Compare page. Each run is saved
        here.
      </EmptyState>
    )
  }
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted-foreground">
        {list.data.total} saved comparison{list.data.total === 1 ? "" : "s"},
        newest first. Open one to see both answers side by side.
      </p>
      <ComparisonTable items={list.data.items} />
    </div>
  )
}
