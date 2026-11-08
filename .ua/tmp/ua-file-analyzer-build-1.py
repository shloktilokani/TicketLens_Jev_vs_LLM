"""Build the batch 1 graph fragment from the extraction results and analyst-written semantics."""
import json
import math
import re
from pathlib import Path

UA = Path("/Users/shloktilokani/Projects/TicketLens_Jev_vs_LLM/.ua")
batch = json.loads((UA / "tmp/batch-input-1.json").read_text())
extract = json.loads((UA / "tmp/ua-file-extract-results-1.json").read_text())
results = {r["path"]: r for r in extract["results"]}

B = "backend/app/"
AD, AX, AI, AR, AT = (B + f"api/{n}.py" for n in ("dashboard", "executions", "imports", "runs", "tickets"))
DEPS = B + "api/deps.py"
CLOCK = B + "core/clock.py"
RC, RE, RL, RT = (B + f"repositories/{n}.py" for n in ("comparisons", "executions", "labels", "tickets"))
SC, SI = B + "schemas/comparisons.py", B + "schemas/imports.py"
VC, VX, VI, VD, VM, VR = (
    B + f"services/{n}.py"
    for n in ("comparisons", "csv_export", "csv_import", "dashboard", "run_metrics", "run_report")
)
SCRIPT = "backend/scripts/run_report.py"
TC, TM = "backend/tests/test_csv.py", "backend/tests/test_run_metrics.py"
# Cross-batch modules
VE, VT = B + "services/executions.py", B + "services/tickets.py"
DB, SET, MAIN = B + "repositories/database.py", B + "core/settings.py", B + "main.py"

FILES = {
    AD: ("FastAPI routes for the Overview metrics and for listing and reading stored Jev-vs-LLM comparisons, delegating all work to the dashboard service.", ["api-handler", "dashboard", "fastapi", "comparisons"], "simple", None),
    DEPS: ("Shared FastAPI dependency that exposes the MongoDB database held on application state as the injectable `Db` type used by every route module.", ["middleware", "dependency-injection", "fastapi", "database"], "simple", "`Annotated[Database, Depends(get_db)]` packages the dependency into a reusable type alias, so routes declare `db: Db` instead of repeating `Depends`."),
    AX: ("FastAPI routes for the execution log: a filtered, paginated list of every AI attempt without payloads, and a detail route returning one attempt in full.", ["api-handler", "execution-log", "fastapi", "pagination"], "simple", None),
    AI: ("FastAPI routes for the CSV import template, ticket imports with a dry-run mode and a 5 MB size limit, and CSV downloads of tickets, executions and comparisons.", ["api-handler", "csv", "import-export", "fastapi", "validation"], "simple", "The async import route hands synchronous PyMongo work to `run_in_threadpool` so it does not block the event loop."),
    AR: ("FastAPI routes that run one provider on one ticket and record a comparison between finished Jev and GPT runs, without ever choosing a winner.", ["api-handler", "provider-runs", "comparisons", "fastapi"], "simple", None),
    AT: ("FastAPI CRUD routes for tickets, covering search, filtering, sorting, pagination, notes, the operator's final classification and cascading deletion.", ["api-handler", "tickets", "crud", "fastapi", "pagination"], "moderate", None),
    CLOCK: ("Provides the UTC clock used for stored timestamps, truncated to the millisecond precision that BSON dates keep.", ["utility", "time", "bson", "timestamps"], "simple", None),
    B + "repositories/__init__.py": ("Empty package marker for the MongoDB repository layer.", ["package-marker", "repository-layer", "python"], "simple", None),
    RC: ("MongoDB access for Jev-vs-GPT comparison records: insert, newest-first listing, counting and lookup by ID.", ["repository", "data-access", "mongodb", "comparisons"], "simple", None),
    RE: ("MongoDB access for AI execution records, including updates, comparison linking, each ticket's latest run and a paginated search that leaves out payloads.", ["repository", "data-access", "mongodb", "execution-log", "aggregation"], "moderate", None),
    RL: ("Write-only MongoDB access for evaluation labels, which are kept apart from tickets and never read when building provider requests.", ["repository", "data-access", "mongodb", "evaluation-labels"], "simple", None),
    RT: ("MongoDB access for tickets and the atomic ticket-ID counter, with plain-text search, priority-ranked sorting, status counts and dependents-first deletion.", ["repository", "data-access", "mongodb", "tickets", "aggregation"], "moderate", None),
    SC: ("Pydantic models for a Jev-vs-GPT comparison record, its per-field values and the request that creates one.", ["data-model", "validation", "pydantic", "comparisons"], "simple", None),
    SI: ("Pydantic models for the CSV import result: row-level errors and the summary of imported, invalid and duplicate rows.", ["data-model", "validation", "pydantic", "csv"], "simple", None),
    B + "services/__init__.py": ("Empty package marker for the service layer.", ["package-marker", "service-layer", "python"], "simple", None),
    VC: ("Compares one Jev run with one GPT run on the five shared fields, validates both executions and stores the agreement figures while leaving the final answer to the operator.", ["service", "comparisons", "evaluation", "business-logic"], "moderate", None),
    VX: ("Builds CSV exports of tickets, AI executions and comparisons from declarative column maps, omitting payloads and neutralizing spreadsheet formula injection.", ["service", "csv", "serialization", "security", "import-export"], "moderate", None),
    VI: ("Imports tickets from CSV with row-level validation, value normalization, fingerprint-based duplicate detection, a dry-run mode and separately stored evaluation labels.", ["service", "csv", "validation", "idempotent-import", "evaluation-labels"], "moderate", None),
    VD: ("Assembles Overview and Comparisons page data by joining stored comparisons with their runs and tickets, keeping fake-provider runs out of the metrics.", ["service", "dashboard", "metrics", "comparisons"], "moderate", None),
    VM: ("Computes pure metrics for a set of Jev-vs-LLM comparisons: per-field agreement and Cohen's kappa, latency, tokens, outcomes, cost, Jev confidence, distributions and disagreements.", ["service", "metrics", "statistics", "evaluation", "pure-functions"], "moderate", None),
    VR: ("Renders one test run as a self-contained HTML report with inline CSS, SVG charts and summary tables, escaping stored text and stating that agreement is not accuracy.", ["service", "report", "html-rendering", "svg-charts", "evaluation"], "complex", None),
    SCRIPT: ("Command-line entry point that loads named comparisons from MongoDB and writes a test run's HTML report and JSON record to reports/test-runs.", ["entry-point", "cli", "report", "script"], "moderate", None),
    TC: ("API-level tests for CSV import and export, covering row counts, normalization, duplicates, dry runs, label separation, malformed files, formula neutralization and payload exclusion.", ["test", "csv", "api-test", "import-export"], "moderate", None),
    TM: ("Unit tests for the run metrics, using hand-built rows to check percentile, kappa, completed-only agreement, latency, tokens, outcomes, cost and Jev confidence.", ["test", "metrics", "unit-test", "statistics"], "moderate", None),
}

