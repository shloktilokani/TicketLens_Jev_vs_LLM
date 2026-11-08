"""Builds the batch 4 graph fragment. Line ranges come from the extraction results."""
import json
import math
import os

UA = "/Users/shloktilokani/Projects/TicketLens_Jev_vs_LLM/.ua"
extract = json.load(open(f"{UA}/tmp/ua-file-extract-results-4.json"))
batch = json.load(open(f"{UA}/tmp/batch-input-4.json"))
imports = batch["batchImportData"]
neighbor_map = batch["neighborMap"]
results = {r["path"]: r for r in extract["results"]}

F = "frontend/src/"
COMPARE_RUN = F + "features/compare/useCompareRun.ts"
CMP_DETAIL = F + "features/comparisons/ComparisonDetailPage.tsx"
CMP_LIST = F + "features/comparisons/ComparisonsPage.tsx"
CMP_HOOKS = F + "features/comparisons/hooks.ts"
DASH = F + "features/dashboard/DashboardPage.tsx"
EXEC_DETAIL = F + "features/executions/ExecutionDetailPage.tsx"
EXEC_LIST = F + "features/executions/ExecutionsPage.tsx"
AI = F + "features/tickets/AiResults.tsx"
FINAL = F + "features/tickets/FinalClassification.tsx"
IMPORT = F + "features/tickets/ImportExport.tsx"
NEW = F + "features/tickets/NewTicketPage.tsx"
T_DETAIL = F + "features/tickets/TicketDetailPage.tsx"
T_FORM = F + "features/tickets/TicketForm.tsx"
T_LIST = F + "features/tickets/TicketListPage.tsx"
T_HOOKS = F + "features/tickets/hooks.ts"
FORMAT = F + "lib/format.ts"
UTILS = F + "lib/utils.ts"
API = F + "services/api.ts"
QUERIES = F + "services/queries.ts"
TYPES = F + "types/api.ts"
PROVIDER_COLUMN = F + "features/compare/ProviderColumn.tsx"
CONFIRM = F + "components/ConfirmDialog.tsx"
LIST_CONTROLS = F + "components/ListControls.tsx"

