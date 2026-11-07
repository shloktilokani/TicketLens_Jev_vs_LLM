import { useEffect, useState } from "react"

import { send } from "@/services/api"
import type { Comparison, Execution } from "@/types/api"

export type ProviderName = "jev" | "gpt"

export type ProviderRun = {
  state: "idle" | "running" | "done"
  startedAt?: number
  finishedAt?: number
  execution?: Execution
  error?: string // the request itself failed (for example, backend unreachable)
}

export type ComparisonState = {
  state: "idle" | "running" | "done"
  data?: Comparison
  error?: string
}

const IDLE: Record<ProviderName, ProviderRun> = {
  jev: { state: "idle" },
  gpt: { state: "idle" },
}

/**
 * Runs Jev and GPT at the same time with separate requests, so each column finishes (and its
 * timer stops) the moment that provider answers. Then asks the backend to compare and save.
 */
export function useCompareRun() {
  const [runs, setRuns] = useState(IDLE)
  const [comparison, setComparison] = useState<ComparisonState>({
    state: "idle",
  })

  async function start(ticketId: string) {
    const startedAt = performance.now()
    setRuns({
      jev: { state: "running", startedAt },
      gpt: { state: "running", startedAt },
    })
    setComparison({ state: "idle" })

    const runOne = async (provider: ProviderName) => {
      const finish = (result: Partial<ProviderRun>) =>
        setRuns((r) => ({
          ...r,
          [provider]: {
            state: "done",
            startedAt,
            finishedAt: performance.now(),
            ...result,
          },
        }))
      try {
        const execution = await send<Execution>(
          "POST",
          `/api/tickets/${encodeURIComponent(ticketId)}/runs/${provider}`,
        )
        finish({ execution })
        return execution
      } catch (error) {
        finish({ error: (error as Error).message })
        return undefined
      }
    }

    const [jev, gpt] = await Promise.all([runOne("jev"), runOne("gpt")])
    if (!jev || !gpt) return
    setComparison({ state: "running" })
    try {
      const data = await send<Comparison>("POST", "/api/comparisons", {
        ticket_id: ticketId,
        jev_execution_id: jev.execution_id,
        gpt_execution_id: gpt.execution_id,
      })
      setComparison({ state: "done", data })
    } catch (error) {
      setComparison({ state: "done", error: (error as Error).message })
    }
  }

  const reset = () => {
    setRuns(IDLE)
    setComparison({ state: "idle" })
  }

  const running =
    runs.jev.state === "running" ||
    runs.gpt.state === "running" ||
    comparison.state === "running"
  return { runs, comparison, running, start, reset }
}

/** Milliseconds since the run started, ticking while it runs and frozen once it finishes. */
export function useElapsed(run: ProviderRun): number {
  const [now, setNow] = useState(() => performance.now())
  useEffect(() => {
    if (run.state !== "running") return
    const id = setInterval(() => setNow(performance.now()), 47)
    return () => clearInterval(id)
  }, [run.state])
  if (run.startedAt === undefined) return 0
  return Math.max(0, (run.finishedAt ?? now) - run.startedAt)
}

export function formatElapsed(ms: number): string {
  const minutes = Math.floor(ms / 60_000)
  const seconds = Math.floor((ms % 60_000) / 1000)
  const hundredths = Math.floor((ms % 1000) / 10)
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(hundredths).padStart(2, "0")}`
}