# (file, symbol) -> (summary, tags, complexity)
S = {}


def add(path, entries):
    for name, summary, tags, *rest in entries:
        S[(path, name)] = (summary, tags, rest[0] if rest else "simple")


add(AD, [
    ("get_dashboard", "GET /api/dashboard route returning ticket counts and metrics from stored real runs.", ["api-handler", "dashboard", "metrics"]),
    ("list_comparisons", "GET /api/comparisons route listing stored comparisons newest first, with a bounded limit and an optional ticket filter.", ["api-handler", "comparisons", "listing"]),
    ("get_comparison", "GET /api/comparisons/{comparison_id} route returning one comparison with its ticket and both runs, or a 404.", ["api-handler", "comparisons", "detail"]),
])
add(DEPS, [("get_db", "Returns the MongoDB database stored on the FastAPI application state for the current request.", ["dependency-injection", "database", "fastapi"])])
add(AX, [
    ("list_executions", "GET /api/executions route that filters attempts by provider, status, ticket and date range and returns one page without payloads.", ["api-handler", "execution-log", "pagination"]),
    ("get_execution", "GET /api/executions/{execution_id} route returning one attempt in full with redacted payloads, or a 404.", ["api-handler", "execution-log", "detail"]),
])
add(AI, [
    ("csv_download", "Wraps CSV text in a UTF-8 attachment response with the given filename.", ["utility", "csv", "http-response"]),
    ("import_template", "GET /api/imports/template route that downloads an empty CSV containing the import columns.", ["api-handler", "csv", "template"]),
    ("import_tickets", "POST /api/imports/tickets route that enforces the 5 MB limit, runs the import off the event loop and maps whole-file CSV errors to a 400.", ["api-handler", "csv", "validation", "import-export"], "moderate"),
    ("export_csv", "GET /api/exports/{name}.csv route that downloads tickets, executions or comparisons as CSV.", ["api-handler", "csv", "import-export"]),
])
add(AR, [
    ("run_provider", "POST route that runs one provider on an existing ticket in a worker thread, so Jev and GPT can run side by side, and returns the recorded execution.", ["api-handler", "provider-runs", "concurrency"]),
    ("create_comparison", "POST /api/comparisons route that creates a comparison from two runs and maps comparison errors to their HTTP status.", ["api-handler", "comparisons", "error-handling"]),
])
add(AT, [
    ("found", "Returns the ticket, or raises a 404 when it is missing.", ["utility", "error-handling", "tickets"]),
    ("create_ticket", "POST route that creates a ticket with status Open and never triggers AI.", ["api-handler", "tickets", "crud"]),
    ("list_tickets", "GET route that searches, filters, sorts and paginates tickets and attaches each ticket's latest run.", ["api-handler", "tickets", "pagination", "search"], "moderate"),
    ("get_ticket", "GET route returning one ticket, or a 404.", ["api-handler", "tickets", "crud"]),
    ("update_ticket", "PATCH route applying a partial ticket update, or returning a 404.", ["api-handler", "tickets", "crud"]),
    ("add_note", "POST route appending a note to a ticket, or returning a 404.", ["api-handler", "tickets", "notes"]),
    ("set_final_classification", "PUT route saving the operator's final answer, by hand or from one of the ticket's runs, and returning a 422 when the run is unusable.", ["api-handler", "tickets", "classification"]),
    ("delete_ticket", "DELETE route removing a ticket with its runs, comparisons and labels, logging database failures and returning a safe 500 when the delete is incomplete.", ["api-handler", "tickets", "deletion", "error-handling"]),
])
add(CLOCK, [("utc_now", "Returns the current UTC time truncated to milliseconds, so values returned at creation match those read back from MongoDB.", ["utility", "time", "bson"])])
add(RC, [
    ("insert", "Inserts a copy of a comparison document so the caller's dict does not gain an ObjectId.", ["repository", "mongodb", "write"]),
    ("newest_first", "Returns comparisons newest first, optionally for one ticket, with a limit of 0 meaning all.", ["repository", "mongodb", "query"]),
    ("count", "Counts comparisons, optionally for one ticket.", ["repository", "mongodb", "query"]),
    ("get", "Fetches one comparison by ID without the MongoDB _id.", ["repository", "mongodb", "query"]),
])
add(RE, [
    ("insert", "Inserts a copy of an execution document so the caller's dict does not gain an ObjectId.", ["repository", "mongodb", "write"]),
    ("update", "Applies field changes to an execution and returns the updated document.", ["repository", "mongodb", "write"]),
    ("get", "Fetches one execution by ID without the MongoDB _id.", ["repository", "mongodb", "query"]),
    ("link_comparison", "Sets the comparison ID on the given executions.", ["repository", "mongodb", "write"]),
    ("latest_by_ticket", "Aggregates each ticket's most recent run into a map of provider, status and start time.", ["repository", "mongodb", "aggregation"], "moderate"),
    ("search", "Returns one page of runs newest first, without payloads, plus the total, treating the end date as the whole UTC day.", ["repository", "mongodb", "pagination", "search"], "moderate"),
])
add(RL, [("insert", "Inserts one evaluation label document.", ["repository", "mongodb", "evaluation-labels"])])
add(RT, [
    ("next_ticket_id", "Issues the next SK-prefixed ticket ID from an atomic upserted counter; IDs are never reused and gaps are acceptable.", ["repository", "mongodb", "id-generation", "concurrency"]),
    ("insert", "Inserts a copy of a ticket document so the caller's dict does not gain an ObjectId.", ["repository", "mongodb", "write"]),
    ("get", "Fetches one ticket by ID without the MongoDB _id.", ["repository", "mongodb", "query"]),
    ("fingerprint_exists", "Checks whether a ticket with the given import fingerprint is already stored.", ["repository", "mongodb", "deduplication"]),
    ("update", "Applies MongoDB update operators and returns the updated ticket, or None if it does not exist.", ["repository", "mongodb", "write"]),
    ("delete_with_dependents", "Deletes a ticket's comparisons, executions and labels first and the ticket last, so a failed delete can simply be retried on standalone MongoDB.", ["repository", "mongodb", "deletion", "data-integrity"]),
    ("search", "Returns one page of tickets plus the total, escaping search text and ranking by priority with unclassified tickets always last.", ["repository", "mongodb", "aggregation", "search", "pagination"], "complex"),
    ("counts", "Returns the total number of tickets and the number in each status.", ["repository", "mongodb", "aggregation"]),
])
add(SC, [
    ("FieldComparison", "One shared field's Jev and GPT values and whether they match; match is None when either side has no value.", ["data-model", "pydantic", "comparisons"]),
    ("Comparison", "A stored comparison of Jev and GPT on the five shared fields with agreement figures, which never names a winner.", ["data-model", "pydantic", "comparisons"]),
    ("ComparisonCreate", "Request body naming a ticket and the Jev and GPT executions to compare.", ["data-model", "pydantic", "api-schema"]),
])
add(SI, [
    ("ImportRowError", "One validation error tied to a 1-based data row and, where known, a field.", ["data-model", "pydantic", "validation"]),
    ("ImportSummary", "Result of an import: total, imported, invalid and duplicate counts, row errors, new ticket IDs and a dry-run preview.", ["data-model", "pydantic", "csv"]),
])
add(VC, [
    ("ComparisonError", "ValueError carrying the HTTP status code the API should return for a failed comparison.", ["error-handling", "comparisons", "exception"]),
    ("field_comparison", "Builds per-field Jev and GPT values, with match set only when both sides have a validated result.", ["comparisons", "evaluation", "business-logic"]),
    ("status_of", "Derives Completed, Partial or Unavailable from which provider results exist.", ["comparisons", "status", "business-logic"]),
    ("load", "Fetches an execution and checks that it exists, belongs to the ticket and provider, and has finished running.", ["comparisons", "validation", "data-access"]),
    ("create", "Loads both runs, computes field agreement, stores the comparison and links it back to both executions.", ["comparisons", "evaluation", "business-logic"], "moderate"),
])
add(VX, [
    ("value_at", "Reads a dotted path from a nested document, returning None when any step is missing.", ["utility", "serialization", "csv"]),
    ("cell", "Formats a value for CSV and prefixes a quote on cells a spreadsheet could run as formulas.", ["serialization", "csv", "security"]),
    ("to_csv", "Writes documents to CSV text using the given header-to-path column map.", ["serialization", "csv", "utility"]),
    ("export", "Loads the named collection in sorted order and serializes it with its column map.", ["service", "csv", "import-export"]),
])
add(VI, [
    ("CsvFileError", "Raised when the file as a whole cannot be read, so nothing is imported.", ["error-handling", "csv", "exception"]),
    ("normalize", "Collapses whitespace and maps enum-like values and booleans to canonical form while keeping descriptions exact.", ["validation", "csv", "normalization"]),
    ("fingerprint", "Hashes title, description, email and order ID into a SHA-256 identity insensitive to case and spacing.", ["deduplication", "hashing", "csv"]),
    ("read_rows", "Decodes UTF-8 with an optional byte-order mark and rejects files with missing columns, no rows or too many rows.", ["validation", "csv", "parsing"], "moderate"),
    ("row_errors", "Converts a Pydantic ValidationError into friendly per-field import row errors.", ["validation", "csv", "error-handling"]),
    ("validate_row", "Validates a row's ticket and optional all-or-nothing expected labels, returning ticket, label and errors.", ["validation", "csv", "evaluation-labels"], "moderate"),
    ("save", "Creates the ticket with its import source and stores any evaluation label separately.", ["csv", "persistence", "evaluation-labels"]),
    ("import_csv", "Runs the import loop, keeping valid rows when others fail, skipping duplicates within the file, in the database or from a concurrent import, and writing nothing in a dry run.", ["csv", "idempotent-import", "business-logic", "orchestration"], "complex"),
])
add(VD, [
    ("load_rows", "Joins comparison records with their two runs and ticket in the given order, labelling deleted tickets.", ["dashboard", "data-joining", "comparisons"], "moderate"),
    ("is_fake", "Detects rows where either side used a mock- model.", ["dashboard", "fake-provider", "filter"]),
    ("model_of", "Returns an execution's actual model, falling back to the requested model.", ["utility", "dashboard", "models"]),
    ("summary", "Builds the Overview payload of ticket counts, real and excluded comparison counts, models and metrics over real runs only.", ["dashboard", "metrics", "fake-provider"], "moderate"),
    ("list_item", "Flattens a joined row into one Comparisons list entry with models, timings and the fake flag.", ["dashboard", "comparisons", "serialization"]),
    ("list_comparisons", "Returns joined list items for the requested comparisons plus their total count.", ["dashboard", "comparisons", "listing"]),
    ("detail", "Returns one comparison joined with its ticket and runs, or None.", ["dashboard", "comparisons", "detail"]),
])
add(VM, [
    ("percentile", "Computes a nearest-rank percentile, returning None for an empty list.", ["statistics", "metrics", "utility"]),
    ("kappa", "Computes Cohen's kappa for label pairs, returning None when there are no pairs or no variety.", ["statistics", "metrics", "evaluation"]),
    ("latency", "Summarizes run durations as count, mean, median, 90th percentile, minimum and maximum.", ["metrics", "latency", "statistics"]),
    ("tokens", "Totals and averages provider-reported tokens and output tokens per second, never estimating unreported usage.", ["metrics", "tokens", "usage"], "moderate"),
    ("outcomes", "Counts runs by status and computes the success rate.", ["metrics", "reliability", "statistics"]),
    ("cost", "Totals the estimated cost of priced runs, returning None when no run has a price.", ["metrics", "cost", "statistics"]),
    ("jev_confidence", "Averages Jev's confidence per field, overall and split by whether the LLM agreed.", ["metrics", "confidence", "evaluation"], "moderate"),
    ("compute", "Produces the full run metrics, using completed comparisons for agreement and every recorded run for latency, tokens, outcomes and cost.", ["metrics", "evaluation", "orchestration", "statistics"], "complex"),
])
add(VR, [
    ("fmt", "Formats a number with digits and a suffix, or a dash when missing.", ["formatting", "utility", "report"]),
    ("pct", "Formats a ratio as a whole percentage, or a dash when missing.", ["formatting", "utility", "report"]),
    ("secs", "Formats milliseconds as seconds, or a dash when missing.", ["formatting", "utility", "report"]),
    ("table", "Renders headers and rows as a horizontally scrollable HTML table with right-aligned numeric columns.", ["html-rendering", "report", "table"]),
    ("agreement_chart", "Draws an inline SVG of horizontal agreement bars, one per field, on a single 0-100% scale.", ["svg-charts", "report", "agreement"], "moderate"),
    ("speed_chart", "Draws an inline SVG dumbbell chart of Jev and LLM seconds per ticket on one shared scale.", ["svg-charts", "report", "latency"], "moderate"),
    ("word", "Returns escaped display text for a field value, showing escalation booleans as words.", ["formatting", "report", "html-escaping"]),
    ("mark", "Returns the HTML marker for agree, differ or not compared.", ["formatting", "report", "html-rendering"]),
    ("ticket_rows", "Builds one table row per ticket with both sides' answers, agreement marks and timings.", ["html-rendering", "report", "table"], "moderate"),
    ("side", "Returns the opening HTML of a legend key with the Jev or LLM color swatch.", ["html-rendering", "report", "legend"]),
    ("render", "Assembles the complete report from run metadata, metrics and rows, covering agreement, speed, reliability, usage, confidence, distributions and disagreements.", ["html-rendering", "report", "orchestration"], "complex"),
])
add(SCRIPT, [
    ("load_run", "Loads the named comparisons in the given order and exits with an error when any are missing.", ["cli", "report", "data-access"]),
    ("main", "Parses arguments, loads the run, closes the database client and writes the HTML report and JSON record.", ["entry-point", "cli", "report"], "moderate"),
])
add(TC, [
    ("api", "Pytest fixture providing a TestClient for an app built with test settings and the test database.", ["test", "fixture", "api-test"]),
    ("upload", "Test helper that posts CSV text or bytes to the import route.", ["test", "helper", "csv"]),
    ("csv_of", "Test helper that joins the import header with the given rows into CSV text.", ["test", "helper", "csv"]),
    ("errors_by_row", "Test helper that groups an import summary's error fields by row number.", ["test", "helper", "csv"]),
    ("test_template_matches_the_spec_file", "Checks the downloaded template is a CSV attachment whose header matches the specification's template file.", ["test", "csv", "template"]),
    ("test_mixed_file_reports_accurate_counts", "Checks a mixed file reports exact imported, invalid and duplicate counts and the fields in error for each row.", ["test", "csv", "validation"]),
    ("test_valid_rows_are_stored_with_import_source_and_normalised_values", "Checks imported rows keep their import source and fingerprint, normalize the channel and set the sample flag from the label.", ["test", "csv", "normalization"]),
    ("test_labels_are_stored_separately_from_tickets", "Checks expected labels go only to evaluation_labels and do not appear on the ticket document.", ["test", "csv", "evaluation-labels"]),
    ("test_reimporting_the_same_file_skips_every_row", "Checks re-importing a file adds no tickets and reports its valid rows as duplicates.", ["test", "csv", "idempotent-import"]),
    ("test_dry_run_reports_without_writing", "Checks a dry run reports counts and a preview while leaving tickets and counters untouched.", ["test", "csv", "dry-run"]),
    ("test_import_never_runs_ai", "Checks an import creates no AI executions or comparisons.", ["test", "csv", "guardrail"]),
    ("test_bom_crlf_and_quoted_multiline_description", "Checks a byte-order mark and CRLF line endings are handled and a quoted multi-line description stays exact.", ["test", "csv", "parsing"]),
    ("test_unreadable_files_are_rejected_whole", "Checks empty, column-deficient, header-only and non-UTF-8 files are each rejected with a 400.", ["test", "csv", "validation"]),
    ("test_oversized_file_is_rejected", "Checks a body over 5 MB is rejected with a 413.", ["test", "csv", "limits"]),
    ("test_supplied_100_ticket_sample_is_valid", "Checks the supplied 100-ticket sample passes a dry run with no invalid rows.", ["test", "csv", "sample-data"]),
    ("read_csv", "Test helper that asserts a successful CSV response and parses it into dictionaries.", ["test", "helper", "csv"]),
    ("test_ticket_export_is_valid_csv_and_neutralises_formulas", "Checks the ticket export parses as CSV and prefixes formula-like cells with a quote.", ["test", "csv", "security"]),
    ("test_execution_export_leaves_out_payloads", "Checks the execution export includes usage and result columns but no stored payload text.", ["test", "csv", "security"]),
    ("test_comparison_export_has_per_field_columns", "Checks the comparison export flattens field comparisons into Jev, GPT and match columns.", ["test", "csv", "comparisons"]),
    ("test_unknown_export_is_404", "Checks an unknown export name is rejected with a 404 or 422.", ["test", "csv", "validation"]),
])
add(TM, [
    ("execution", "Test helper that builds an execution dict with a duration, result, status and optional reported tokens.", ["test", "helper", "fixture-data"]),
    ("result", "Test helper that builds a normalized result with configurable category, priority, confidence and summary.", ["test", "helper", "fixture-data"]),
    ("comparison", "Test helper that builds a Completed comparison when both results exist and a Partial one otherwise.", ["test", "helper", "fixture-data"]),
    ("row", "Test helper that combines a ticket, both executions and their comparison into one metrics row.", ["test", "helper", "fixture-data"]),
    ("test_percentile_and_kappa", "Checks nearest-rank percentile and kappa, including the undefined and perfectly opposed cases.", ["test", "statistics", "metrics"]),
    ("test_agreement_metrics_use_completed_comparisons_only", "Checks agreement figures and disagreements ignore a partial comparison.", ["test", "metrics", "agreement"]),
    ("test_latency_tokens_and_outcomes", "Checks latency, wall-clock, token, outcome and cost metrics against hand-worked values.", ["test", "metrics", "latency"]),
    ("test_jev_confidence_split_by_agreement", "Checks Jev's confidence is averaged separately for agreeing and differing rows.", ["test", "metrics", "confidence"]),
])


