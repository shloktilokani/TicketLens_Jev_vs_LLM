import glob
import json
import math
import os

ROOT = "/Users/shloktilokani/Projects/TicketLens_Jev_vs_LLM/.ua"
source = json.load(open(f"{ROOT}/tmp/batch-input-5.json"))
extracted = json.load(open(f"{ROOT}/tmp/ua-file-extract-results-5.json"))
imports = source["batchImportData"]
neighbors = source["neighborMap"]

API = "backend/app/api"
T = "backend/tests"
MAIN = "backend/app/main.py"
SETTINGS = "backend/app/core/settings.py"
DB = "backend/app/repositories/database.py"
INIT = "backend/scripts/init_db.py"
CONFTEST = f"{T}/conftest.py"

FILES = {
    f"{API}/__init__.py": ("Empty package marker that makes the API routers importable as app.api.", ["barrel", "python-package", "api"], None),
    f"{API}/health.py": ("FastAPI router for process health and MongoDB readiness probes, returning 503 with a safe setup message when the database is unreachable.", ["api-handler", "health-check", "readiness", "mongodb"], None),
    f"{API}/providers.py": ("FastAPI router reporting whether the Jev and LLM sides can run and their display labels, without exposing API key values.", ["api-handler", "provider-status", "security", "configuration"], None),
    f"{API}/taxonomy.py": ("FastAPI router serving the canonical categories and enum values so the frontend reads the taxonomy rather than copying it.", ["api-handler", "taxonomy", "single-source-of-truth"], None),
    "backend/app/core/__init__.py": ("Empty package marker for the core settings, taxonomy, and pricing modules.", ["barrel", "python-package", "core"], None),
    SETTINGS: ("Typed backend settings and the only module that reads environment variables or backend/.env, covering MongoDB, provider backends, secrets, timeouts, and mock mode.", ["configuration", "settings", "secrets", "validation", "singleton"], "The extra='forbid' and env_ignore_empty options make misspelt variables fail at startup while treating empty values from a copied .env.example as unset."),
    MAIN: ("TicketLens API entry point whose application factory wires the MongoDB lifespan, CORS for the local frontend, all routers, and a 503 handler for database connection failures.", ["entry-point", "factory", "fastapi", "middleware", "error-handling"], "The lifespan closure captures the settings passed to create_app, so tests can build isolated apps with their own configuration."),
    DB: ("MongoDB access layer defining the client factory, readiness ping, index specifications, exact Decimal128 money codec, and shared read helpers.", ["database", "repository", "mongodb", "indexes", "serialization"], "A partial unique index on source_fingerprint enforces import idempotency without colliding on manually created tickets that have no fingerprint."),
    INIT: ("Repeatable command-line script that creates all TicketLens MongoDB indexes and exits non-zero with setup guidance when the database is unreachable.", ["script", "database", "indexes", "entry-point", "idempotent"], None),
    CONFTEST: ("Shared pytest fixtures providing settings isolated from backend/.env and a throwaway MongoDB test database that skips tests when MongoDB is down.", ["test", "fixtures", "pytest", "mongodb"], "pytest discovers conftest.py fixtures by parameter name, so test modules can use them without importing them."),
    f"{T}/test_app_starts.py": ("Smoke tests confirming the app imports and serves Swagger UI and an OpenAPI schema titled TicketLens API.", ["test", "smoke-test", "openapi", "fastapi"], None),
    f"{T}/test_dashboard.py": ("API tests for dashboard metrics, comparison listing and detail, and each ticket's latest run, including exclusion of fake runs from real metrics.", ["test", "dashboard", "comparisons", "api-test", "metrics"], None),
    f"{T}/test_health.py": ("Tests the health and readiness endpoints with MongoDB reachable and unreachable, and checks connection credentials never reach the response.", ["test", "health-check", "readiness", "security"], None),
    f"{T}/test_indexes.py": ("Tests that MongoDB index creation is correct and repeatable, that tickets without fingerprints do not collide, and that the init_db script reports success and failure.", ["test", "database", "indexes", "script"], None),
    f"{T}/test_runs_and_comparisons.py": ("API tests for provider runs, agreement-counting comparisons, partial and unavailable outcomes, final answer selection, and keeping the chosen answer out of model input.", ["test", "provider-runs", "comparisons", "evaluation-integrity", "api-test"], None),
    f"{T}/test_settings.py": ("Tests settings defaults, environment overrides, empty-value handling, secret masking, range validation, and that .env.example lists every setting.", ["test", "configuration", "settings", "secrets", "validation"], None),
    f"{T}/test_shell_support.py": ("Tests the CORS allow-list for the configured frontend origin and that provider status reports readiness without revealing API keys.", ["test", "cors", "provider-status", "security"], None),
    f"{T}/test_taxonomy.py": ("Tests that the canonical taxonomy matches the specification exactly, including enum values, valid category-subcategory pairs, and the taxonomy endpoint response.", ["test", "taxonomy", "validation", "specification"], None),
    f"{T}/test_tickets.py": ("End-to-end API tests for ticket creation, updates, notes, classification, search, filtering, sorting, pagination, dependent-safe deletion, and database outage responses.", ["test", "tickets", "api-test", "crud", "search"], None),
}

