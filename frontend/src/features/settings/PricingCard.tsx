import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useSaveSettings } from "@/features/settings/hooks"
import { SIDE_LABELS } from "@/lib/format"
import type { AppSettings } from "@/types/api"

type Row = {
  id: number
  provider: string
  model: string
  input_per_million: string
  output_per_million: string
}

export function PricingCard({ pricing }: { pricing: AppSettings["pricing"] }) {
  const [rows, setRows] = useState<Row[]>(() =>
    pricing.map((entry, id) => ({
      id,
      provider: entry.provider,
      model: entry.model,
      input_per_million: String(entry.input_per_million),
      output_per_million: String(entry.output_per_million),
    })),
  )
  const save = useSaveSettings("PUT", "/pricing")
  const change = (id: number, field: keyof Row, value: string) =>
    setRows((all) =>
      all.map((row) => (row.id === id ? { ...row, [field]: value } : row)),
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Prices per million tokens</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <p className="text-sm text-muted-foreground">
          Costs are estimates. A model with no row here uses its default: local
          models cost nothing, hosted Jev uses its published rate, and anything
          else stays unpriced. Each run keeps the rates it was saved with, so
          changes here never alter past costs. Check rates against the
          provider's current price list.
        </p>
        {rows.length > 0 && (
          <div className="overflow-x-auto rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  {["Side", "Model", "Input (USD)", "Output (USD)", ""].map(
                    (h) => (
                      <TableHead key={h}>{h}</TableHead>
                    ),
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>
                      <Select
                        value={row.provider}
                        onValueChange={(v) => change(row.id, "provider", v)}
                      >
                        <SelectTrigger className="w-24" aria-label="Side">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {Object.entries(SIDE_LABELS).map(([key, label]) => (
                            <SelectItem key={key} value={key}>
                              {label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Input
                        aria-label="Model"
                        value={row.model}
                        onChange={(e) =>
                          change(row.id, "model", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        aria-label="Input price per million tokens"
                        inputMode="decimal"
                        className="w-28"
                        value={row.input_per_million}
                        onChange={(e) =>
                          change(row.id, "input_per_million", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Input
                        aria-label="Output price per million tokens"
                        inputMode="decimal"
                        className="w-28"
                        value={row.output_per_million}
                        onChange={(e) =>
                          change(row.id, "output_per_million", e.target.value)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Remove ${row.model || "this row"}`}
                        onClick={() =>
                          setRows((all) => all.filter((r) => r.id !== row.id))
                        }
                      >
                        <Trash2 aria-hidden />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() =>
              setRows((all) => [
                ...all,
                {
                  id: Date.now(),
                  provider: "gpt",
                  model: "",
                  input_per_million: "0",
                  output_per_million: "0",
                },
              ])
            }
          >
            <Plus aria-hidden /> Add price
          </Button>
          <Button
            disabled={save.isPending}
            onClick={() =>
              save.mutate({
                entries: rows.map((row) => ({
                  provider: row.provider,
                  model: row.model,
                  input_per_million: row.input_per_million,
                  output_per_million: row.output_per_million,
                })),
              })
            }
          >
            {save.isPending ? "Saving…" : "Save prices"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