def fn(path, name):
    return f"function:{path}:{name}"


# caller file -> caller -> [(callee file, callee)]
CALLS = {
    AD: {"get_dashboard": [(VD, "summary")], "list_comparisons": [(VD, "list_comparisons")], "get_comparison": [(VD, "detail")]},
    AX: {"list_executions": [(RE, "search")], "get_execution": [(RE, "get")]},
    AI: {"import_template": [(AI, "csv_download")], "import_tickets": [(VI, "import_csv")], "export_csv": [(AI, "csv_download"), (VX, "export")]},
    AR: {"run_provider": [(RT, "get"), (VE, "run")], "create_comparison": [(VC, "create")]},
    AT: {
        "create_ticket": [(VT, "create")],
        "list_tickets": [(RT, "search"), (RE, "latest_by_ticket")],
        "get_ticket": [(AT, "found"), (RT, "get")],
        "update_ticket": [(AT, "found"), (VT, "update")],
        "add_note": [(AT, "found"), (VT, "add_note")],
        "set_final_classification": [(AT, "found"), (VT, "set_classification")],
        "delete_ticket": [(RT, "delete_with_dependents")],
    },
    VC: {
        "load": [(RE, "get")],
        "create": [(VC, "load"), (VC, "field_comparison"), (VC, "status_of"), (RC, "insert"), (RE, "link_comparison"), (CLOCK, "utc_now")],
    },
    VX: {"to_csv": [(VX, "cell"), (VX, "value_at")], "export": [(DB, "find_all"), (VX, "to_csv")]},
    VI: {
        "validate_row": [(VI, "normalize"), (VI, "row_errors")],
        "save": [(VT, "create"), (RL, "insert"), (CLOCK, "utc_now")],
        "import_csv": [(VI, "read_rows"), (VI, "validate_row"), (VI, "fingerprint"), (RT, "fingerprint_exists"), (VI, "save")],
    },
    VD: {
        "load_rows": [(DB, "find_in")],
        "summary": [(VD, "load_rows"), (VD, "is_fake"), (VD, "model_of"), (RC, "newest_first"), (RT, "counts"), (VM, "compute")],
        "list_item": [(VD, "model_of"), (VD, "is_fake")],
        "list_comparisons": [(RC, "newest_first"), (RC, "count"), (VD, "load_rows"), (VD, "list_item")],
        "detail": [(RC, "get"), (VD, "load_rows")],
    },
    VM: {
        "latency": [(VM, "percentile")],
        "compute": [(VM, "kappa"), (VM, "outcomes"), (VM, "latency"), (VM, "tokens"), (VM, "cost"), (VM, "jev_confidence")],
    },
    VR: {
        "agreement_chart": [(VR, "pct")],
        "speed_chart": [(VR, "secs")],
        "ticket_rows": [(VR, "word"), (VR, "mark"), (VR, "secs")],
        "render": [(VR, n) for n in ("pct", "secs", "fmt", "word", "side", "table", "agreement_chart", "speed_chart", "ticket_rows")],
    },
    SCRIPT: {
        "load_run": [(DB, "find_in"), (VD, "load_rows")],
        "main": [(SET, "get_settings"), (DB, "connect"), (SCRIPT, "load_run"), (CLOCK, "utc_now"), (VR, "render"), (VM, "compute")],
    },
    TC: {
        "api": [(MAIN, "create_app")],
        "test_mixed_file_reports_accurate_counts": [(TC, "upload"), (TC, "errors_by_row")],
        "test_valid_rows_are_stored_with_import_source_and_normalised_values": [(TC, "upload")],
        "test_labels_are_stored_separately_from_tickets": [(TC, "upload")],
        "test_reimporting_the_same_file_skips_every_row": [(TC, "upload")],
        "test_dry_run_reports_without_writing": [(TC, "upload")],
        "test_import_never_runs_ai": [(TC, "upload")],
        "test_bom_crlf_and_quoted_multiline_description": [(TC, "upload")],
        "test_unreadable_files_are_rejected_whole": [(TC, "upload")],
        "test_oversized_file_is_rejected": [(TC, "csv_of"), (TC, "upload")],
        "test_supplied_100_ticket_sample_is_valid": [(TC, "upload")],
        "test_ticket_export_is_valid_csv_and_neutralises_formulas": [(TC, "upload"), (TC, "csv_of"), (TC, "read_csv")],
        "test_execution_export_leaves_out_payloads": [(TC, "read_csv")],
        "test_comparison_export_has_per_field_columns": [(TC, "read_csv")],
    },
    TM: {
        "row": [(TM, "comparison")],
        "test_percentile_and_kappa": [(VM, "percentile"), (VM, "kappa")],
        "test_agreement_metrics_use_completed_comparisons_only": [(VM, "compute")],
        "test_latency_tokens_and_outcomes": [(VM, "compute")],
        "test_jev_confidence_split_by_agreement": [(VM, "compute")],
    },
}
# Real module imports the scanner resolved only to the package __init__.py.
DEPENDS = [(AT, VT), (VI, VT), (VI, RT)]
TESTED = [(VI, TC), (AI, TC), (VX, TC), (VM, TM), (RT, "backend/tests/test_tickets.py")]