FILES = {
    COMPARE_RUN: ("Drives the live Compare workbench: runs Jev and GPT concurrently as separate requests so each column finishes independently, then asks the backend to save a comparison. Also provides the elapsed-time timer hook and its formatter.", ["hook", "concurrency", "comparison", "timer"], "moderate", None),
    CMP_DETAIL: ("Page that shows one saved comparison, reusing the live provider columns with timers frozen at each run's stored duration. States how many fields agree and that agreement is not accuracy.", ["component", "page", "comparison", "read-only"], "moderate", None),
    CMP_LIST: ("Page listing saved comparisons newest first, and the shared comparison table that the dashboard and ticket detail views also render. Flags fake-AI runs with a badge.", ["component", "page", "comparison", "table"], "moderate", None),
    CMP_HOOKS: ("Single React Query hook that fetches saved comparisons, optionally for one ticket, and polls every 5 seconds so new runs appear during a test.", ["hook", "data-fetching", "comparison", "polling"], "simple", None),
    DASH: ("Dashboard page summarising real comparison runs: ticket counts, agreement rates, side-by-side distribution charts, latency, success and estimated cost. It polls every 5 seconds, excludes fake-AI comparisons and states that agreement is not accuracy.", ["component", "page", "dashboard", "charts", "metrics"], "complex", "Chart colours use CSS variables so Recharts follows the app's theme tokens."),
    EXEC_DETAIL: ("Page for one AI run: status, models, versions, token usage, the pricing snapshot saved with the run and any error. Collapsible, copyable JSON blocks expose the validated result, input snapshot and redacted request and response payloads.", ["component", "page", "execution-log", "debugging", "cost"], "moderate", None),
    EXEC_LIST: ("Paginated log of every AI run, including failures, with provider, status, ticket and UTC date filters kept in the URL so a filtered view can be bookmarked. Also links to the executions CSV export.", ["component", "page", "execution-log", "filtering", "pagination"], "complex", None),
    AI: ("Ticket-level AI panel with buttons that run Jev or the LLM on demand, the ticket's run history and its comparisons. Each successful run offers a 'Use this answer' action that seeds the final classification form.", ["component", "ticket", "provider-run", "history"], "moderate", None),
    FINAL: ("Panel where the operator views and sets a ticket's final classification, by hand or starting from an AI answer. The value changes only on Save, escalation has no default, and changing category clears the subcategory.", ["component", "form", "ticket", "classification", "human-in-the-loop"], "complex", None),
    IMPORT: ("CSV import dialog with a dry-run check that reports valid, invalid and duplicate rows before anything is saved, plus download links for the ticket, execution and comparison CSV exports.", ["component", "csv-import", "csv-export", "dialog", "validation"], "moderate", None),
    NEW: ("Page that loads the taxonomy, renders the ticket form and, once the API confirms creation, shows a success state with a link to the new ticket. No AI runs on creation.", ["component", "page", "ticket", "form"], "moderate", None),
    T_DETAIL: ("Ticket detail page composing ticket info, status select, edit form, final classification, AI results, internal notes and confirmed deletion. Status changes and edits appear only after the API confirms them.", ["component", "page", "ticket", "crud", "composition"], "complex", None),
    T_FORM: ("Shared create and edit form for tickets, validated client-side with a Zod schema that mirrors the backend's schema. Blank optional fields are sent as null, and the description is kept untrimmed.", ["component", "form", "validation", "ticket", "accessibility"], "moderate", "Uses react-hook-form with a Zod resolver; the Radix-based select is wired in through Controller because it is not a native input."),
    T_LIST: ("Ticket list page with search, taxonomy filters, sort and pagination kept in the URL, plus import and export actions. Rows navigate to the ticket and show its final classification and latest AI run.", ["component", "page", "ticket", "filtering", "pagination"], "complex", None),
    T_HOOKS: ("React Query hooks for ticket reads and writes, per-ticket AI runs and CSV import. Writes update the cache only after the API confirms them, and paid provider runs are never retried automatically.", ["hook", "data-fetching", "mutation", "ticket", "cache"], "moderate", None),
    FORMAT: ("Display formatters for dates, durations, escalation, tokens and estimated costs, plus the labels that show the gpt provider as 'LLM'. Missing values render as an em dash.", ["utility", "formatting", "display", "cost"], "simple", None),
    UTILS: ("One-line re-export of the cn class-name merging helper from the external cn package, used by UI components.", ["utility", "barrel", "styling"], "simple", None),
    API: ("The frontend's single HTTP client for the TicketLens backend, with a typed fetch wrapper, an ApiError class and readable messages from FastAPI errors. The browser never calls Jev or OpenAI directly.", ["service", "http-client", "error-handling", "api-client"], "simple", None),
    QUERIES: ("Shared React Query hooks for the taxonomy, cached indefinitely as fixed per backend version, and for provider configuration status, cached for one minute.", ["hook", "data-fetching", "taxonomy", "cache"], "simple", None),
    TYPES: ("TypeScript shapes for every TicketLens API response and request, including tickets, executions, comparisons, imports and dashboard metrics. Enum-like values stay plain strings because the allowed values come from the taxonomy endpoint.", ["type-definition", "api-contract", "data-model", "typescript"], "moderate", None),
}

