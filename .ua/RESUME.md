# Understand-Anything: knowledge graph (finished)

Finished 2026-11-08 and saved to `.ua/knowledge-graph.json`. There is nothing left to resume.

Plugin: understand-anything 2.9.8. Risk audit: `dependency_risk_audits/2026-11-08_understand-anything/`.

## Result

- 795 nodes, 1,910 links, 10 layers and a 16-step tour, built from 192 files.
- It was validated with 0 issues, and every scanned file has nodes. There are 9 harmless warnings: files with no links, such as empty `__init__.py` files.
- It records commit `0e90f74`, and the structural fingerprints in `fingerprints.json` cover all 192 files, so a later update only reads what changed.
- It was finished in two passes on 2026-11-08: the original 165 files, then an update that added the 28 new Phase 13 to 18 files and re-analyzed 37 files that had changed since the first scan.

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

- **Thin summaries:** about three of the nine refresh batches (the repository, service and settings files) wrote function summaries from names and structure instead of reading the source, so many read like "Repository function `X` querying MongoDB." The structure and links are right; only the wording is thin. Re-run `/understand-anything:understand --full` if you want richer summaries, which costs a full rebuild.
- **Edge cases:** the merge step dropped 3 links earlier in the update, which the second pass restored, and the tool's own change detection could not see the 37 stale files, so they were refreshed by hand.
- **Git:** `.ua/` is not in `.gitignore`. Two `.trash-*` folders of build scratch files are also in `.ua/` and safe to delete.
- **Updating later:** commit your changes first, since the update tool refuses to run on a dirty tree. Then run `/understand-anything:understand`.
