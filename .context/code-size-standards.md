# Code size and reuse standards

Owner requirement (2026-11-07): keep the codebase clean and small **without losing functionality or
security**. Repeated logic goes into shared functions. The `ponytail` skill is applied to every
coding, development and database task.

This document is the technical analysis behind that requirement and the rules that follow from it.
All agents follow these rules; `AGENTS.md` lists this file in the read order.

## 1. Summary

- **Aim for less code to understand, not the fewest lines.** The evidence ties defects to
  copy-paste that drifts out of sync and to complex functions, more than to total size.
- **Share code once it repeats.** Extract a shared function when the same logic appears a third time,
  or a second time when it is security-critical, as with redaction, validation or cost maths.
- **Do not share too early.** A shared function that fits two cases badly costs more than a short duplicate.
- **Never trade away required behaviour:** validation, error handling, logging, tests, accessibility,
  and every item in `AGENTS.md` sections 3 and 4.

## 2. What the research says

| Finding | Source | What it means here |
|---|---|---|
| Inconsistent changes to cloned code are common, and about every second unintentional inconsistency was a fault. | Juergens et al., "Do Code Clones Matter?", ICSE 2009 ([arXiv](https://arxiv.org/pdf/1701.05472)) | Duplicated security or money logic must live in one place. |
| Up to 71% of studied clones had a positive or neutral effect on maintainability. The harmful patterns were mainly verbatim snippets and parameterised copies. | Kapser & Godfrey, Empirical Software Engineering 13(6), 2008 ([PDF](https://cormack.uwaterloo.ca/~migod/papers/2008/emse08-ClonePatterns.pdf)) | Not every repeat is bad. Remove copied blocks, not every similar line. |
| "Duplication is far cheaper than the wrong abstraction." Inline a wrong abstraction and re-extract it. | Metz, ["The Wrong Abstraction"](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction), 2016 | No generic layers in advance; extract when the shape is proven. |
| Refactor duplication on the third occurrence ("rule of three"). | Attributed to Don Roberts in Fowler, *Refactoring* ([summary](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming))) | The default trigger for extracting a shared function. |
| Presumptive features carry build, delay and carry costs. Unused code slows every later change. | Fowler, ["Yagni"](https://www.martinfowler.com/bliki/Yagni.html) | Build only what the spec needs now. |
| The size–defect link is real but not simple. Several studies find smaller modules proportionally more defect-prone, and results vary by system. | Koru et al., Empirical Software Engineering, 2009 ([DOI](https://doi.org/10.1007/s10664-008-9080-x)); summary by [Shape of Code](https://shape-of-code.com/2023/09/10/optimal-function-length-an-analysis-of-the-cited-data/) | Do not split code into many tiny pieces only to shorten files. |
| Cyclomatic complexity: McCabe suggested splitting a module above 10 ("a reasonable, but not magical, upper limit"). | McCabe, "A Complexity Measure", IEEE TSE 2(4), 1976 (secondary: [Wikipedia](https://www.wikiwand.com/en/Cyclomatic_complexity)) | Lint limit of 10 per function (section 5). |
| Cognitive Complexity correlates with longer comprehension time and lower understandability ratings. | Muñoz Barón, Wyrich & Wagner, ESEM 2020 ([arXiv](https://arxiv.org/abs/2007.12520)) | Prefer flat, readable code over clever one-liners. |
| AI-generated code contains clones: commercial generators had Type-1/2 clone rates up to 7.5%. A large repository study found the opposite on duplication ratios. Evidence is mixed. | [FSE 2025](https://dl.acm.org/doi/10.1145/3729397); [arXiv 2603.27130](https://arxiv.org/html/2603.27130v2) | Agents check for an existing helper before writing a new one. |
| No systematic maintainability gain or loss was detected when others later changed AI-assisted code. | Borg et al., "Echoes of AI", v3 ([arXiv](https://arxiv.org/abs/2507.00788v3)) | Maintainability depends on rules and review, not on who wrote the code. |
| Repository: "mediates between the domain and data mapping layers using a collection-like interface." | Fowler, [PoEAA catalog](https://www.martinfowler.com/eaaCatalog/repository.html) | The meaning of "repository" in this project (section 4). |

Notes on evidence quality:
- The McCabe threshold, the rule-of-three wording, and the clone fault rate are cited from secondary
  sources or abstracts. The original texts were not read in full.
- The GitClear industry data on rising copy-paste is a vendor report seen only second-hand, so it is
  not relied on.

## 3. Standards applied

- **ISO/IEC 25010 maintainability:** modularity, reusability, analysability, modifiability and
  testability. Every rule below supports one of these. The sub-characteristics were confirmed from
  secondary sources for the 2011 edition; that the 2023 edition keeps the same five is not verified.
- **DRY with the rule of three:** one authoritative place for each piece of knowledge, extracted when proven.
- **YAGNI and KISS:** no speculative options, layers or configuration.
- **Layered architecture from `architecture.md`:** routes, schemas, services, providers,
  repositories, core. Reuse happens inside these layers, never by merging them.
- **Repository pattern (Fowler):** data access goes behind repositories only.
- **Security first:** `codebase-security-auditor` and the security rules in `AGENTS.md` outrank size
  goals every time.

## 4. Where shared code lives

The owner asked for repeated logic to go into shared functions "called repository". In this
project's architecture, **repository** already means one thing: the MongoDB access layer. Using the
word for general helpers would blur two layers. So:

| Shared logic | Location | Examples |
|---|---|---|
| Database access | `backend/app/repositories/` | One small base helper for common queries, timestamps and pagination; one module per collection |
| Cross-cutting backend helpers | `backend/app/core/` | Settings, taxonomy, errors, redaction, money and cost maths, time helpers |
| Provider plumbing | `backend/app/providers/` | One shared HTTP call, timeout and retry helper (`providers/http.py`) used by the Jev and Ollama adapters and the Settings model list |
| Business workflows | `backend/app/services/` | Run one provider, run both, bulk jobs, imports |
| Frontend API access | `frontend/src/services/` | One API client; shared TanStack Query hooks |
| Frontend UI | `frontend/src/components/` | shadcn components plus shared loading, error, empty and confirm states |
| Shared types and enums | `frontend/src/types/` and `backend/app/core/` | One canonical taxonomy. Frontend values mirror the backend's and are checked by tests. |

## 5. Rules for every coding task

1. **Search before writing.** Look for an existing helper, component or pattern first, and reuse it.
2. **Extract on the third repeat**, or the second for security, money, redaction, validation or taxonomy logic.
3. **Keep functions simple.** Cyclomatic complexity of 10 or less (enforced by lint). Split by meaning, not by line count.
4. **No speculative code:** no unused options, generic base classes or "for later" layers.
5. **Prefer the platform and installed libraries.** Never add a dependency for a few lines.
   Any new dependency goes through `dependency-data-risk-audit`.
6. **Shrink tests with parametrised tests and shared fixtures,** never by dropping cases.
7. **Readable beats short.** A one-liner that needs decoding is not an improvement.
8. **Shortcuts are marked:** `# shortcut: <the limit>, <when to upgrade>`.

**Never cut:** input validation, error handling, redaction, execution logging, tests, accessibility,
loading/error/empty states, or anything in `AGENTS.md` sections 3 to 5.

## 6. How it is enforced

| Mechanism | What it checks |
|---|---|
| `ponytail` skill, always applied to coding tasks (see its tailoring block) | Smallest complete change; reuse first |
| Ruff `C90` (max complexity 10) and `SIM` rules in `backend/pyproject.toml` | Complex functions; needlessly long Python patterns |
| ESLint `complexity: 10` in `frontend/eslint.config.js` | Complex functions in TypeScript |
| Code review against section 5 before each phase is marked done | Duplication the linters cannot see |

A dedicated duplicate-code detector (for example `jscpd`) is not added yet. It is a new dependency
and would need an audit first. Revisit when the codebase is large enough for review to miss copies.

## 7. Precedence

When rules conflict: security and data integrity, then required spec behaviour and tests, then this
document, then `ponytail`'s smallest-change rule.