nodes, edges = [], []


def edge(source, target, kind, weight):
    edges.append({"source": source, "target": target, "type": kind, "direction": "forward", "weight": weight})


for spec in batch["files"]:
    path = spec["path"]
    res = results[path]
    summary, tags, complexity, notes = FILES[path]
    node = {"id": f"file:{path}", "type": "file", "name": path.rsplit("/", 1)[1], "filePath": path, "summary": summary, "tags": tags, "complexity": complexity}
    if notes:
        node["languageNotes"] = notes
    nodes.append(node)
    exported = {e["name"] for e in res.get("exports", [])}
    symbols = [("function", s) for s in res.get("functions", [])] + [("class", s) for s in res.get("classes", [])]
    for kind, sym in symbols:
        name = sym["name"]
        text, sym_tags, sym_complexity = S.pop((path, name))
        sym_id = f"{kind}:{path}:{name}"
        nodes.append({"id": sym_id, "type": kind, "name": name, "filePath": path, "lineRange": [sym["startLine"], sym["endLine"]], "summary": text, "tags": sym_tags, "complexity": sym_complexity})
        edge(f"file:{path}", sym_id, "contains", 1.0)
        if name in exported:
            edge(f"file:{path}", sym_id, "exports", 0.8)
    for target in batch["batchImportData"][path]:
        edge(f"file:{path}", f"file:{target}", "imports", 0.7)