# (summary, extra tags, complexity); missing complexity means simple.
SYMBOLS = {
    f"{API}/health.py": {
        "health": ("Liveness endpoint that reports process status without touching the database.", ["api-handler", "health-check", "liveness"]),
        "ready": ("Readiness endpoint that pings MongoDB and returns 503 with a safe setup message when it is unreachable.", ["api-handler", "readiness", "mongodb"]),
    },
    f"{API}/providers.py": {
        "provider_status": ("Computes whether the Jev and LLM sides are configured from mock mode, local backends, or key presence, and returns their labels without key values.", ["api-handler", "provider-status", "security"]),
    },
    f"{API}/taxonomy.py": {
        "get_taxonomy": ("Returns the canonical taxonomy and enum values for the frontend.", ["api-handler", "taxonomy", "single-source-of-truth"]),
    },
    SETTINGS: {
        "Settings": ("Pydantic settings model for app, MongoDB, provider, timeout, and mock-mode values, rejecting unknown keys and holding API keys as optional SecretStr values.", ["configuration", "data-model", "validation", "secrets"], "moderate"),
        "get_settings": ("Returns a cached process-wide Settings instance.", ["configuration", "singleton", "cache"]),
        "is_local": ("Checks whether a URL's hostname refers to the local machine.", ["utility", "url", "validation"]),
    },
    MAIN: {
        "create_app": ("Builds the FastAPI app with a lifespan that connects MongoDB and ensures indexes, a restricted CORS policy, all routers, and a 503 handler for connection failures.", ["factory", "entry-point", "fastapi", "middleware"], "moderate"),
    },
    DB: {
        "DecimalCodec": ("BSON type codec converting Python Decimal to and from Decimal128 so stored money values stay exact.", ["serialization", "codec", "money", "mongodb"]),
        "connect": ("Creates a lazy, timezone-aware MongoClient with a short server-selection timeout and the Decimal codec, so the app can start while MongoDB is down.", ["database", "factory", "mongodb"]),
        "is_reachable": ("Pings MongoDB and returns whether the server responded.", ["database", "readiness", "mongodb"]),
        "ensure_indexes": ("Creates every declared collection index, and is safe to run repeatedly.", ["database", "indexes", "idempotent"]),
        "find_all": ("Reads every document in a collection, sorted ascending and without internal ids, for exports.", ["database", "query", "export"]),
        "find_in": ("Reads documents whose field matches any given value, without internal ids, for run reports.", ["database", "query", "reporting"]),
    },
    INIT: {
        "main": ("Ensures indexes in the configured database, prints the outcome, and returns exit code 1 with setup guidance when MongoDB is unreachable.", ["entry-point", "script", "indexes"]),
    },
    CONFTEST: {
        "test_settings": ("Fixture that builds Settings pointing at the test database and ignoring any developer backend/.env.", ["test", "fixture", "configuration"]),
        "test_db": ("Fixture yielding a test database emptied before and after each test, skipping the test when MongoDB is down.", ["test", "fixture", "mongodb"]),
    },
    f"{T}/test_app_starts.py": {
        "test_swagger_ui_is_served": ("Verifies the /docs page returns Swagger UI.", ["test", "smoke-test", "openapi"]),
        "test_openapi_schema_names_the_app": ("Verifies the OpenAPI schema is served with the TicketLens API title.", ["test", "smoke-test", "openapi"]),
    },
    f"{T}/test_dashboard.py": {
        "api": ("Fixture yielding a test client backed by zero-delay mock providers.", ["test", "fixture", "mock"]),
        "compared": ("Helper that creates a ticket, runs both fake providers, and returns their comparison.", ["test", "helper", "comparisons"]),
        "make_real": ("Helper that relabels a fake comparison's runs as if real models produced them.", ["test", "helper", "database"]),
        "test_dashboard_is_empty_before_any_runs": ("Verifies the dashboard reports zero counts and no metrics before any runs exist.", ["test", "dashboard", "empty-state"]),
        "test_dashboard_counts_real_runs_and_excludes_fake_ones": ("Verifies metrics count only real comparisons and report how many fake ones were excluded.", ["test", "dashboard", "metrics"], "moderate"),
        "test_comparison_list_is_newest_first_and_flags_fake_runs": ("Verifies comparisons are listed newest first, flagged as fake or real, and bounded by the limit parameter.", ["test", "comparisons", "pagination"], "moderate"),
        "test_comparison_detail_returns_both_stored_runs": ("Verifies comparison detail includes the ticket and both stored runs, and returns 404 for an unknown id.", ["test", "comparisons", "api-test"]),
        "test_ticket_list_shows_each_tickets_latest_run": ("Verifies the ticket list exposes the latest run status, or none for tickets without runs.", ["test", "tickets", "provider-runs"]),
        "test_comparisons_can_be_listed_for_one_ticket": ("Verifies the comparison list can be filtered to a single ticket.", ["test", "comparisons", "filtering"]),
    },
    f"{T}/test_health.py": {
        "test_health_reports_process_up": ("Verifies the health endpoint returns ok.", ["test", "health-check", "liveness"]),
        "test_ready_when_database_is_reachable": ("Verifies readiness returns ready when MongoDB responds.", ["test", "readiness", "mongodb"]),
        "test_not_ready_when_database_is_unreachable": ("Verifies health stays up while readiness returns 503 with setup guidance and no connection password.", ["test", "readiness", "security"], "moderate"),
    },
    f"{T}/test_indexes.py": {
        "keys_of": ("Helper that maps a collection's index key tuples to their index details.", ["test", "helper", "indexes"]),
        "test_indexes_are_created_and_safe_to_rerun": ("Verifies repeated index creation yields the expected unique, partial, and compound indexes.", ["test", "indexes", "idempotent"]),
        "test_tickets_without_fingerprint_do_not_collide": ("Verifies multiple tickets lacking a fingerprint can coexist under the partial unique index.", ["test", "indexes", "import-idempotency"]),
        "init_db_settings": ("Fixture that sets the MongoDB environment for the init script and clears the cached settings.", ["test", "fixture", "configuration"]),
        "test_init_db_script_is_repeatable": ("Verifies the init script succeeds on consecutive runs and names the database in its output.", ["test", "script", "idempotent"]),
        "test_init_db_script_explains_when_database_is_down": ("Verifies the init script exits 1 and points to the README when MongoDB is unreachable.", ["test", "script", "error-handling"]),
    },
    f"{T}/test_runs_and_comparisons.py": {
        "api": ("Fixture yielding a test client backed by zero-delay mock providers.", ["test", "fixture", "mock"]),
        "new_ticket": ("Helper that creates a ticket and returns its id.", ["test", "helper", "tickets"]),
        "run": ("Helper that runs a provider on a ticket, asserts success, and returns the execution.", ["test", "helper", "provider-runs"]),
        "compare": ("Helper that posts a comparison request for a Jev and a GPT execution.", ["test", "helper", "comparisons"]),
        "test_run_endpoint_records_and_returns_the_execution": ("Verifies a run returns a successful normalized execution and stores one record.", ["test", "provider-runs", "execution-log"]),
        "test_run_unknown_ticket_or_provider": ("Verifies an unknown ticket returns 404 and an unknown provider returns 422.", ["test", "provider-runs", "validation"]),
        "test_run_without_mock_or_key_is_recorded_as_not_configured": ("Verifies an OpenAI run without a key is stored as a failed execution with a not_configured error.", ["test", "provider-runs", "error-handling"]),
        "test_comparison_counts_agreement_and_links_both_runs": ("Verifies a completed comparison computes per-field agreement, names no winner, and links both executions.", ["test", "comparisons", "agreement"], "moderate"),
        "test_comparison_is_partial_when_one_provider_fails": ("Verifies one failed run gives a Partial comparison with no agreement rate while keeping the successful result.", ["test", "comparisons", "failure-isolation"], "moderate"),
        "test_comparison_is_unavailable_when_both_fail": ("Verifies the comparison status is Unavailable when both providers fail.", ["test", "comparisons", "error-handling"]),
        "test_comparison_rejects_mismatched_runs": ("Verifies comparisons reject runs from another ticket or the wrong provider, and unknown executions.", ["test", "comparisons", "validation"]),
        "test_comparison_waits_for_running_executions": ("Verifies comparing an execution that is still running returns 409.", ["test", "comparisons", "concurrency"]),
        "answer_of": ("Helper that extracts the five classification fields from an execution's normalized result.", ["test", "helper", "classification"]),
        "choose": ("Helper that submits a final classification, optionally naming the source execution.", ["test", "helper", "classification"]),
        "test_final_answer_taken_unchanged_from_a_run_is_not_marked_edited": ("Verifies an unchanged answer records its source run and is not marked manually edited.", ["test", "classification", "final-answer"]),
        "test_final_answer_changed_after_choosing_a_run_is_marked_edited": ("Verifies changing an answer selected from a run marks it manually edited while keeping the source.", ["test", "classification", "final-answer"]),
        "test_final_answer_rejects_a_run_it_cannot_come_from": ("Verifies missing, other-ticket, and failed source runs are rejected and no final answer is saved.", ["test", "classification", "validation"], "moderate"),
        "test_running_and_comparing_never_set_the_final_answer": ("Verifies provider runs and comparisons leave the final classification unset.", ["test", "classification", "evaluation-integrity"]),
        "test_the_chosen_final_answer_is_never_sent_to_a_model": ("Verifies later provider input and redacted request payloads contain no final-answer fields.", ["test", "evaluation-integrity", "provider-input"]),
    },
    f"{T}/test_settings.py": {
        "test_defaults_need_no_env_file_or_api_keys": ("Verifies settings load with local defaults and without any env file or API keys.", ["test", "settings", "defaults"]),
        "test_environment_overrides_defaults": ("Verifies environment variables override defaults with type conversion.", ["test", "settings", "environment"]),
        "test_empty_values_count_as_unset": ("Verifies empty environment values read as not configured.", ["test", "settings", "environment"]),
        "test_api_keys_never_appear_in_repr": ("Verifies API keys are masked in the settings repr yet remain retrievable as secrets.", ["test", "settings", "secrets"]),
        "test_out_of_range_values_are_rejected": ("Verifies out-of-range concurrency, threshold, and timeout values raise validation errors.", ["test", "settings", "validation"]),
        "test_env_example_lists_every_setting": ("Verifies .env.example variable names match the settings fields exactly.", ["test", "settings", "documentation"]),
    },
    f"{T}/test_shell_support.py": {
        "preflight": ("Helper that sends a CORS preflight request to the tickets endpoint from a given origin.", ["test", "helper", "cors"]),
        "test_cors_allows_only_the_configured_frontend_origin": ("Verifies CORS approves the configured frontend origin and no other.", ["test", "cors", "security"]),
        "test_provider_status_reports_configured_without_revealing_keys": ("Verifies provider status and labels reflect configuration while the key value stays out of the response.", ["test", "provider-status", "security"], "moderate"),
    },
    f"{T}/test_taxonomy.py": {
        "test_taxonomy_matches_the_spec_exactly": ("Verifies the taxonomy version, categories, and subcategories match the specification.", ["test", "taxonomy", "specification"]),
        "test_subcategory_names_are_unique_across_categories": ("Verifies all 36 subcategory names are unique across categories.", ["test", "taxonomy", "validation"]),
        "test_enums_hold_the_canonical_values": ("Parametrized check that each taxonomy enum holds its canonical values in order.", ["test", "taxonomy", "enums"]),
        "test_every_spec_pair_is_valid": ("Parametrized check that every specified category-subcategory pair is accepted.", ["test", "taxonomy", "validation"]),
        "test_inconsistent_or_unknown_pairs_are_invalid": ("Parametrized check that mismatched, unknown, or wrongly cased pairs are rejected.", ["test", "taxonomy", "validation"]),
        "test_taxonomy_endpoint_serves_the_same_values": ("Verifies the taxonomy endpoint returns the specified version, categories, and enum lists.", ["test", "taxonomy", "api-test"]),
    },
    f"{T}/test_tickets.py": {
        "api": ("Fixture yielding a test client backed by the test database.", ["test", "fixture", "tickets"]),
        "create": ("Helper that creates a ticket, asserts a 201 response, and returns its body.", ["test", "helper", "tickets"]),
        "classify": ("Helper that saves a final classification and asserts success.", ["test", "helper", "classification"]),
        "ids": ("Helper that extracts ticket ids from a list response.", ["test", "helper", "tickets"]),
        "test_create_assigns_sequential_ids_and_defaults": ("Verifies new tickets get sequential ids, default status, nested fields, and manual source.", ["test", "tickets", "creation"]),
        "test_ids_stay_unique_under_concurrent_creation": ("Verifies concurrent id allocation yields unique sequential ticket ids.", ["test", "tickets", "concurrency"]),
        "test_get_returns_ticket_or_404": ("Verifies fetching returns an existing ticket or 404.", ["test", "tickets", "api-test"]),
        "test_invalid_input_is_rejected": ("Verifies a malformed customer email is rejected with 422.", ["test", "tickets", "validation"]),
        "test_ticket_text_is_kept_exactly": ("Verifies a description keeps its line breaks and surrounding spaces exactly as typed.", ["test", "tickets", "data-integrity"]),
        "test_update_changes_only_given_fields": ("Verifies a partial update changes only supplied fields and advances updated_at.", ["test", "tickets", "update"]),
        "test_invalid_updates_are_rejected": ("Parametrized check that null titles, unknown statuses, bad emails, and empty updates return 422.", ["test", "tickets", "validation"]),
        "test_update_unknown_ticket_is_404": ("Verifies updating an unknown ticket returns 404.", ["test", "tickets", "error-handling"]),
        "test_notes_are_appended": ("Verifies notes append in order with distinct ids and that blank notes are rejected.", ["test", "tickets", "notes"]),
        "test_manual_classification_is_stored_with_version": ("Verifies a manual classification is stored as manually edited, with no source run and the taxonomy version.", ["test", "tickets", "classification"]),
        "test_inconsistent_classification_is_rejected": ("Verifies a mismatched category-subcategory pair returns 422 and leaves the final classification unset.", ["test", "tickets", "validation"]),
        "test_search_matches_each_searchable_field": ("Parametrized check that case-insensitive search finds a ticket by id, title, customer name, email, or order id.", ["test", "tickets", "search"]),
        "test_search_treats_input_as_plain_text": ("Verifies regex-like search input succeeds as plain text and matches nothing.", ["test", "tickets", "search"]),
        "test_filters_by_status_category_and_priority": ("Verifies list filters by status, category, and priority, and rejects an unknown priority.", ["test", "tickets", "filtering"], "moderate"),
        "test_sorts_by_created_date": ("Verifies tickets sort newest first by default and oldest first on request.", ["test", "tickets", "sorting"]),
        "test_sorts_by_priority_most_urgent_first_unclassified_last": ("Verifies priority sorting orders most urgent first and places unclassified tickets last.", ["test", "tickets", "sorting"], "moderate"),
        "test_pagination_is_bounded": ("Verifies pagination returns the right page and rejects out-of-range page parameters.", ["test", "tickets", "pagination"]),
        "seed_dependents": ("Helper that inserts a comparison, execution, and evaluation label for a ticket.", ["test", "helper", "database"]),
        "test_delete_removes_ticket_and_its_dependents_only": ("Verifies deletion removes one ticket and its dependents while another ticket's records remain.", ["test", "tickets", "deletion"], "moderate"),
        "test_repeated_delete_is_safe": ("Verifies deleting the same ticket twice returns 204 both times.", ["test", "tickets", "idempotent"]),
        "test_failed_dependent_delete_keeps_the_ticket": ("Verifies a simulated dependent-delete failure keeps the ticket and that a retry completes the deletion.", ["test", "tickets", "deletion", "failure-handling"], "moderate"),
        "test_ticket_endpoints_explain_when_database_is_down": ("Verifies ticket endpoints return 503 with README guidance when MongoDB is unreachable.", ["test", "tickets", "error-handling"]),
    },
}

