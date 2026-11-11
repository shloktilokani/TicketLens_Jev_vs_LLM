import { CircleCheck } from "lucide-react"
import { Link } from "react-router"
import { toast } from "sonner"

import { ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { TicketForm } from "@/features/tickets/TicketForm"
import { useCreateTicket } from "@/features/tickets/hooks"
import { useTaxonomy } from "@/services/queries"

export function NewTicketPage() {
  const taxonomy = useTaxonomy()
  const create = useCreateTicket()

  if (taxonomy.isPending) return <LoadingState />
  if (taxonomy.isError)
    return <ErrorState error={taxonomy.error} onRetry={taxonomy.refetch} />

  if (create.data) {
    const id = create.data.ticket_id
    return (
      <div
        role="status"
        className="flex max-w-xl flex-col gap-4 rounded-lg border p-6"
      >
        <p className="flex items-center gap-2 text-lg font-medium">
          <CircleCheck className="size-5 text-green-600" aria-hidden />
          Ticket {id} created
        </p>
        <p className="text-sm text-muted-foreground">
          It is saved as Open. No AI has run on it yet: run Jev, the LLM or both
          from its page, or from Compare.
        </p>
        <div className="flex gap-2">
          <Button asChild>
            <Link to={`/tickets/${id}`}>Open {id}</Link>
          </Button>
          <Button variant="outline" onClick={() => create.reset()}>
            Create another
          </Button>
        </div>
      </div>
    )
  }

  return (
    <TicketForm
      channels={taxonomy.data.channels}
      submitLabel="Create ticket"
      pending={create.isPending}
      onSubmit={(input) =>
        create.mutate(input, { onError: (error) => toast.error(error.message) })
      }
    />
  )
}
