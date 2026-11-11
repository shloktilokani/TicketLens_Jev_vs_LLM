import { ResponsiveContainer } from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export function Stat({
  value,
  label,
}: {
  value: string | number
  label: string
}) {
  return (
    <div className="grid gap-1 rounded-lg border p-4">
      <span className="text-2xl font-semibold tabular-nums">{value}</span>
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  )
}

export function ChartCard({
  title,
  height,
  children,
}: {
  title: string
  height: number
  children: React.ReactElement
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div style={{ height }}>
          <ResponsiveContainer width="100%" height="100%">
            {children}
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