NOTES_COMPLEXITY = {r["path"]: r["nonEmptyLines"] for r in extracted["results"]}


def file_complexity(lines: int) -> str:
    return "simple" if lines < 50 else "moderate" if lines <= 200 else "complex"


def edge(src, dst, kind, weight):
    return {"source": src, "target": dst, "type": kind, "direction": "forward", "weight": weight}


def fn(path, name):
    return f"function:{path}:{name}"


nodes, edges = [], []
for result in extracted["results"]:
    path = result["path"]
    summary, tags, notes = FILES[path]
    file_id = f"file:{path}"
    node = {
        "id": file_id, "type": "file", "name": os.path.basename(path), "filePath": path,
        "summary": summary, "tags": tags, "complexity": file_complexity(result["nonEmptyLines"]),
    }
    if notes:
        node["languageNotes"] = notes
    nodes.append(node)
    exported = {e["name"] for e in result.get("exports", [])}
    table = dict(SYMBOLS.get(path, {}))
    for kind, items in (("function", result.get("functions", [])), ("class", result.get("classes", []))):
        for item in items:
            entry = table.pop(item["name"])
            symbol_id = f"{kind}:{path}:{item['name']}"
            nodes.append({
                "id": symbol_id, "type": kind, "name": item["name"], "filePath": path,
                "lineRange": [item["startLine"], item["endLine"]], "summary": entry[0],
                "tags": entry[1], "complexity": entry[2] if len(entry) > 2 else "simple",
            })
            edges.append(edge(file_id, symbol_id, "contains", 1.0))
            if item["name"] in exported:
                edges.append(edge(file_id, symbol_id, "exports", 0.8))
    assert not table, f"unmatched symbols in {path}: {list(table)}"
    for target in imports[path]:
        edges.append(edge(file_id, f"file:{target}", "imports", 0.7))

