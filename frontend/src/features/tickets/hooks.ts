import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query"

import { api, send } from "@/services/api"
import type {
  Execution,
  ExecutionPage,
  FinalClassificationInput,
  ImportSummary,
  Ticket,
  TicketInput,
  TicketPage,
} from "@/types/api"

export type TicketQuery = Partial<
  Record<
    "q" | "category" | "priority" | "status" | "sort" | "order" | "page",
    string
  >
>

export const useTickets = (query: TicketQuery) =>
  useQuery({
    queryKey: ["tickets", "list", query],
    queryFn: () =>
      api<TicketPage>(`/api/tickets?${new URLSearchParams(query)}`),
    placeholderData: keepPreviousData, // keep the old page visible while the next one loads
  })

export const useTicket = (ticketId: string, enabled = true) =>
  useQuery({
    queryKey: ["tickets", ticketId],
    queryFn: () => api<Ticket>(`/api/tickets/${encodeURIComponent(ticketId)}`),
    enabled: enabled && ticketId !== "",
    retry: false,
  })

/** A ticket write. The UI changes only once the API confirms it (AGENTS.md section 3). */
function useTicketWrite<V>(write: (vars: V) => Promise<Ticket | undefined>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: write,
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ["tickets", "list"] })
      if (ticket)
        queryClient.setQueryData(["tickets", ticket.ticket_id], ticket)
    },
  })
}

const path = (ticketId: string) =>
  `/api/tickets/${encodeURIComponent(ticketId)}`

export const useCreateTicket = () =>
  useTicketWrite((input: TicketInput) =>
    send<Ticket>("POST", "/api/tickets", input),
  )

export const useUpdateTicket = (ticketId: string) =>
  useTicketWrite((changes: Partial<TicketInput> & { status?: string }) =>
    send<Ticket>("PATCH", path(ticketId), changes),
  )

export const useAddNote = (ticketId: string) =>
  useTicketWrite((text: string) =>
    send<Ticket>("POST", `${path(ticketId)}/notes`, { text }),
  )

export const useSetFinal = (ticketId: string) =>
  useTicketWrite((input: FinalClassificationInput) =>
    send<Ticket>("PUT", `${path(ticketId)}/final-classification`, input),
  )

export const useTicketRuns = (ticketId: string) =>
  useQuery({
    queryKey: ["executions", "ticket", ticketId],
    queryFn: () =>
      api<ExecutionPage>(
        `/api/executions?ticket_id=${encodeURIComponent(ticketId)}&page_size=100`,
      ),
  })

/** One provider on one ticket. Paid calls are never retried automatically (AGENTS.md section 3). */
export function useRunProvider(ticketId: string, provider: "jev" | "gpt") {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () =>
      send<Execution>("POST", `${path(ticketId)}/runs/${provider}`),
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["executions"] })
      queryClient.invalidateQueries({ queryKey: ["tickets", "list"] })
    },
  })
}

export const useDeleteTicket = (ticketId: string) =>
  useTicketWrite(() => send<undefined>("DELETE", path(ticketId)))

/** CSV import. `dryRun` checks the file and saves nothing. */
export function useImportTickets() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ file, dryRun }: { file: File; dryRun: boolean }) =>
      api<ImportSummary>(`/api/imports/tickets?dry_run=${dryRun}`, {
        method: "POST",
        body: file,
        headers: { "Content-Type": "text/csv" },
      }),
    onSuccess: (summary) => {
      if (!summary.dry_run)
        queryClient.invalidateQueries({ queryKey: ["tickets", "list"] })
    },
  })
}
