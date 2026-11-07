// Shapes returned by the TicketLens API (backend/app/schemas). Enum-like values stay plain
// strings because their allowed values come from GET /api/taxonomy, the single source.

export type Taxonomy = {
  version: string
  categories: Record<string, string[]>
  priorities: string[]
  sentiments: string[]
  statuses: string[]
  channels: string[]
  providers: string[]
}

export type ProviderStatus = Record<"jev" | "gpt", { configured: boolean }>

export type Classification = {
  category: string
  subcategory: string
  priority: string
  sentiment: string
  escalation_required: boolean
}

export type FinalClassification = Classification & {
  selected_from_execution_id: string | null
  manually_edited: boolean
  taxonomy_version: string
  updated_at: string | null
}

export type Note = { note_id: string; text: string; created_at: string }

export type Ticket = {
  ticket_id: string
  title: string
  description: string
  customer: { name: string; email: string }
  order: { order_id: string | null; product_name: string | null }
  submission_channel: string
  status: string
  final_classification: FinalClassification | null
  operator_notes: Note[]
  source: {
    type: "manual" | "csv_import"
    import_batch_id: string | null
    source_fingerprint: string | null
  }
  is_sample: boolean
  taxonomy_version: string
  created_at: string
  updated_at: string
}

export type TicketPage = {
  items: Ticket[]
  total: number
  page: number
  page_size: number
}

export type TicketInput = {
  title: string
  description: string
  customer_name: string
  customer_email: string
  order_id: string | null
  product_name: string | null
  submission_channel: string
}

export type ImportRowError = {
  row: number
  field: string | null
  message: string
}

export type ImportSummary = {
  dry_run: boolean
  total_rows: number
  imported: number
  invalid: number
  duplicates_skipped: number
  errors: ImportRowError[]
  duplicate_rows: number[]
  imported_ticket_ids: string[]
  preview: (TicketInput & { labelled: boolean })[]
}

export type NormalizedResult = Classification & {
  confidence: Record<string, number>
  summary: string | null
  suggested_resolution: string | null
  unsupported_fields: string[]
  warnings: string[]
}

export type Execution = {
  execution_id: string
  ticket_id: string
  comparison_id: string | null
  provider: "jev" | "gpt"
  requested_model: string
  actual_model: string | null
  status: string
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  normalized_result: NormalizedResult | null
  usage: {
    input_tokens: number | null
    output_tokens: number | null
    total_tokens: number | null
    usage_source: string
  } | null
  estimated_cost: {
    amount: string | null
    currency: string
    is_estimate: boolean
  } | null
  error: {
    code: string | null
    http_status: number | null
    message: string
  } | null
}

export type FieldComparison = {
  jev: string | boolean | null
  gpt: string | boolean | null
  match: boolean | null
}

export type Comparison = {
  comparison_id: string
  ticket_id: string
  jev_execution_id: string | null
  gpt_execution_id: string | null
  status: string
  field_comparison: Record<string, FieldComparison>
  agreement_count: number
  comparable_field_count: number
  agreement_rate: number | null
  created_at: string
}