CREATE_APP = fn(MAIN, "create_app")
REGISTRY = "backend/app/providers/registry.py"
TAXONOMY = "backend/app/core/taxonomy.py"
REPO_TICKETS = "backend/app/repositories/tickets.py"
CALLS = [
    (fn(f"{API}/health.py", "ready"), fn(DB, "is_reachable")),
    (fn(f"{API}/providers.py", "provider_status"), fn(SETTINGS, "is_local")),
    (fn(f"{API}/providers.py", "provider_status"), fn(REGISTRY, "provider_labels")),
    (fn(f"{API}/taxonomy.py", "get_taxonomy"), fn(TAXONOMY, "as_dict")),
    (CREATE_APP, fn(SETTINGS, "get_settings")),
    (CREATE_APP, fn(DB, "connect")),
    (CREATE_APP, fn(DB, "ensure_indexes")),
    (fn(INIT, "main"), fn(SETTINGS, "get_settings")),
    (fn(INIT, "main"), fn(DB, "connect")),
    (fn(INIT, "main"), fn(DB, "ensure_indexes")),
    (fn(f"{T}/test_dashboard.py", "api"), CREATE_APP),
    (fn(f"{T}/test_runs_and_comparisons.py", "api"), CREATE_APP),
    (fn(f"{T}/test_runs_and_comparisons.py", "test_run_without_mock_or_key_is_recorded_as_not_configured"), CREATE_APP),
    (fn(f"{T}/test_tickets.py", "api"), CREATE_APP),
    (fn(f"{T}/test_tickets.py", "test_ticket_endpoints_explain_when_database_is_down"), CREATE_APP),
    (fn(f"{T}/test_tickets.py", "test_ids_stay_unique_under_concurrent_creation"), fn(REPO_TICKETS, "next_ticket_id")),
    (fn(f"{T}/test_health.py", "test_health_reports_process_up"), CREATE_APP),
    (fn(f"{T}/test_health.py", "test_ready_when_database_is_reachable"), CREATE_APP),
    (fn(f"{T}/test_health.py", "test_not_ready_when_database_is_unreachable"), CREATE_APP),
    (fn(f"{T}/test_shell_support.py", "test_cors_allows_only_the_configured_frontend_origin"), CREATE_APP),
    (fn(f"{T}/test_shell_support.py", "test_provider_status_reports_configured_without_revealing_keys"), CREATE_APP),
    (fn(f"{T}/test_taxonomy.py", "test_taxonomy_endpoint_serves_the_same_values"), CREATE_APP),
    (fn(f"{T}/test_taxonomy.py", "test_every_spec_pair_is_valid"), fn(TAXONOMY, "is_valid_pair")),
    (fn(f"{T}/test_taxonomy.py", "test_inconsistent_or_unknown_pairs_are_invalid"), fn(TAXONOMY, "is_valid_pair")),
    (fn(f"{T}/test_indexes.py", "test_indexes_are_created_and_safe_to_rerun"), fn(DB, "ensure_indexes")),
    (fn(f"{T}/test_indexes.py", "test_tickets_without_fingerprint_do_not_collide"), fn(DB, "ensure_indexes")),
    (fn(f"{T}/test_indexes.py", "init_db_settings"), fn(SETTINGS, "get_settings")),
    (fn(f"{T}/test_indexes.py", "test_init_db_script_is_repeatable"), fn(INIT, "main")),
    (fn(f"{T}/test_indexes.py", "test_init_db_script_explains_when_database_is_down"), fn(INIT, "main")),
]
edges += [edge(src, dst, "calls", 0.8) for src, dst in CALLS]

