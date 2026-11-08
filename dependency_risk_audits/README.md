# Dependency data-risk audits

One folder per audit: `index.html` (the report) and `meta.json`. Newest first.

- 2026-11-08: [Understand-Anything plugin](2026-11-08_understand-anything/index.html). 1 content-exposure risk (project files reach the AI model through the Claude Code session; secrets excluded by hand in `.ua/.understandignore`), 3 low or metadata-only, 1 no structural risk.
- 2026-11-07: [UI testing tools](2026-11-07_ui-testing-tools/index.html). 1 content-exposure risk (chrome-devtools-mcp usage statistics and CrUX, disabled in `.mcp.json`), 5 low or metadata-only.
