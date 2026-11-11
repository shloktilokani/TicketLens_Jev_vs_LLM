import { Button } from "@/components/ui/button"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

const ALL = "all" // Radix Select cannot hold an empty value

/** A dropdown filter with an "All ..." option. Reports "" when "All" is chosen. */
export function FilterSelect({
  label,
  value,
  options,
  optionLabels = {},
  onChange,
}: {
  label: string
  value?: string
  options: string[]
  optionLabels?: Record<string, string>
  onChange: (value: string) => void
}) {
  return (
    <Select
      value={value ?? ALL}
      onValueChange={(v) => onChange(v === ALL ? "" : v)}
    >
      <SelectTrigger className="w-44" aria-label={label}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value={ALL}>All {label.toLowerCase()}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option} value={option}>
            {optionLabels[option] ?? option}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export function Pager({
  total,
  page,
  pageSize,
  noun,
  onPage,
}: {
  total: number
  page: number
  pageSize: number
  noun: string
  onPage: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="flex items-center justify-between text-sm text-muted-foreground">
      <span>
        {total} {noun}
        {total === 1 ? "" : "s"} · page {page} of {pages}
      </span>
      <div className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
        >
          Previous
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= pages}
          onClick={() => onPage(page + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  )
}
