# Understand-Anything: knowledge graph (finished)

Finished 2026-11-08 and saved to `.ua/knowledge-graph.json`. There is nothing left to resume.

Plugin: understand-anything 2.9.8. Risk audit: `dependency_risk_audits/2026-11-08_understand-anything/`.

## Result

- 637 nodes, 1,776 edges, 10 layers and a 14-step tour, built from 165 files.
- It was validated with 0 issues. There are 10 harmless warnings: files with no links, such as empty `__init__.py` files.
- It records commit `dbdf828`.
- Structural fingerprints for all 165 files are in `fingerprints.json`, so a later update only reads what changed.

## What is in this folder

| File | Purpose |
|---|---|
| `knowledge-graph.json` | The graph |
| `meta.json`, `fingerprints.json` | Let incremental updates find what changed |
| `config.json`, `.understandignore` | Settings and exclusions (secrets and `.claude/skills/` are excluded) |
| `intermediate/scan-result.json` | The file inventory, kept for incremental updates |
| `.trash-*` | Scratch files from the build. Safe to delete; the next run also clears old ones |

## Using it

- **Open the dashboard:** run `/understand-anything:understand-dashboard`. It loads Google Fonts, so it sends your IP address to Google. Its server is fixed to port 5173, the same as the app's frontend, so stop the frontend first.
- **Ask questions** with `/understand-anything:understand-chat`, or explain one file with `/understand-anything:understand-explain`.
- **Update after code changes:** run `/understand-anything:understand` again. It should update only what changed, rather than rebuilding everything. Do not use `--full` unless you want a rebuild.

## Known gaps

- **Behind the code:** the scan ran before the Phase 13 to 18 files were fully settled and before commit `dbdf828`. These files are therefore missing from the graph:
  `backend/app/jobs/bulk.py`, `backend/app/api/bulk_jobs.py`, `backend/app/repositories/bulk_jobs.py`, `backend/app/services/evaluation.py`, `backend/app/services/app_settings.py`, `backend/app/api/app_settings.py`, `backend/app/api/evaluation.py`, `backend/app/schemas/app_settings.py`, `backend/app/repositories/app_settings.py`, `frontend/src/features/settings/`, `frontend/src/features/bulk/`, and the Phase 14 to 18 tests. An incremental update adds them.
- `backend/app/repositories/executions.py` changed just after the scan, so its node is slightly stale.
- **Git:** `.ua/` is not in `.gitignore`. Add `.ua/` there if you do not want it committed.