# Fixtures are injected by name, and test_indexes imports the script as `from scripts import init_db`.
for path in ("test_dashboard.py", "test_runs_and_comparisons.py", "test_shell_support.py", "test_taxonomy.py"):
    edges.append(edge(f"file:{T}/{path}", f"file:{CONFTEST}", "depends_on", 0.6))
edges.append(edge(f"file:{T}/test_indexes.py", f"file:{INIT}", "depends_on", 0.6))

TESTED_BY = [
    (f"{API}/health.py", "test_health.py"),
    (f"{API}/providers.py", "test_shell_support.py"),
    (f"{API}/taxonomy.py", "test_taxonomy.py"),
    (TAXONOMY, "test_taxonomy.py"),
    (SETTINGS, "test_settings.py"),
    (MAIN, "test_app_starts.py"),
    (MAIN, "test_shell_support.py"),
    (DB, "test_indexes.py"),
    (INIT, "test_indexes.py"),
    (f"{API}/dashboard.py", "test_dashboard.py"),
    ("backend/app/services/dashboard.py", "test_dashboard.py"),
    (f"{API}/runs.py", "test_runs_and_comparisons.py"),
    (f"{API}/tickets.py", "test_tickets.py"),
    (REPO_TICKETS, "test_tickets.py"),
]
edges += [edge(f"file:{prod}", f"file:{T}/{test}", "tested_by", 0.5) for prod, test in TESTED_BY]