# path -> name -> (summary, tags, complexity)
SYMBOLS = {
    COMPARE_RUN: {
        "useCompareRun": ("Starts both providers in parallel, tracks each run's state and timing, and creates the comparison only when both requests return an execution.", ["hook", "concurrency", "comparison"], "moderate"),
        "useElapsed": ("Returns milliseconds since a run started, ticking while it runs and frozen once it finishes.", ["hook", "timer", "ui-state"], "simple"),
        "formatElapsed": ("Formats milliseconds as an MM:SS.hh stopwatch string.", ["utility", "formatting", "timer"], "simple"),
    },
    CMP_DETAIL: {
        "ComparisonDetailPage": ("Loads one comparison and renders its ticket, both provider columns and the agreement verdict, with a not-found state on 404.", ["component", "page", "comparison"], "moderate"),
    },
    CMP_LIST: {
        "ComparisonTable": ("Table of comparisons showing ticket, agreement, each side's time and a fake-AI badge, linking to the comparison detail page.", ["component", "table", "comparison"], "simple"),
        "ComparisonsPage": ("Fetches up to 200 comparisons and renders loading, error, empty or table states.", ["component", "page", "comparison"], "simple"),
    },
    CMP_HOOKS: {
        "useComparisons": ("Queries saved comparisons by limit and optional ticket ID, refetching every 5 seconds.", ["hook", "data-fetching", "polling"], "simple"),
    },
    DASH: {
        "Stats": ("Grid of headline numbers: ticket counts, real comparisons, mean agreement, full matches and median times per side.", ["component", "metrics", "dashboard"], "simple"),
        "ChartCard": ("Card wrapper giving a chart a title, fixed height and responsive container.", ["component", "charts", "layout"], "simple"),
        "AgreementChart": ("Horizontal bar chart of agreement percentage per classification field, with counts in the tooltip.", ["component", "charts", "metrics"], "simple"),
        "SideBySideChart": ("Paired bar chart comparing how often Jev and the LLM chose each value of a field, ordered by severity where applicable.", ["component", "charts", "comparison"], "moderate"),
        "Reliability": ("Lists each side's success count, slowest run and estimated cost with the number of priced runs.", ["component", "metrics", "cost"], "simple"),
        "Recent": ("Shows the ten latest comparisons with a link to the full list, or nothing when there are none.", ["component", "comparison", "dashboard"], "simple"),
        "NoRealRuns": ("Empty state shown when no real runs exist, noting how many fake-AI comparisons were left out.", ["component", "empty-state", "dashboard"], "simple"),
        "DashboardPage": ("Polls dashboard data every 5 seconds and composes the stats, reliability line, charts and latest comparisons.", ["component", "page", "dashboard", "polling"], "moderate"),
    },
    EXEC_DETAIL: {
        "JsonBlock": ("Collapsible block showing a value as formatted JSON with a copy-to-clipboard button.", ["component", "debugging", "clipboard"], "simple"),
        "UsageAndCost": ("Card showing token usage, estimated cost and the rates saved with the run.", ["component", "cost", "execution-log"], "simple"),
        "Summary": ("Card with the run's status, models, timing, versions and links to its ticket and comparison.", ["component", "execution-log", "detail-view"], "simple"),
        "ExecutionDetailPage": ("Loads one execution and renders its summary, any error, usage, and validated and redacted payloads, with a not-found state on 404.", ["component", "page", "execution-log"], "moderate"),
    },
    EXEC_LIST: {
        "useLogParams": ("Reads log filters from the URL and updates them, resetting to page 1 when a filter changes.", ["hook", "url-state", "filtering"], "simple"),
        "DateFilter": ("Labelled date input used for the UTC from and to filters.", ["component", "filtering", "form"], "simple"),
        "Filters": ("Filter bar for side, status, ticket ID and UTC date range, with statuses taken from the taxonomy.", ["component", "filtering", "url-state"], "simple"),
        "LogTable": ("Table of runs with time, ticket, side, model, status, tokens, estimated cost and duration, linking to each run.", ["component", "table", "execution-log"], "simple"),
        "Body": ("Chooses between loading, error, empty, filtered-empty and table-with-pager states for the log.", ["component", "state-handling", "pagination"], "simple"),
        "ExecutionsPage": ("Wires URL filters to the log query and renders the filters, cost note, CSV download link and results.", ["component", "page", "execution-log"], "simple"),
    },
    AI: {
        "RunButton": ("Button that runs one provider on the ticket and toasts the outcome, disabled while the run is pending.", ["component", "provider-run", "mutation"], "simple"),
        "RunRow": ("One run's model, status, answer, error, timing, tokens and cost, with a 'Use this answer' button when it succeeded.", ["component", "provider-run", "history"], "simple"),
        "RunHistory": ("Lists the ticket's newest runs with loading, error and empty states and a link to the full log when there are more.", ["component", "history", "provider-run"], "simple"),
        "ComparisonHistory": ("Shows up to 50 comparisons for the ticket, or nothing when there are none.", ["component", "comparison", "history"], "simple"),
        "AiResults": ("Card combining the Jev and LLM run buttons, the link to Compare, run history and comparison history.", ["component", "ticket", "composition"], "simple"),
    },
    FINAL: {
        "startingValues": ("Builds the form's starting values from an AI or saved answer, or empty values when there is none.", ["utility", "form", "classification"], "simple"),
        "Field": ("Labelled select used for each classification field, disabled when it has no options.", ["component", "form", "accessibility"], "simple"),
        "FinalForm": ("Form editing the five classification fields; it requires all of them and saves the source run ID when an AI answer was used.", ["component", "form", "classification", "mutation"], "moderate"),
        "SavedFinal": ("Read-only view of the saved classification and whether it came from an AI answer, an edited one or by hand.", ["component", "classification", "detail-view"], "simple"),
        "FormLoader": ("Loads the taxonomy, with loading and error states, before rendering the final classification form.", ["component", "taxonomy", "state-handling"], "simple"),
        "FinalClassificationPanel": ("Card switching between the saved answer and the form, opening automatically when an AI answer is chosen and restarting the form for a different one.", ["component", "classification", "human-in-the-loop"], "simple"),
    },
    IMPORT: {
        "SummaryView": ("Renders an import summary: counts, duplicate rows, a per-row error table and a preview of the first rows.", ["component", "csv-import", "validation"], "simple"),
        "ImportDialog": ("Dialog that checks a chosen CSV with a dry run and enables the real import only after a successful check with rows to import.", ["component", "csv-import", "dialog", "mutation"], "moderate"),
        "ExportLinks": ("Download links for the tickets, executions and comparisons CSV exports.", ["component", "csv-export", "links"], "simple"),
    },
    NEW: {
        "NewTicketPage": ("Loads the taxonomy, submits the ticket form and shows a confirmation with next actions after creation.", ["component", "page", "ticket", "form"], "simple"),
    },
    T_DETAIL: {
        "StatusSelect": ("Select controlled by the saved status, so it changes only after the API confirms the update.", ["component", "ticket", "mutation"], "simple"),
        "TicketInfo": ("Card showing the ticket description with line breaks preserved, plus customer, order and channel details.", ["component", "ticket", "detail-view"], "simple"),
        "Notes": ("Lists internal operator notes and provides a form to add one.", ["component", "ticket", "form", "mutation"], "simple"),
        "TicketView": ("Composes the ticket's header actions, edit form or info, final classification, AI results, notes and delete confirmation, and passes a chosen AI answer to the final panel.", ["component", "ticket", "composition", "crud"], "moderate"),
        "TicketDetailPage": ("Loads the ticket named in the route and renders it, with loading, not-found and error states.", ["component", "page", "ticket"], "simple"),
    },
    T_FORM: {
        "Field": ("Form row with a label, a control and an inline error message linked by ID.", ["component", "form", "accessibility"], "simple"),
        "TicketForm": ("Validated create and edit form with accessible error wiring; converts blank optional fields to null on submit.", ["component", "form", "validation", "ticket"], "moderate"),
    },
    T_LIST: {
        "useListParams": ("Exposes the list's URL search parameters as a ticket query and updates them, resetting to page 1 when a filter changes.", ["hook", "url-state", "filtering"], "simple"),
        "Filters": ("Search box, taxonomy filters and sort select that write to the URL.", ["component", "filtering", "url-state"], "simple"),
        "TicketRow": ("Clickable table row showing a ticket's ID, customer, final classification, status, creation time and latest AI run.", ["component", "table", "ticket"], "simple"),
        "NoTickets": ("Empty state offering to clear filters when filtered, or to create or import tickets otherwise.", ["component", "empty-state", "ticket"], "simple"),
        "TicketTable": ("Ticket table with its column headers and one row per ticket.", ["component", "table", "ticket"], "simple"),
        "TicketListPage": ("Connects URL parameters to the ticket query and renders import and export actions, filters and the matching list state.", ["component", "page", "ticket"], "moderate"),
    },
    T_HOOKS: {
        "useTickets": ("Queries a page of tickets, keeping the previous page visible while the next loads.", ["hook", "data-fetching", "pagination"], "simple"),
        "useTicket": ("Queries one ticket by ID without retries.", ["hook", "data-fetching", "ticket"], "simple"),
        "useTicketWrite": ("Shared mutation wrapper that invalidates ticket lists and stores the returned ticket in the cache once the API confirms a write.", ["hook", "mutation", "cache"], "simple"),
        "useCreateTicket": ("Mutation that creates a ticket.", ["hook", "mutation", "ticket"], "simple"),
        "useUpdateTicket": ("Mutation that patches a ticket's fields or status.", ["hook", "mutation", "ticket"], "simple"),
        "useAddNote": ("Mutation that adds an internal note to a ticket.", ["hook", "mutation", "ticket"], "simple"),
        "useSetFinal": ("Mutation that saves a ticket's final classification.", ["hook", "mutation", "classification"], "simple"),
        "useTicketRuns": ("Queries up to 100 executions for one ticket.", ["hook", "data-fetching", "execution-log"], "simple"),
        "useRunProvider": ("Mutation that runs one provider on a ticket and refreshes execution and ticket-list caches when it settles; paid calls are never retried automatically.", ["hook", "mutation", "provider-run"], "simple"),
        "useDeleteTicket": ("Mutation that deletes a ticket.", ["hook", "mutation", "ticket"], "simple"),
        "useImportTickets": ("Mutation that uploads a CSV as a dry run or real import, refreshing ticket lists only after a real import.", ["hook", "mutation", "csv-import"], "simple"),
    },
    FORMAT: {
        "formatDateTime": ("Formats an ISO timestamp as a medium date and short time in the viewer's locale.", ["utility", "formatting", "date"], "simple"),
        "seconds": ("Formats milliseconds as seconds with two decimals, or an em dash when null.", ["utility", "formatting", "duration"], "simple"),
        "formatEscalation": ("Converts the escalation boolean to 'Required' or 'Not required'.", ["utility", "formatting", "classification"], "simple"),
        "formatTokens": ("Formats token usage as input / output, or an em dash when usage is unavailable.", ["utility", "formatting", "tokens"], "simple"),
        "formatCost": ("Formats an estimated USD cost, keeping more digits for amounts below one cent.", ["utility", "formatting", "cost"], "simple"),
    },
    API: {
        "ApiError": ("Error subclass carrying the HTTP status so callers can handle cases such as 404; status 0 means the backend was unreachable.", ["error-handling", "api-client", "http-client"], "simple"),
        "messageFrom": ("Extracts a readable message from an error body, including FastAPI validation errors as 'field: message' lists.", ["utility", "error-handling", "validation"], "simple"),
        "api": ("Typed fetch wrapper that adds the base URL and JSON content type, returns undefined on 204 and throws ApiError on failure.", ["http-client", "api-client", "error-handling"], "simple"),
        "send": ("Convenience wrapper over api that sends a method and JSON-encoded body.", ["http-client", "api-client", "utility"], "simple"),
    },
    QUERIES: {
        "useTaxonomy": ("Queries the canonical taxonomy and caches it indefinitely.", ["hook", "data-fetching", "taxonomy"], "simple"),
        "useProviderStatus": ("Queries whether each provider is configured, cached for one minute.", ["hook", "data-fetching", "provider-status"], "simple"),
    },
}

