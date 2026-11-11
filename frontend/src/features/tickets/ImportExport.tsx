import { Download, Upload } from "lucide-react"
import { useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useImportTickets } from "@/features/tickets/hooks"
import { BASE_URL } from "@/services/api"
import type { ImportSummary } from "@/types/api"

function Count({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border p-3">
      <p className="text-2xl font-semibold">{value}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  )
}

function SummaryView({ summary }: { summary: ImportSummary }) {
  return (
    <div className="grid gap-3 text-sm">
      <div className="grid grid-cols-3 gap-2">
        <Count
          label={summary.dry_run ? "Ready to import" : "Imported"}
          value={summary.imported}
        />
        <Count label="Invalid rows" value={summary.invalid} />
        <Count label="Duplicates skipped" value={summary.duplicates_skipped} />
      </div>
      <p className="text-muted-foreground">
        {summary.total_rows} rows read.
        {summary.duplicate_rows.length > 0 &&
          ` Duplicate rows: ${summary.duplicate_rows.join(", ")}.`}
      </p>
      {summary.errors.length > 0 && (
        <details open={summary.errors.length <= 10}>
          <summary className="cursor-pointer font-medium">
            Row errors ({summary.errors.length})
          </summary>
          <div className="mt-2 max-h-56 overflow-auto rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Row</TableHead>
                  <TableHead>Column</TableHead>
                  <TableHead>Problem</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {summary.errors.map((e, i) => (
                  <TableRow key={i}>
                    <TableCell>{e.row}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {e.field ?? "—"}
                    </TableCell>
                    <TableCell>{e.message}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </details>
      )}
      {summary.preview.length > 0 && (
        <div>
          <p className="font-medium">First rows</p>
          <ul className="mt-1 list-disc pl-5 text-muted-foreground">
            {summary.preview.map((row, i) => (
              <li key={i}>
                {row.title} · {row.customer_name} · {row.submission_channel}
                {row.labelled && " · labelled"}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export function ImportDialog() {
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const importer = useImportTickets()
  const summary = importer.data

  const run = (dryRun: boolean) =>
    file &&
    importer.mutate(
      { file, dryRun },
      {
        onSuccess: (s) => {
          if (!s.dry_run)
            toast.success(
              `Imported ${s.imported} ticket${s.imported === 1 ? "" : "s"}`,
            )
        },
        onError: (error) => toast.error(error.message),
      },
    )

  const reset = (next: boolean) => {
    setOpen(next)
    if (!next) {
      setFile(null)
      importer.reset()
    }
  }

  const checked = summary?.dry_run === true
  return (
    <Dialog open={open} onOpenChange={reset}>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        <Upload aria-hidden /> Import CSV
      </Button>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Import tickets from CSV</DialogTitle>
          <DialogDescription>
            Check the file first; nothing is saved until you import. AI never
            runs on imported tickets.
          </DialogDescription>
        </DialogHeader>
        <a
          className="text-sm underline underline-offset-4"
          href={`${BASE_URL}/api/imports/template`}
        >
          Download the template
        </a>
        <a
          className="text-sm underline underline-offset-4"
          href={`${BASE_URL}/api/imports/sample-dataset`}
        >
          Download the 100 labelled sample tickets
        </a>
        <Input
          type="file"
          accept=".csv,text/csv"
          aria-label="CSV file"
          onChange={(e) => {
            setFile(e.target.files?.[0] ?? null)
            importer.reset()
          }}
        />
        {summary && <SummaryView summary={summary} />}
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={!file || importer.isPending}
            onClick={() => run(true)}
          >
            Check file
          </Button>
          <Button
            disabled={!checked || summary.imported === 0 || importer.isPending}
            onClick={() => run(false)}
          >
            {importer.isPending
              ? "Working…"
              : `Import ${checked ? summary.imported : ""} tickets`}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

const EXPORTS = [
  { name: "tickets", label: "Tickets" },
  { name: "executions", label: "AI executions" },
  { name: "comparisons", label: "Comparisons" },
]

export function ExportLinks() {
  return (
    <div className="flex flex-wrap items-center gap-2 text-sm">
      {EXPORTS.map(({ name, label }) => (
        <Button key={name} asChild variant="ghost" size="sm">
          <a href={`${BASE_URL}/api/exports/${name}.csv`}>
            <Download aria-hidden /> {label} CSV
          </a>
        </Button>
      ))}
      <span className="text-xs text-muted-foreground">
        Exports never include secrets.
      </span>
    </div>
  )
}
