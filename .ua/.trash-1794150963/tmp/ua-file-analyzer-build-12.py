import json
import os

ROOT = "/Users/shloktilokani/Projects/TicketLens_Jev_vs_LLM/.ua"
batch = json.load(open(f"{ROOT}/tmp/batch-input-12.json"))

# path: (type, summary, tags, complexity, languageNotes)
F = {
    ".claude/settings.json": ("config", "Project Claude Code settings that allow read-only git and test commands, deny secret-file reads, docker and every git write, and add a prompt hook enforcing skill routing.", ["configuration", "security", "agent-tooling", "permissions", "hooks"], "moderate", None),
    ".gitattributes": ("file", "Git attributes that normalize text to LF, keep CSV spec data byte-for-byte (BOM and CRLF preserved), and mark images and fonts as binary.", ["configuration", "git", "line-endings", "build-system"], "simple", None),
    "backend/app/__init__.py": ("file", "Empty marker that makes the backend `app` directory a Python package.", ["python-package", "package-marker", "backend"], "simple", None),
    "backend/app/jobs/__init__.py": ("file", "Empty marker that makes the backend `app.jobs` directory a Python package.", ["python-package", "package-marker", "jobs"], "simple", None),
    "backend/app/schemas/__init__.py": ("file", "Empty marker that makes the backend `app.schemas` directory a Python package.", ["python-package", "package-marker", "schemas"], "simple", None),
    "backend/tests/__init__.py": ("file", "Empty marker that makes the backend test directory a Python package.", ["python-package", "package-marker", "test"], "simple", None),
    "e2e/README.md": ("document", "Guide to UI testing through the real interface, covering the isolated test stack, what each browser tool is for, commands, how to write test cases and personas, the unbuilt real-provider mode, and tool data-risk settings.", ["documentation", "testing", "e2e", "playwright", "development"], "simple", None),
    "e2e/package.json": ("config", "Standalone npm package for UI testing that pins `@playwright/test` and `agent-browser` and defines scripts for the test stack, tests, baseline updates, reports, and a visible Chrome for Testing browser.", ["configuration", "testing", "e2e", "npm-scripts", "build-system"], "simple", None),
    "e2e/personas/README.md": ("document", "Explains how a persona run pairs a customer voice (how the ticket is written) with an analyst (how the app is used), and sets rules for synthetic data, taxonomy limits, and never typing expected labels.", ["documentation", "testing", "personas", "synthetic-data"], "simple", None),
    "e2e/playwright.config.ts": ("file", "Playwright configuration that runs tests serially against the isolated stack on port 5174, on desktop and Pixel 7 Chromium projects, with a 1% screenshot diff tolerance and traces kept on failure.", ["config", "testing", "e2e", "playwright", "visual-regression"], "simple", "`workers: 1` is deliberate because every test shares one database, and `reuseExistingServer: false` guarantees a freshly reset stack per run."),
    "e2e/scripts/reset_db.py": ("file", "Safety-guarded script that drops the UI-test MongoDB database so each stack start is clean, refusing any database name not ending in `_e2e`.", ["script", "testing", "database", "safety-guard", "e2e"], "simple", None),
    "e2e/scripts/stack.sh": ("file", "Starts the isolated UI-test stack: resets `ticketlens_e2e`, launches the backend with mock providers on port 8001, waits for the database readiness check, then starts Vite on port 5174, and refuses real-provider mode.", ["script", "testing", "e2e", "process-management", "entry-point"], "moderate", "The servers `exec` inside subshells and run without a reloader, so the EXIT trap's `kill` really stops them rather than leaving child processes behind."),
    "e2e/test-cases/TC-001-create-ticket.md": ("document", "Test case for creating a duplicate-charge ticket and finding it again by search, with expected labels, field-validation outcomes, and visual checkpoints for desktop and mobile.", ["documentation", "testing", "test-case", "tickets"], "simple", None),
    "e2e/test-cases/TEMPLATE.md": ("document", "Copyable template for persona test cases, with sections for mode, personas, preconditions, ticket intent, expected labels, steps, expected results, and visual checkpoints.", ["documentation", "testing", "template", "test-case"], "simple", None),
    "e2e/tests/smoke.spec.ts": ("file", "End-to-end smoke test that creates a ticket through the form, finds it in the list and on its detail page, and checks pixel baselines with changing rows and totals masked.", ["test", "e2e", "playwright", "visual-regression", "tickets"], "simple", None),
    "frontend/.prettierignore": ("file", "Prettier ignore list that excludes build output, dependencies, the lockfile, and generated shadcn components so their updates diff cleanly.", ["configuration", "formatting", "frontend", "shadcn"], "simple", None),
    "frontend/eslint.config.js": ("file", "ESLint flat config for TypeScript and React that combines the recommended rule sets with Prettier, enforces a maximum complexity of 10, and relaxes the fast-refresh export rule for shadcn files.", ["config", "linting", "code-quality", "frontend", "build-system"], "simple", None),
    "frontend/src/components/ui/sonner.tsx": ("file", "shadcn wrapper around the Sonner toaster that follows the active theme, sets the status icons, and maps toast colors and radius to the app's design tokens.", ["component", "ui", "notifications", "theming", "shadcn"], "simple", None),
    "frontend/src/features/settings/.gitkeep": ("file", "Empty placeholder that keeps the settings feature directory in git.", ["placeholder", "git", "frontend"], "simple", None),
    "frontend/src/index.css": ("file", "Global stylesheet that imports Tailwind and shadcn styles, defines the light and dark theme tokens, maps them into the Tailwind theme, and sets base element styles.", ["styles", "theming", "design-tokens", "tailwind", "frontend"], "moderate", "Tailwind v4 is configured in CSS: `@theme inline` exposes the `:root` and `.dark` custom properties as utilities, and `@custom-variant dark` ties dark mode to the `.dark` class."),
    "frontend/src/main.tsx": ("file", "React entry point that mounts the app under StrictMode with the theme provider (light by default, remembered per browser), TanStack Query client, router, and global toaster.", ["entry-point", "bootstrap", "providers", "react", "frontend"], "simple", None),
    "frontend/src/services/.gitkeep": ("file", "Empty placeholder that keeps the frontend services directory in git.", ["placeholder", "git", "frontend"], "simple", None),
    "frontend/src/types/.gitkeep": ("file", "Empty placeholder that keeps the frontend types directory in git.", ["placeholder", "git", "frontend"], "simple", None),
    "frontend/vite.config.ts": ("file", "Vite configuration with the React and Tailwind plugins, the `@` alias for `src`, and a dev server fixed to localhost:5173 because the backend allows exactly that CORS origin.", ["config", "build-system", "vite", "frontend", "dev-server"], "simple", None),
}

