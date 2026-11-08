# Understand-Anything: paused knowledge graph

Paused 2026-11-08 at the owner's request. Phases 0 to 5 of 7 are done and saved in `intermediate/`.
Plugin: understand-anything 2.9.8. Risk audit: `dependency_risk_audits/2026-11-08_understand-anything/`.

**Do not just re-run `/understand-anything:understand`.** With no `knowledge-graph.json` or `meta.json`
yet, it starts a full rebuild and re-analyses every file. Tell Claude: "resume the graph from `.ua/RESUME.md`".

**Status on 2026-11-08, end of day:** still paused, and the owner plans to continue on 2026-11-09. No agents are running. All outputs below were present when this was written. Project development is tracked separately in `.context/PROGRESS.md`.

## Done

| Phase | Result | File |
|---|---|---|
| 0.5 Ignore rules | Secrets and `.claude/skills/` excluded | `.understandignore` |
| 1 Scan | 165 files, 81 excluded | `intermediate/scan-result.json` |
| 1.5 Batches | 12 batches | `intermediate/batches.json` |
| 2 Analyze | All 12 batches | `intermediate/batch-*.json` |
| 3 Review | 637 nodes, 1,776 edges | `intermediate/assembled-graph.json`, `assemble-review.json` |
| 4 Layers | 10 layers, 165 of 165 files placed | `intermediate/layers.json` |
| 5 Tour | 14 steps | `intermediate/tour.json` |

## To finish (no AI analysis needed)

Plugin folder: `~/.claude/plugins/cache/understand-anything/understand-anything/2.9.8`. The scripts are in
its `skills/understand/`. Use `python3`, because this machine has no `python`. `pnpm` is in `~/.local/bin`.

1. **Phase 6:** merge `assembled-graph.json`, `layers.json` and `tour.json` into one graph with the
   `version`, `project`, `nodes`, `edges`, `layers` and `tour` fields, and run the inline validation from
   the skill's Phase 6.
2. **Phase 7:** write `knowledge-graph.json`, run `build-fingerprints.mjs` over every file in
   `scan-result.json`, write `meta.json` only after that succeeds, then clean up as the skill describes.
3. **Open it:** `/understand-anything:understand-dashboard`. It loads Google Fonts, so it sends your IP
   address to Google. Its port may clash with the app's frontend on 5173.
4. **Catch up:** run `/understand-anything:understand`, which should now update incrementally for what
   changed since the scan.

## Known gaps

- **Behind the code:** the scan predates Phases 13 to 18 (`backend/app/jobs/bulk.py`,
  `backend/app/services/evaluation.py`, `frontend/src/features/bulk/` and more). Step 4 above picks them up.
- **Stale node:** `backend/app/repositories/executions.py` changed just after the scan.
- **Commit reference:** the scan used files with uncommitted changes on top of commit `d6fb162`. Commit
  first if you want the graph's commit to match its contents.
- **Source Control:** `.ua/` is not in `.gitignore`. Add `.ua/` there if it should not be committed. The
  folder is about 3 MB.
- `tmp/` holds working files that are no longer needed once the graph is saved.
