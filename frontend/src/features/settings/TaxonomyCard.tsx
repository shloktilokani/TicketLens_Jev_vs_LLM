import { Plus, Trash2 } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useSaveSettings } from "@/features/settings/hooks"
import type { AppSettings } from "@/types/api"

type Row = { id: number; name: string; subcategories: string }

const toRows = (categories: Record<string, string[]>): Row[] =>
  Object.entries(categories).map(([name, subs], id) => ({
    id,
    name,
    subcategories: subs.join("\n"),
  }))

const toBody = (rows: Row[]) => ({
  categories: Object.fromEntries(
    rows.map((row) => [
      row.name.trim(),
      row.subcategories
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    ]),
  ),
})

export function TaxonomyCard({
  taxonomy,
}: {
  taxonomy: AppSettings["taxonomy"]
}) {
  const [rows, setRows] = useState(() => toRows(taxonomy.categories))
  const save = useSaveSettings("PUT", "/taxonomy")
  const change = (id: number, field: "name" | "subcategories", value: string) =>
    setRows((all) =>
      all.map((row) => (row.id === id ? { ...row, [field]: value } : row)),
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Categories and subcategories (version {taxonomy.version})
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <p className="text-sm text-muted-foreground">
          One subcategory per line. Each level needs 2 to 16 options, which is
          the limit Jev accepts. Labels already used by a ticket, run or
          evaluation answer cannot be removed or renamed. Saving creates a new
          version; earlier records keep theirs.
        </p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((row) => (
            <div
              key={row.id}
              className="grid content-start gap-2 rounded-lg border p-3"
            >
              <div className="flex gap-2">
                <Input
                  aria-label="Category name"
                  value={row.name}
                  onChange={(e) => change(row.id, "name", e.target.value)}
                />
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Remove ${row.name || "this category"}`}
                  onClick={() =>
                    setRows((all) => all.filter((r) => r.id !== row.id))
                  }
                >
                  <Trash2 aria-hidden />
                </Button>
              </div>
              <Textarea
                aria-label={`Subcategories of ${row.name || "this category"}`}
                rows={7}
                value={row.subcategories}
                onChange={(e) =>
                  change(row.id, "subcategories", e.target.value)
                }
              />
            </div>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            onClick={() =>
              setRows((all) => [
                ...all,
                { id: Date.now(), name: "", subcategories: "" },
              ])
            }
          >
            <Plus aria-hidden /> Add category
          </Button>
          <Button
            disabled={save.isPending}
            onClick={() => save.mutate(toBody(rows))}
          >
            {save.isPending ? "Saving…" : "Save as new version"}
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