assert set(F) == {f["path"] for f in batch["files"]}


def nid(path):
    return f"{F[path][0]}:{path}"


nodes = []
for f in batch["files"]:
    path = f["path"]
    kind, summary, tags, complexity, notes = F[path]
    node = {"id": nid(path), "type": kind, "name": os.path.basename(path), "filePath": path,
            "summary": summary, "tags": tags, "complexity": complexity}
    if notes:
        node["languageNotes"] = notes
    nodes.append(node)

SONNER = "frontend/src/components/ui/sonner.tsx"
TOASTER = f"function:{SONNER}:Toaster"
nodes.append({"id": TOASTER, "type": "function", "name": "Toaster", "filePath": SONNER, "lineRange": [5, 45],
              "summary": "Renders the Sonner toaster with the current theme, custom status icons, and design-token colors, passing other props through.",
              "tags": ["component", "notifications", "theming"], "complexity": "simple"})

WEIGHT = {"contains": 1.0, "imports": 0.7, "exports": 0.8, "depends_on": 0.6, "configures": 0.6, "documents": 0.5, "related": 0.5}
edges = []


def edge(source, target, kind):
    edges.append({"source": source, "target": target, "type": kind, "direction": "forward", "weight": WEIGHT[kind]})


for path, targets in batch["batchImportData"].items():
    for target in targets:
        edge(f"file:{path}", f"file:{target}", "imports")

edge(f"file:{SONNER}", TOASTER, "contains")
edge(f"file:{SONNER}", TOASTER, "exports")
edge(f"file:{SONNER}", "file:frontend/src/index.css", "depends_on")

STACK, RESET, PW, SMOKE = "e2e/scripts/stack.sh", "e2e/scripts/reset_db.py", "e2e/playwright.config.ts", "e2e/tests/smoke.spec.ts"
PKG, README, PERSONAS = "e2e/package.json", "e2e/README.md", "e2e/personas/README.md"
TC, TEMPLATE = "e2e/test-cases/TC-001-create-ticket.md", "e2e/test-cases/TEMPLATE.md"
MAIN, VITE = "frontend/src/main.tsx", "frontend/vite.config.ts"

for source, target, kind in [
    (STACK, RESET, "depends_on"),
    (STACK, VITE, "depends_on"),
    (PW, STACK, "depends_on"),
    (PW, SMOKE, "configures"),
    (PKG, PW, "configures"),
    (PKG, STACK, "depends_on"),
    (README, STACK, "documents"),
    (README, RESET, "documents"),
    (README, PKG, "documents"),
    (README, TEMPLATE, "documents"),
    (README, PERSONAS, "documents"),
    (TC, TEMPLATE, "related"),
    (TC, SMOKE, "related"),
    (PERSONAS, TEMPLATE, "related"),
    (VITE, MAIN, "configures"),
    ("frontend/eslint.config.js", MAIN, "configures"),
    ("frontend/eslint.config.js", SONNER, "configures"),
    ("frontend/.prettierignore", SONNER, "configures"),
    (".gitattributes", STACK, "configures"),
]:
    edge(nid(source), nid(target), kind)

# Step E self-validation, and the import-count self-check.
ids = {n["id"] for n in nodes}
allowed = set(ids)
for targets in batch["batchImportData"].values():
    allowed |= {f"file:{t}" for t in targets}
for neighbors in batch["neighborMap"].values():
    for n in neighbors:
        allowed.add(f"file:{n['path']}")
assert len(ids) == len(nodes), "duplicate node id"
bad = [e for e in edges if e["source"] not in allowed or e["target"] not in allowed or e["source"] == e["target"]]
assert not bad, bad
assert len({(e["source"], e["target"], e["type"]) for e in edges}) == len(edges), "duplicate edge"
expected = sum(len(v) for v in batch["batchImportData"].values())
assert sum(e["type"] == "imports" for e in edges) == expected
assert all(3 <= len(n["tags"]) <= 5 and n["summary"] for n in nodes)
assert len(nodes) <= 60 and len(edges) <= 120

out = f"{ROOT}/intermediate/batch-12.json"
json.dump({"nodes": nodes, "edges": edges}, open(out, "w"), indent=2)
check = json.load(open(out))
print(out, len(check["nodes"]), "nodes", len(check["edges"]), "edges", expected, "imports")