assert not S, f"unmatched symbols: {list(S)}"

for path, callers in CALLS.items():
    for caller, callees in callers.items():
        for target_path, callee in callees:
            edge(fn(path, caller), fn(target_path, callee), "calls", 0.8)
for source, target in DEPENDS:
    edge(f"file:{source}", f"file:{target}", "depends_on", 0.6)
for source, target in TESTED:
    edge(f"file:{source}", f"file:{target}", "tested_by", 0.5)

# Validation
ids = {n["id"] for n in nodes}
assert len(ids) == len(nodes), "duplicate node IDs"
assert not {f"file:{f['path']}" for f in batch["files"]} - ids
for n in nodes:
    assert n["summary"] and 3 <= len(n["tags"]) <= 5, n["id"]
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", t) for t in n["tags"]), n["id"]
neighbor_paths, neighbor_symbols = set(), set()
for neighbors in batch["neighborMap"].values():
    for nb in neighbors:
        neighbor_paths.add(nb["path"])
        neighbor_symbols |= {(nb["path"], s) for s in nb["symbols"]}
import_paths = set(batch["batchImportData"]) | {p for v in batch["batchImportData"].values() for p in v}
errors = []
keys = set()
for e in edges:
    key = (e["source"], e["target"], e["type"])
    if key in keys:
        errors.append(f"duplicate edge {key}")
    keys.add(key)
    if e["source"] == e["target"]:
        errors.append(f"self edge {key}")
    for ref in (e["source"], e["target"]):
        if ref in ids:
            continue
        parts = ref.split(":")
        if parts[0] == "file" and (parts[1] in neighbor_paths or parts[1] in import_paths):
            continue
        if parts[0] in ("function", "class") and (parts[1], parts[2]) in neighbor_symbols:
            continue
        errors.append(f"unresolved {ref}")
