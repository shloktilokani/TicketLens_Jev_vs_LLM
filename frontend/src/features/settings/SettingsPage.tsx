import { CircleCheck, RefreshCw, TriangleAlert } from "lucide-react"
import { useId, useState } from "react"

import { ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { PricingCard } from "@/features/settings/PricingCard"
import { TaxonomyCard } from "@/features/settings/TaxonomyCard"
import {
  useModelList,
  useSaveSettings,
  useSettings,
} from "@/features/settings/hooks"
import { formatDateTime, SIDE_LABELS } from "@/lib/format"
import type { AppSettings } from "@/types/api"

function ProviderStatus({ settings }: { settings: AppSettings }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Connections</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm">
        {(["jev", "gpt"] as const).map((key) => {
          const { configured, label } = settings.providers[key]
          const Icon = configured ? CircleCheck : TriangleAlert
          return (
            <p key={key} className="flex items-center gap-2">
              <Icon
                className={`size-4 ${configured ? "text-green-600" : "text-destructive"}`}
                aria-hidden
              />
              <span className="font-medium">{SIDE_LABELS[key]}:</span> {label} ·{" "}
              {configured ? "ready" : "not configured"}
            </p>
          )
        })}
        <p className="text-muted-foreground">
          API keys live only in <code>backend/.env</code> on this computer. This
          page cannot show or change them.
        </p>
      </CardContent>
    </Card>
  )
}

function listNote(list: ReturnType<typeof useModelList>) {
  if (list.isFetching) return "Checking this server for models…"
  if (list.isError) return list.error.message
  if (list.data?.error) return list.data.error
  const count = list.data?.models.length ?? 0
  return `${count} model${count === 1 ? "" : "s"} available on this server.`
}

function ModelField({
  side,
  label,
  saved,
}: {
  side: "jev" | "llm"
  label: string
  saved: string
}) {
  const id = useId()
  const [value, setValue] = useState(saved)
  const list = useModelList(side)
  const save = useSaveSettings("PATCH")
  const field = side === "jev" ? "jev_model" : "llm_model"
  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="flex flex-wrap gap-2">
        <Input
          id={id}
          className="w-64"
          list={`${id}-options`}
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
        <datalist id={`${id}-options`}>
          {list.data?.models.map((model) => (
            <option key={model} value={model} />
          ))}
        </datalist>
        <Button
          variant="outline"
          aria-label={`Refresh the ${label} list`}
          disabled={list.isFetching}
          onClick={() => list.refetch()}
        >
          <RefreshCw aria-hidden /> Refresh
        </Button>
        <Button
          disabled={save.isPending || value === saved}
          onClick={() => save.mutate({ [field]: value.trim() })}
        >
          Save
        </Button>
      </div>
      <p className="text-xs text-muted-foreground">{listNote(list)}</p>
    </div>
  )
}

function Tuning({ settings }: { settings: AppSettings }) {
  const [threshold, setThreshold] = useState(
    String(settings.jev_escalation_threshold),
  )
  const [concurrency, setConcurrency] = useState(
    String(settings.bulk_concurrency),
  )
  const save = useSaveSettings("PATCH")
  return (
    <Card>
      <CardHeader>
        <CardTitle>Run behaviour</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <div className="flex flex-wrap gap-4">
          <div className="grid gap-1">
            <Label htmlFor="threshold">Jev escalation threshold (0 to 1)</Label>
            <Input
              id="threshold"
              type="number"
              min="0"
              max="1"
              step="0.05"
              className="w-40"
              value={threshold}
              onChange={(e) => setThreshold(e.target.value)}
            />
          </div>
          <div className="grid gap-1">
            <Label htmlFor="concurrency">Tickets at once in a bulk run</Label>
            <Input
              id="concurrency"
              type="number"
              min="1"
              max="10"
              className="w-40"
              value={concurrency}
              onChange={(e) => setConcurrency(e.target.value)}
            />
          </div>
        </div>
        <Button
          className="justify-self-start"
          disabled={save.isPending}
          onClick={() =>
            save.mutate({
              jev_escalation_threshold: Number(threshold),
              bulk_concurrency: Number(concurrency),
            })
          }
        >
          Save
        </Button>
      </CardContent>
    </Card>
  )
}

function PromptCard({ prompt }: { prompt: AppSettings["prompt"] }) {
  const [text, setText] = useState(prompt.instructions)
  const save = useSaveSettings("PUT", "/prompt")
  return (
    <Card>
      <CardHeader>
        <CardTitle>Prompt (version {prompt.version})</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        <p className="text-sm text-muted-foreground">
          Both sides receive this same text, so the comparison stays fair.
          Saving creates a new version; earlier runs keep the version they used.
        </p>
        <Textarea
          aria-label="Prompt text"
          rows={5}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <Button
          className="justify-self-start"
          disabled={save.isPending || text.trim() === prompt.instructions}
          onClick={() => save.mutate({ instructions: text })}
        >
          {save.isPending ? "Saving…" : "Save as new version"}
        </Button>
        {prompt.history.length > 0 && (
          <details className="rounded-lg border p-3 text-sm">
            <summary className="cursor-pointer font-medium">
              Earlier versions ({prompt.history.length})
            </summary>
            <ul className="mt-2 grid gap-2">
              {prompt.history.map((item) => (
                <li key={item.version} className="rounded-md bg-muted p-2">
                  <p className="text-xs text-muted-foreground">
                    Version {item.version} · {formatDateTime(item.created_at)}
                  </p>
                  <p className="whitespace-pre-wrap">{item.instructions}</p>
                </li>
              ))}
            </ul>
          </details>
        )}
      </CardContent>
    </Card>
  )
}

export function SettingsPage() {
  const query = useSettings()
  if (query.isPending) return <LoadingState label="Loading settings…" />
  if (query.isError)
    return <ErrorState error={query.error} onRetry={query.refetch} />
  const settings = query.data
  return (
    <div className="flex flex-col gap-4">
      <ProviderStatus settings={settings} />
      <Card>
        <CardHeader>
          <CardTitle>Models</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <ModelField side="jev" label="Jev model" saved={settings.jev_model} />
          <ModelField side="llm" label="LLM model" saved={settings.llm_model} />
        </CardContent>
      </Card>
      <Tuning settings={settings} />
      {/* Keys restart a form from what was saved, so it can never show stale values. */}
      <PromptCard key={settings.prompt.version} prompt={settings.prompt} />
      <TaxonomyCard
        key={settings.taxonomy.version}
        taxonomy={settings.taxonomy}
      />
      <PricingCard pricing={settings.pricing} />
    </div>
  )
}
