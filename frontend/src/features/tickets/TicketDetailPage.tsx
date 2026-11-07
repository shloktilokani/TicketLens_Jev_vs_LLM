import { useQueryClient } from "@tanstack/react-query"
import { Pencil, Trash2 } from "lucide-react"
import { useState } from "react"
import { Link, useNavigate, useParams } from "react-router"
import { toast } from "sonner"

import { ConfirmDialog } from "@/components/ConfirmDialog"
import { EmptyState, ErrorState, LoadingState } from "@/components/states"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { TicketForm } from "@/features/tickets/TicketForm"
import {
  useAddNote,
  useDeleteTicket,
  useTicket,
  useUpdateTicket,
} from "@/features/tickets/hooks"
import { formatDateTime } from "@/lib/format"
import { ApiError } from "@/services/api"
import { useTaxonomy } from "@/services/queries"
import type { Ticket } from "@/types/api"

const fail = (error: Error) => toast.error(error.message)

function StatusSelect({ ticket }: { ticket: Ticket }) {
  const statuses = useTaxonomy().data?.statuses ?? []
  const update = useUpdateTicket(ticket.ticket_id)
  // Controlled by the saved status: the select changes only after the API confirms.
  return (
    <Select
      value={ticket.status}
      disabled={update.isPending}
      onValueChange={(status) =>
        update.mutate(
          { status },
          {
            onSuccess: () => toast.success(`Status set to ${status}`),
            onError: fail,
          },
        )
      }
    >
      <SelectTrigger className="w-40" aria-label="Status">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {statuses.map((s) => (
          <SelectItem key={s} value={s}>
            {s}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function Detail({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value ?? "—"}</dd>
    </div>
  )
}

function TicketInfo({ ticket }: { ticket: Ticket }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Ticket</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        {/* pre-wrap keeps the customer's line breaks and spacing exactly as entered */}
        <p className="text-sm break-words whitespace-pre-wrap">
          {ticket.description}
        </p>
        <dl className="grid gap-3 sm:grid-cols-3">
          <Detail label="Customer" value={ticket.customer.name} />
          <Detail label="Email" value={ticket.customer.email} />
          <Detail label="Channel" value={ticket.submission_channel} />
          <Detail label="Order ID" value={ticket.order.order_id} />
          <Detail label="Product" value={ticket.order.product_name} />
          <Detail label="Created" value={formatDateTime(ticket.created_at)} />
        </dl>
      </CardContent>
    </Card>
  )
}

function FinalClassificationPanel({ ticket }: { ticket: Ticket }) {
  const final = ticket.final_classification
  return (
    <Card>
      <CardHeader>
        <CardTitle>Final classification</CardTitle>
      </CardHeader>
      <CardContent>
        {final ? (
          <dl className="grid gap-3 sm:grid-cols-3">
            <Detail label="Category" value={final.category} />
            <Detail label="Subcategory" value={final.subcategory} />
            <Detail label="Priority" value={final.priority} />
            <Detail label="Sentiment" value={final.sentiment} />
            <Detail
              label="Escalation"
              value={final.escalation_required ? "Required" : "Not required"}
            />
            <Detail
              label="Source"
              value={
                final.manually_edited ? "Set by hand" : "From an AI result"
              }
            />
          </dl>
        ) : (
          <p className="text-sm text-muted-foreground">
            Not chosen yet. You will pick it from the AI results (Phase 12); it
            is never set automatically.
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function Notes({ ticket }: { ticket: Ticket }) {
  const [text, setText] = useState("")
  const addNote = useAddNote(ticket.ticket_id)
  return (
    <Card>
      <CardHeader>
        <CardTitle>Internal notes</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3">
        {ticket.operator_notes.length === 0 && (
          <p className="text-sm text-muted-foreground">No notes yet.</p>
        )}
        <ul className="grid gap-2">
          {ticket.operator_notes.map((note) => (
            <li key={note.note_id} className="rounded-md border p-2 text-sm">
              <p className="whitespace-pre-wrap">{note.text}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {formatDateTime(note.created_at)}
              </p>
            </li>
          ))}
        </ul>
        <form
          className="grid gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            addNote.mutate(text, {
              onSuccess: () => setText(""),
              onError: fail,
            })
          }}
        >
          <Textarea
            aria-label="New note"
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
          />
          <Button
            type="submit"
            variant="outline"
            className="justify-self-start"
            disabled={!text.trim() || addNote.isPending}
          >
            {addNote.isPending ? "Adding…" : "Add note"}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

function AiResults({ ticketId }: { ticketId: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>AI results</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 text-sm text-muted-foreground">
        <p>Run history on this page arrives with Phases 11 and 12.</p>
        <Button
          asChild
          variant="outline"
          size="sm"
          className="justify-self-start"
        >
          <Link to={`/compare?ticket=${encodeURIComponent(ticketId)}`}>
            Run Jev + GPT in Compare
          </Link>
        </Button>
      </CardContent>
    </Card>
  )
}

function TicketView({ ticket }: { ticket: Ticket }) {
  const [editing, setEditing] = useState(false)
  const [confirming, setConfirming] = useState(false)
  const channels = useTaxonomy().data?.channels ?? []
  const update = useUpdateTicket(ticket.ticket_id)
  const remove = useDeleteTicket(ticket.ticket_id)
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const deleteTicket = () =>
    remove.mutate(undefined, {
      onSuccess: () => {
        queryClient.removeQueries({ queryKey: ["tickets", ticket.ticket_id] })
        toast.success(`${ticket.ticket_id} deleted`)
        navigate("/tickets")
      },
      onError: fail,
    })

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="mr-auto text-lg font-semibold">
          <span className="font-mono text-sm text-muted-foreground">
            {ticket.ticket_id}
          </span>{" "}
          {ticket.title}
        </h2>
        <StatusSelect ticket={ticket} />
        <Button
          variant="outline"
          size="sm"
          onClick={() => setEditing(true)}
          disabled={editing}
        >
          <Pencil aria-hidden /> Edit
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setConfirming(true)}
        >
          <Trash2 aria-hidden /> Delete
        </Button>
      </div>
      {editing ? (
        <TicketForm
          channels={channels}
          initial={{
            title: ticket.title,
            description: ticket.description,
            customer_name: ticket.customer.name,
            customer_email: ticket.customer.email,
            order_id: ticket.order.order_id ?? "",
            product_name: ticket.order.product_name ?? "",
            submission_channel: ticket.submission_channel,
          }}
          submitLabel="Save changes"
          pending={update.isPending}
          onCancel={() => setEditing(false)}
          onSubmit={(input) =>
            update.mutate(input, {
              onSuccess: () => {
                setEditing(false)
                toast.success("Changes saved")
              },
              onError: fail,
            })
          }
        />
      ) : (
        <TicketInfo ticket={ticket} />
      )}
      <FinalClassificationPanel ticket={ticket} />
      <AiResults ticketId={ticket.ticket_id} />
      <Notes ticket={ticket} />
      <ConfirmDialog
        open={confirming}
        onOpenChange={setConfirming}
        title={`Delete ${ticket.ticket_id}?`}
        description="This permanently deletes the ticket and all of its AI runs and comparisons. It cannot be undone."
        confirmLabel="Delete ticket"
        pending={remove.isPending}
        onConfirm={deleteTicket}
      />
    </div>
  )
}

export function TicketDetailPage() {
  const { ticketId = "" } = useParams()
  const ticket = useTicket(ticketId)

  if (ticket.isPending) return <LoadingState label="Loading ticket…" />
  if (ticket.error instanceof ApiError && ticket.error.status === 404) {
    return (
      <EmptyState
        title={`Ticket ${ticketId} not found`}
        action={
          <Link to="/tickets" className="text-sm underline underline-offset-4">
            Back to tickets
          </Link>
        }
      />
    )
  }
  if (ticket.isError)
    return <ErrorState error={ticket.error} onRetry={ticket.refetch} />
  return <TicketView ticket={ticket.data} />
}
