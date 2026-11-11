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
  execution_statuses: string[]
}

export type ProviderStatus = Record<
  "jev" | "gpt",
  { configured: boolean; label: string }
>

export type Classification = {
  category: string
  subcategory: string
  priority: string
  sentiment: string
  escalation_required: boolean
}

export type FinalClassificationInput = Classification & {
  selected_from_execution_id: string | null
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
  latest_run: { provider: string; status: string; started_at: string } | null
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
    amount: string | number | null
    currency: string
    is_estimate: boolean
  } | null
  error: {
    code: string | null
    http_status: number | null
    message: string
  } | null
  pricing_snapshot: {
    currency: string
    input_per_million: string | number
    output_per_million: string | number
    pricing_version: string
  } | null
  prompt_version: string
  taxonomy_version: string
  input_snapshot: unknown
  request_payload_redacted: unknown
  response_payload_redacted: unknown
}

/** A run as listed in the log: everything except the payloads. */
export type ExecutionSummary = Omit<
  Execution,
  "input_snapshot" | "request_payload_redacted" | "response_payload_redacted"
>

export type ExecutionPage = {
  items: ExecutionSummary[]
  total: number
  page: number
  page_size: number
}

export type FieldScore = {
  correct: number
  scored: number
  accuracy: number | null
  macro_f1?: number | null
}

export type EvaluationSide = {
  labelled: number
  scored: number
  failed: number
  not_run: number
  models: string[]
  per_field: Record<string, FieldScore & { macro_f1: number | null }>
  exact_match: FieldScore
  confusion: Record<
    "category" | "priority" | "sentiment" | "escalation_required",
    { labels: string[]; counts: number[][] }
  >
}

export type EvaluationScored = {
  labelled_tickets: number
  scored: boolean
  sides: { jev: EvaluationSide; llm: EvaluationSide }
  head_to_head: {
    compared_tickets: number
    per_field: Record<
      string,
      {
        compared: number
        both_correct: number
        jev_only: number
        llm_only: number
        both_wrong: number
        agreed: number
        agreement: number | null
      }
    >
  }
}

export type AppSettings = {
  providers: ProviderStatus
  jev_model: string
  llm_model: string
  jev_escalation_threshold: number
  bulk_concurrency: number
  prompt: {
    version: string
    instructions: string
    history: { version: string; instructions: string; created_at: string }[]
  }
  taxonomy: { version: string; categories: Record<string, string[]> }
  pricing: {
    provider: string
    model: string
    input_per_million: string | number
    output_per_million: string | number
    pricing_version: string
  }[]
  updated_at: string | null
}

export type BulkProvider = "jev" | "gpt"

export type BulkJob = {
  job_id: string
  ticket_ids: string[] | null
  all_eligible: boolean
  providers: BulkProvider[]
  status: string
  total: number
  completed: number
  failed: number
  skipped: number
  outcomes: {
    ticket_id: string
    provider: BulkProvider
    status: string
    execution_id: string | null
  }[]
  created_at: string
  started_at: string | null
  completed_at: string | null
  error_summary: string | null
}

export type BulkJobList = { items: BulkJob[]; total: number }

export type BulkStart = {
  ticket_ids?: string[]
  all_eligible?: boolean
  providers: BulkProvider[]
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

export type LatencyStats = {
  count: number
  mean: number | null
  median: number | null
  p90: number | null
  min: number | null
  max: number | null
}

type SideMetric<T> = { jev: T; llm: T }

export type RunMetrics = {
  tickets: number
  comparisons: Record<string, number>
  exact_matches: number
  mean_agreement: number | null
  per_field: Record<
    string,
    {
      agreed: number
      compared: number
      rate: number | null
      kappa: number | null
    }
  >
  outcomes: SideMetric<{
    total: number
    counts: Record<string, number>
    success_rate: number | null
  }>
  latency: SideMetric<LatencyStats>
  wall_clock: LatencyStats
  tokens: SideMetric<{
    reported_runs: number
    mean_input: number | null
    mean_output: number | null
  }>
  distributions: SideMetric<Record<string, Record<string, number>>>
  cost: SideMetric<{ priced_runs: number; total: number | null }>
}

export type DashboardData = {
  tickets: { total: number; by_status: Record<string, number> }
  real_comparisons: number
  fake_comparisons_excluded: number
  models: { jev: string[]; llm: string[] }
  metrics: RunMetrics | null
}

export type ComparisonListItem = {
  comparison_id: string
  ticket_id: string
  title: string
  status: string
  agreement_count: number
  comparable_field_count: number
  jev_model: string | null
  llm_model: string | null
  jev_ms: number | null
  llm_ms: number | null
  fake: boolean
  created_at: string
}

export type ComparisonList = { items: ComparisonListItem[]; total: number }

export type ComparisonDetail = {
  ticket: Pick<Ticket, "ticket_id" | "title"> & Partial<Ticket>
  jev: Execution | null
  llm: Execution | null
  comparison: Comparison
}