# Validation against the full batch: Step C allows targets in another part of the same batch.
ids = [n["id"] for n in nodes]
assert len(ids) == len(set(ids)), "duplicate node ids"
assert len({(e["source"], e["target"], e["type"]) for e in edges}) == len(edges), "duplicate edges"
known_files, known_symbols = set(), set()
for targets in imports.values():
    known_files |= {f"file:{t}" for t in targets}
for entries in neighbors.values():
    for neighbor in entries:
        known_files.add(f"file:{neighbor['path']}")
        for symbol in neighbor["symbols"]:
            known_symbols |= {f"function:{neighbor['path']}:{symbol}", f"class:{neighbor['path']}:{symbol}"}
valid = set(ids) | known_files | known_symbols
bad = [e for e in edges if e["source"] not in valid or e["target"] not in valid or e["source"] == e["target"]]
assert not bad, f"invalid edges: {bad}"
for n in nodes:
    assert n["summary"] and 3 <= len(n["tags"]) <= 5, n["id"]
expected = sum(len(v) for v in imports.values())
assert sum(e["type"] == "imports" for e in edges) == expected, "imports count mismatch"

for stale in glob.glob(f"{ROOT}/intermediate/batch-5.json") + glob.glob(f"{ROOT}/intermediate/batch-5-part-*.json"):
    os.remove(stale)