JS_EXPORT_ONLY = {UTILS}
nodes, edges = [], []


def node_id(path, name):
    return f"function:{path}:{name}"


def edge(source, target, kind, weight):
    edges.append({"source": source, "target": target, "type": kind, "direction": "forward", "weight": weight})


for path, (summary, tags, complexity, notes) in FILES.items():
    node = {"id": f"file:{path}", "type": "file", "name": path.rsplit("/", 1)[1], "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity}
    if notes:
        node["languageNotes"] = notes
    nodes.append(node)
    for target in imports[path]:
        edge(f"file:{path}", f"file:{target}", "imports", 0.7)

for path, symbols in SYMBOLS.items():
    result = results[path]
    fns = {f["name"]: f for f in result.get("functions", [])}
    classes = {c["name"]: c for c in result.get("classes", [])}
    exported = {e["name"] for e in result.get("exports", [])}
    for name, (summary, tags, complexity) in symbols.items():
        is_class = name in classes
        source = classes[name] if is_class else fns[name]
        prefix = "class" if is_class else "function"
        nid = f"{prefix}:{path}:{name}"
        nodes.append({"id": nid, "type": prefix, "name": name, "filePath": path,
                      "lineRange": [source["startLine"], source["endLine"]],
                      "summary": summary, "tags": tags, "complexity": complexity})
        edge(f"file:{path}", nid, "contains", 1.0)
        if name in exported:
            edge(f"file:{path}", nid, "exports", 0.8)

# Cross-file function calls: (caller file, caller, callee file, callee)
CALLS = [
    (COMPARE_RUN, "useCompareRun", API, "send"),
    (CMP_DETAIL, "ComparisonDetailPage", API, "api"),
    (CMP_DETAIL, "ComparisonDetailPage", FORMAT, "formatDateTime"),
    (CMP_LIST, "ComparisonTable", FORMAT, "formatDateTime"),
    (CMP_LIST, "ComparisonTable", FORMAT, "seconds"),
    (CMP_LIST, "ComparisonsPage", CMP_HOOKS, "useComparisons"),
    (CMP_HOOKS, "useComparisons", API, "api"),
    (DASH, "Stats", FORMAT, "seconds"),
    (DASH, "Reliability", FORMAT, "seconds"),
    (DASH, "Reliability", FORMAT, "formatCost"),
    (DASH, "Recent", CMP_HOOKS, "useComparisons"),
    (DASH, "DashboardPage", API, "api"),
    (EXEC_DETAIL, "UsageAndCost", FORMAT, "formatCost"),
    (EXEC_DETAIL, "Summary", FORMAT, "formatDateTime"),
    (EXEC_DETAIL, "Summary", FORMAT, "seconds"),
    (EXEC_DETAIL, "ExecutionDetailPage", API, "api"),
    (EXEC_LIST, "Filters", QUERIES, "useTaxonomy"),
    (EXEC_LIST, "LogTable", FORMAT, "formatDateTime"),
    (EXEC_LIST, "LogTable", FORMAT, "formatTokens"),
    (EXEC_LIST, "LogTable", FORMAT, "formatCost"),
    (EXEC_LIST, "LogTable", FORMAT, "seconds"),
    (AI, "RunButton", T_HOOKS, "useRunProvider"),
    (AI, "RunRow", FORMAT, "formatDateTime"),
    (AI, "RunRow", FORMAT, "formatEscalation"),
    (AI, "RunRow", FORMAT, "formatTokens"),
    (AI, "RunRow", FORMAT, "formatCost"),
    (AI, "RunRow", FORMAT, "seconds"),
    (AI, "RunHistory", T_HOOKS, "useTicketRuns"),
    (AI, "ComparisonHistory", CMP_HOOKS, "useComparisons"),
    (FINAL, "startingValues", FORMAT, "formatEscalation"),
    (FINAL, "FinalForm", T_HOOKS, "useSetFinal"),
    (FINAL, "FinalForm", FORMAT, "formatEscalation"),
    (FINAL, "FinalForm", FORMAT, "formatDateTime"),
    (FINAL, "SavedFinal", FORMAT, "formatEscalation"),
    (FINAL, "SavedFinal", FORMAT, "formatDateTime"),
    (FINAL, "FormLoader", QUERIES, "useTaxonomy"),
    (IMPORT, "ImportDialog", T_HOOKS, "useImportTickets"),
    (NEW, "NewTicketPage", QUERIES, "useTaxonomy"),
    (NEW, "NewTicketPage", T_HOOKS, "useCreateTicket"),
    (T_DETAIL, "StatusSelect", QUERIES, "useTaxonomy"),
    (T_DETAIL, "StatusSelect", T_HOOKS, "useUpdateTicket"),
    (T_DETAIL, "TicketInfo", FORMAT, "formatDateTime"),
    (T_DETAIL, "Notes", T_HOOKS, "useAddNote"),
    (T_DETAIL, "Notes", FORMAT, "formatDateTime"),
    (T_DETAIL, "TicketView", QUERIES, "useTaxonomy"),
    (T_DETAIL, "TicketView", T_HOOKS, "useUpdateTicket"),
    (T_DETAIL, "TicketView", T_HOOKS, "useDeleteTicket"),
    (T_DETAIL, "TicketDetailPage", T_HOOKS, "useTicket"),
    (T_LIST, "Filters", QUERIES, "useTaxonomy"),
    (T_LIST, "TicketRow", FORMAT, "formatDateTime"),
    (T_LIST, "TicketListPage", T_HOOKS, "useTickets"),
    (T_HOOKS, "useTickets", API, "api"),
    (T_HOOKS, "useTicket", API, "api"),
    (T_HOOKS, "useCreateTicket", API, "send"),
    (T_HOOKS, "useUpdateTicket", API, "send"),
    (T_HOOKS, "useAddNote", API, "send"),
    (T_HOOKS, "useSetFinal", API, "send"),
    (T_HOOKS, "useTicketRuns", API, "api"),
    (T_HOOKS, "useRunProvider", API, "send"),
    (T_HOOKS, "useDeleteTicket", API, "send"),
    (T_HOOKS, "useImportTickets", API, "api"),
    (QUERIES, "useTaxonomy", API, "api"),
    (QUERIES, "useProviderStatus", API, "api"),
]
for a, an, b, bn in CALLS:
    edge(node_id(a, an), node_id(b, bn), "calls", 0.8)

# Component renders another component in its JSX: parent contains child.
RENDERS = [
    (CMP_DETAIL, "ComparisonDetailPage", PROVIDER_COLUMN, "ProviderColumn"),
    (CMP_LIST, "ComparisonsPage", CMP_LIST, "ComparisonTable"),
    (DASH, "AgreementChart", DASH, "ChartCard"),
    (DASH, "SideBySideChart", DASH, "ChartCard"),
    (DASH, "Recent", CMP_LIST, "ComparisonTable"),
    (DASH, "DashboardPage", DASH, "NoRealRuns"),
    (DASH, "DashboardPage", DASH, "Stats"),
    (DASH, "DashboardPage", DASH, "Reliability"),
    (DASH, "DashboardPage", DASH, "AgreementChart"),
    (DASH, "DashboardPage", DASH, "SideBySideChart"),
    (DASH, "DashboardPage", DASH, "Recent"),
    (EXEC_DETAIL, "ExecutionDetailPage", EXEC_DETAIL, "Summary"),
    (EXEC_DETAIL, "ExecutionDetailPage", EXEC_DETAIL, "UsageAndCost"),
    (EXEC_DETAIL, "ExecutionDetailPage", EXEC_DETAIL, "JsonBlock"),
    (EXEC_LIST, "Filters", EXEC_LIST, "DateFilter"),
    (EXEC_LIST, "Filters", LIST_CONTROLS, "FilterSelect"),
    (EXEC_LIST, "Body", EXEC_LIST, "LogTable"),
    (EXEC_LIST, "Body", LIST_CONTROLS, "Pager"),
    (EXEC_LIST, "ExecutionsPage", EXEC_LIST, "Filters"),
    (EXEC_LIST, "ExecutionsPage", EXEC_LIST, "Body"),
    (AI, "RunHistory", AI, "RunRow"),
    (AI, "ComparisonHistory", CMP_LIST, "ComparisonTable"),
    (AI, "AiResults", AI, "RunButton"),
    (AI, "AiResults", AI, "RunHistory"),
    (AI, "AiResults", AI, "ComparisonHistory"),
    (FINAL, "FinalForm", FINAL, "Field"),
    (FINAL, "FormLoader", FINAL, "FinalForm"),
    (FINAL, "FinalClassificationPanel", FINAL, "FormLoader"),
    (FINAL, "FinalClassificationPanel", FINAL, "SavedFinal"),
    (IMPORT, "ImportDialog", IMPORT, "SummaryView"),
    (NEW, "NewTicketPage", T_FORM, "TicketForm"),
    (T_DETAIL, "TicketView", T_DETAIL, "StatusSelect"),
    (T_DETAIL, "TicketView", T_DETAIL, "TicketInfo"),
    (T_DETAIL, "TicketView", T_DETAIL, "Notes"),
    (T_DETAIL, "TicketView", T_FORM, "TicketForm"),
    (T_DETAIL, "TicketView", FINAL, "FinalClassificationPanel"),
    (T_DETAIL, "TicketView", AI, "AiResults"),
    (T_DETAIL, "TicketView", CONFIRM, "ConfirmDialog"),
    (T_DETAIL, "TicketDetailPage", T_DETAIL, "TicketView"),
    (T_FORM, "TicketForm", T_FORM, "Field"),
    (T_LIST, "Filters", LIST_CONTROLS, "FilterSelect"),
    (T_LIST, "TicketTable", T_LIST, "TicketRow"),
    (T_LIST, "TicketListPage", T_LIST, "Filters"),
    (T_LIST, "TicketListPage", T_LIST, "NoTickets"),
    (T_LIST, "TicketListPage", T_LIST, "TicketTable"),
    (T_LIST, "TicketListPage", LIST_CONTROLS, "Pager"),
    (T_LIST, "TicketListPage", IMPORT, "ImportDialog"),
    (T_LIST, "TicketListPage", IMPORT, "ExportLinks"),
]
for a, an, b, bn in RENDERS:
    edge(node_id(a, an), node_id(b, bn), "contains", 1.0)

# Consumer file depends on the file holding the custom hook it calls.
HOOK_USE = [
    (CMP_LIST, CMP_HOOKS), (DASH, CMP_HOOKS), (AI, CMP_HOOKS), (AI, T_HOOKS),
    (FINAL, T_HOOKS), (FINAL, QUERIES), (IMPORT, T_HOOKS), (NEW, T_HOOKS), (NEW, QUERIES),
    (T_DETAIL, T_HOOKS), (T_DETAIL, QUERIES), (T_LIST, T_HOOKS), (T_LIST, QUERIES),
    (EXEC_LIST, QUERIES),
]
for a, b in HOOK_USE:
    edge(f"file:{a}", f"file:{b}", "depends_on", 0.6)

# Checks before writing.
ids = [n["id"] for n in nodes]
assert len(ids) == len(set(ids)), "duplicate node ids"
assert set(FILES) == {f["path"] for f in batch["files"]}, "file set mismatch"
assert not [e for e in edges if e["source"] == e["target"]], "self edge"
keys = [(e["source"], e["target"], e["type"]) for e in edges]
assert len(keys) == len(set(keys)), "duplicate edges"
assert all(3 <= len(n["tags"]) <= 5 for n in nodes), "tag count"
import_edges = sum(e["type"] == "imports" for e in edges)
assert import_edges == sum(len(v) for v in imports.values()), "imports self-check"
for n in nodes:
    if n["type"] in ("function", "class"):
        start, end = n["lineRange"]
        name = n["name"]
        res = results[n["filePath"]]
        assert any(f["name"] == name for f in res.get("functions", []) + res.get("classes", []))

# Significance filter: every exported or 10+ line function/class must have a node.
missing = []
for path, res in results.items():
    exported = {e["name"] for e in res.get("exports", [])}
    for f in res.get("functions", []) + res.get("classes", []):
        lines = f["endLine"] - f["startLine"] + 1
        if (lines >= 10 or f["name"] in exported) and path not in JS_EXPORT_ONLY:
            prefix = "class" if f in res.get("classes", []) else "function"
            if f"{prefix}:{path}:{f['name']}" not in ids:
                missing.append((path, f["name"]))
assert not missing, missing

# Split per Steps B and C.
out_dir = f"{UA}/intermediate"
parts = 1
if len(nodes) > 60 or len(edges) > 120:
    parts = math.ceil(max(len(nodes) / 60, len(edges) / 120))
ordered = sorted(FILES)
chunk = math.ceil(len(ordered) / parts)
all_ids = set(ids)
neighbor_files, neighbor_symbols = set(), set()
for neighbors in neighbor_map.values():
    for neighbor in neighbors:
        neighbor_files.add(neighbor["path"])
        for symbol in neighbor["symbols"]:
            neighbor_symbols.add(f"function:{neighbor['path']}:{symbol}")
            neighbor_symbols.add(f"class:{neighbor['path']}:{symbol}")
import_files = set(imports) | {p for v in imports.values() for p in v}


def known(ref):
    # In-batch nodes in another part are allowed by Step C.
    if ref in all_ids or ref in neighbor_symbols:
        return True
    return ref.startswith("file:") and ref[5:] in (neighbor_files | import_files)


errors, written = [], []
for k in range(parts):
    files = set(ordered[k * chunk:(k + 1) * chunk])
    part_nodes = [n for n in nodes if n["filePath"] in files]
    part_ids = {n["id"] for n in part_nodes}
    part_edges = [e for e in edges if e["source"] in part_ids]
    for e in part_edges:
        if not known(e["target"]):
            errors.append(f"part {k + 1}: unknown target {e['target']}")
    name = f"batch-4.json" if parts == 1 else f"batch-4-part-{k + 1}.json"
    target = os.path.join(out_dir, name)
    with open(target, "w") as handle:
        json.dump({"nodes": part_nodes, "edges": part_edges}, handle, indent=1, ensure_ascii=False)
    json.load(open(target))
    written.append((name, len(part_nodes), len(part_edges)))

assert sum(w[1] for w in written) == len(nodes) and sum(w[2] for w in written) == len(edges)
from collections import Counter
print("written", written)
print("nodes", len(nodes), "edges", len(edges), Counter(e["type"] for e in edges))
print("imports", import_edges, "errors", errors)
