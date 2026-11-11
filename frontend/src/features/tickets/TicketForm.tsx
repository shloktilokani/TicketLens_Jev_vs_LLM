import { zodResolver } from "@hookform/resolvers/zod"
import { Controller, useForm } from "react-hook-form"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import type { TicketInput } from "@/types/api"

// Mirrors backend/app/schemas/tickets.py; the backend re-checks everything.
const schema = z.object({
  title: z
    .string()
    .trim()
    .min(1, "Enter a title")
    .max(200, "At most 200 characters"),
  // Not trimmed: the description is stored exactly as typed.
  description: z
    .string()
    .max(10_000, "At most 10,000 characters")
    .refine((v) => v.trim().length > 0, "Enter a description"),
  customer_name: z.string().trim().min(1, "Enter the customer's name").max(200),
  customer_email: z
    .string()
    .trim()
    .regex(/^[^@\s]+@[^@\s]+\.[^@\s]+$/, "Enter a valid email address"),
  order_id: z.string().trim().max(200),
  product_name: z.string().trim().max(200),
  submission_channel: z.string().min(1, "Choose a channel"),
})

type FormValues = z.infer<typeof schema>

const EMPTY_TICKET: FormValues = {
  title: "",
  description: "",
  customer_name: "",
  customer_email: "",
  order_id: "",
  product_name: "",
  submission_channel: "",
}

type Props = {
  channels: string[]
  initial?: FormValues
  submitLabel: string
  pending: boolean
  onSubmit: (input: TicketInput) => void
  onCancel?: () => void
}

function Field({
  id,
  label,
  error,
  children,
}: {
  id: string
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="grid gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}

/** Shared create/edit form. Optional fields left blank are sent as null. */
export function TicketForm({
  channels,
  initial = EMPTY_TICKET,
  submitLabel,
  pending,
  onSubmit,
  onCancel,
}: Props) {
  const { register, control, handleSubmit, formState } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: initial,
  })
  const { errors } = formState
  const msg = (name: keyof FormValues) => errors[name]?.message
  const field = (name: keyof FormValues) => ({
    id: name,
    "aria-invalid": Boolean(errors[name]),
    "aria-describedby": errors[name] ? `${name}-error` : undefined,
    ...register(name),
  })

  return (
    <form
      noValidate
      className="grid max-w-2xl gap-4"
      onSubmit={handleSubmit((v) =>
        onSubmit({
          ...v,
          order_id: v.order_id || null,
          product_name: v.product_name || null,
        }),
      )}
    >
      <Field id="title" label="Title" error={msg("title")}>
        <Input {...field("title")} />
      </Field>
      <Field id="description" label="Description" error={msg("description")}>
        <Textarea rows={6} {...field("description")} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field
          id="customer_name"
          label="Customer name"
          error={msg("customer_name")}
        >
          <Input autoComplete="off" {...field("customer_name")} />
        </Field>
        <Field
          id="customer_email"
          label="Customer email"
          error={msg("customer_email")}
        >
          <Input type="email" autoComplete="off" {...field("customer_email")} />
        </Field>
        <Field
          id="order_id"
          label="Order ID (optional)"
          error={msg("order_id")}
        >
          <Input {...field("order_id")} />
        </Field>
        <Field
          id="product_name"
          label="Product name (optional)"
          error={msg("product_name")}
        >
          <Input {...field("product_name")} />
        </Field>
      </div>
      <Field
        id="submission_channel"
        label="Submission channel"
        error={msg("submission_channel")}
      >
        <Controller
          control={control}
          name="submission_channel"
          render={({ field: f }) => (
            <Select value={f.value} onValueChange={f.onChange}>
              <SelectTrigger
                id="submission_channel"
                className="w-48"
                aria-invalid={Boolean(errors.submission_channel)}
              >
                <SelectValue placeholder="Choose a channel" />
              </SelectTrigger>
              <SelectContent>
                {channels.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? "Saving…" : submitLabel}
        </Button>
        {onCancel && (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={pending}
          >
            Cancel
          </Button>
        )}
      </div>
    </form>
  )
}