expected_imports = sum(len(v) for v in batch["batchImportData"].values())
actual_imports = sum(e["type"] == "imports" for e in edges)
assert expected_imports == actual_imports, (expected_imports, actual_imports)
if errors:
    raise SystemExit("\n".join(errors))

# Write, splitting per protocol
out = UA / "intermediate"
for stale in out.glob("batch-1.json"):
    stale.unlink()
for stale in out.glob("batch-1-part-*.json"):
    stale.unlink()
parts = math.ceil(max(len(nodes) / 60, len(edges) / 120))
if parts <= 1:
    (out / "batch-1.json").write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=1))
    print("single", len(nodes), len(edges), "imports", actual_imports)
else:
    paths = sorted(f["path"] for f in batch["files"])
    size = math.ceil(len(paths) / parts)
    total_n = total_e = 0
    for k in range(parts):
        chunk = set(paths[k * size:(k + 1) * size])
        part_nodes = [n for n in nodes if n["filePath"] in chunk]
        part_ids = {n["id"] for n in part_nodes}
        part_edges = [e for e in edges if e["source"] in part_ids]
        name = f"batch-1-part-{k + 1}.json"
        (out / name).write_text(json.dumps({"nodes": part_nodes, "edges": part_edges}, indent=1))
        json.loads((out / name).read_text())
        total_n += len(part_nodes)
        total_e += len(part_edges)
        print(name, len(part_nodes), len(part_edges))
    assert total_n == len(nodes) and total_e == len(edges), (total_n, len(nodes), total_e, len(edges))
    print("total", total_n, total_e, "imports", actual_imports)
