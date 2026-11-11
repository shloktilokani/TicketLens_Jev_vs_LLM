# .context/

The specification, status and data files for the project. Start with `PROGRESS.md`.

## Files

| File | Type | Purpose |
|---|---|---|
| `PROGRESS.md` | Status, kept current | Handover summary, phase checklist, every decision and test result, as dated notes |
| `ROADMAP.md` | Status, kept current | Phase status in plain words, and the steps that need the owner |
| `architecture.md` | Reference, as built | Layers, provider adapters, request flows, API routes, runtime limits |
| `data-model.md` | Reference, as built | MongoDB collections, fields, indexes, deletion order |
| `requirements.md` | Spec | Product requirements. Its "As built" section lists where the app differs |
| `design.md` | Spec | Pages and UX. Has an "As built" section |
| `ai-evaluation.md` | Spec | Classification contract, providers, accuracy, cost, retries. Has an "As built" section |
| `implementation.md` | Historical plan | The phase-by-phase build plan and acceptance criteria |
| `DEPLOYMENT_DECISIONS.md` | Reference and checklist | Production settings, safety checks, backups, and the decisions needed before hosting |
| `code-size-standards.md` | Rules | How the codebase stays small, with the evidence behind it |
| `sample_tickets_100_v2.csv` | Data | The 100 labelled synthetic tickets to use for accuracy |
| `sample_tickets_100.csv` | Data, reference only | The file as first supplied. Do not evaluate with it: its titles give away the answers |
| `sample_tickets_template.csv` | Data | The import header, also downloadable in the app |

## Rules

- **Where docs disagree,** an "As built" section or `PROGRESS.md` overrides the original spec text, and the code overrides all of them.
- **Update `PROGRESS.md`** after every piece of work, with the real test results.
- **Bare file names** in these documents refer to files in this folder.