parts = max(1, math.ceil(max(len(nodes) / 60, len(edges) / 120)))
paths = sorted(f["path"] for f in source["files"])
size = math.ceil(len(paths) / parts)
chunks = [paths[i:i + size] for i in range(0, len(paths), size)]
node_part = {n["id"]: next(k for k, c in enumerate(chunks) if n["filePath"] in c) for n in nodes}


def part_of(e):
    if e["source"] in node_part:
        return node_part[e["source"]]
    return node_part[e["target"]]


written = []
for k, chunk in enumerate(chunks):
    fragment = {
        "nodes": [n for n in nodes if node_part[n["id"]] == k],
        "edges": [e for e in edges if part_of(e) == k],
    }
    name = "batch-5.json" if len(chunks) == 1 else f"batch-5-part-{k + 1}.json"
    target = f"{ROOT}/intermediate/{name}"
    with open(target, "w") as out:
        json.dump(fragment, out, indent=1)
    json.load(open(target))
    written.append((target, len(fragment["nodes"]), len(fragment["edges"])))

assert sum(w[1] for w in written) == len(nodes) and sum(w[2] for w in written) == len(edges)
print(f"nodes={len(nodes)} edges={len(edges)} imports={expected} parts={len(written)}")
for line in written:
    print(*line)
