import json
C='.context/'
def doc(name,summary,tags,cx,notes=None):
    p=C+name
    n={"id":"document:"+p,"type":"document","name":name,"filePath":p,"summary":summary,"tags":tags,"complexity":cx}
    if notes: n["languageNotes"]=notes
    return n
def tbl(name,summary,tags,cx,notes=None):
    p=C+name; stem=name.rsplit('.',1)[0]
    n={"id":f"table:{p}:{stem}","type":"table","name":name,"filePath":p,"summary":summary,"tags":tags,"complexity":cx}
    if notes: n["languageNotes"]=notes
    return n
nodes=[
 doc("DEPLOYMENT_DECISIONS.md","Lists the hosting, database, authentication, domain, backup and budget decisions the owner must make before any cloud deployment, plus non-negotiable constraints such as never deploying the no-auth demo publicly.",["documentation","deployment","security","decision-record"],"simple"),
 doc("PROGRESS.md","Living status log of the 19-phase build: phase checklist, blockers, spec gaps and assumptions, and dated notes per phase. It also records the required fix to the sample dataset before any paid evaluation.",["documentation","project-status","changelog","development"],"complex"),
 doc("ROADMAP.md","Plain-language table of all phases with where the owner's input is needed, followed by step-by-step owner plans for MongoDB, API keys, model and price choice, spend approval, dataset review and deployment decisions.",["documentation","roadmap","project-planning","owner-input"],"moderate"),
 doc("ai-evaluation.md","Specifies the shared classification contract and taxonomy, Jev and GPT adapter behaviour, fair comparison rules, the labelled dataset, execution logging, cost calculation, retries and privacy handling.",["documentation","ai-evaluation","taxonomy","cost-logging","provider-contract"],"moderate"),
 doc("architecture.md","Describes the local-first system: React UI, FastAPI backend and local MongoDB, the provider adapter boundary, canonical provider input, request flows for runs, bulk, import and deletion, and the deployment boundary.",["documentation","architecture","provider-adapters","request-flows","system-design"],"moderate"),
 doc("code-size-standards.md","Owner-mandated standards for keeping the codebase small without losing functionality or security: research basis, thresholds for sharing code, per-task rules, and enforcement through tools such as Ruff complexity checks.",["documentation","coding-standards","code-quality","development"],"moderate"),
 doc("data-model.md","Defines the `ticketlens` MongoDB collections (tickets, evaluation_labels, ai_executions, comparisons, bulk_jobs, app_settings, counters), their document shapes, required indexes and deletion behaviour.",["documentation","database","schema-definition","mongodb"],"complex"),
 doc("design.md","Frontend design specification for a Linear-inspired dashboard: application shell, routes, each page's layout and states, CSV import/export UX, theme tokens, accessibility rules and non-goals.",["documentation","frontend-design","ui-spec","accessibility"],"complex"),
 doc("implementation.md","Authoritative sequential build plan from Phase 0 repository setup to Phase 18 deployment readiness, with steps and acceptance criteria per phase and a final definition of done.",["documentation","implementation-plan","acceptance-criteria","project-planning"],"complex"),
 doc("requirements.md","Product and technical requirements for TicketLens, a single-user demo for fictional marketplace ShopKart: ticket lifecycle and fields, classification taxonomy, provider behaviour, comparison, CSV, dashboard, settings and non-functional needs.",["documentation","requirements","product-spec","taxonomy"],"moderate"),
 tbl("sample_tickets_100.csv","100 fictional labelled ShopKart tickets, balanced across six categories and four channels, with expected category, subcategory, priority, sentiment and escalation columns. Every title equals its expected_subcategory, so it leaks a label and PROGRESS.md bars it from evaluation until corrected.",["sample-data","evaluation-dataset","synthetic-data","csv-import","ground-truth"],"moderate","The file starts with a UTF-8 byte order mark, so readers need `utf-8-sig` to get a clean first column name."),
 tbl("sample_tickets_template.csv","Header-only CSV listing the 12 ticket import columns: seven ticket fields and five expected_* label fields. `test_csv.py` compares it to the importer's COLUMNS constant, which the template download endpoint uses to build its response.",["csv-import","template","schema-definition","data-format"],"simple"),
]
def d(*names): return ["document:"+(n if '/' in n or n in('README.md','AGENTS.md','CLAUDE.md') else C+n) for n in names]
E=[]
def add(s,t,ty,w): E.append({"source":s,"target":t,"type":ty,"direction":"forward","weight":w})
def documents(name,*paths):
    for p in paths: add("document:"+C+name,"file:"+p,"documents",0.5)
def related(name,*names):
    for t in d(*names): add("document:"+C+name,t,"related",0.5)
documents("PROGRESS.md","backend/app/main.py","backend/app/core/settings.py","backend/app/core/taxonomy.py","backend/app/core/pricing.py","backend/app/repositories/database.py","backend/app/repositories/tickets.py","backend/app/repositories/comparisons.py","backend/app/services/csv_import.py","backend/app/services/csv_export.py","backend/app/services/comparisons.py","backend/app/services/executions.py","backend/app/services/run_report.py","backend/app/providers/registry.py","backend/app/providers/jev.py","backend/app/providers/ollama.py","backend/app/providers/mock.py","frontend/src/app/AppShell.tsx","frontend/src/app/router.tsx","frontend/src/features/compare/ComparePage.tsx","frontend/src/features/tickets/TicketDetailPage.tsx")
related("PROGRESS.md","implementation.md","ROADMAP.md","README.md")
add("document:.context/PROGRESS.md","table:.context/sample_tickets_100.csv:sample_tickets_100","related",0.5)
related("ROADMAP.md","implementation.md","DEPLOYMENT_DECISIONS.md")
add("document:.context/ROADMAP.md","config:backend/.env.example","related",0.5)
documents("ai-evaluation.md","backend/app/core/taxonomy.py","backend/app/core/pricing.py","backend/app/schemas/classification.py","backend/app/schemas/executions.py","backend/app/providers/base.py","backend/app/providers/jev.py","backend/app/providers/definitions.py","backend/app/services/executions.py","backend/app/services/comparisons.py")
related("ai-evaluation.md","requirements.md")
add("document:.context/ai-evaluation.md","table:.context/sample_tickets_100.csv:sample_tickets_100","documents",0.5)
documents("architecture.md","backend/app/main.py","backend/app/providers/base.py","backend/app/providers/jev.py","backend/app/providers/definitions.py","backend/app/providers/ollama.py","backend/app/providers/registry.py","backend/app/services/csv_import.py")
related("architecture.md","data-model.md")
documents("code-size-standards.md")
related("code-size-standards.md","AGENTS.md","architecture.md")
add("document:.context/code-size-standards.md","config:backend/pyproject.toml","related",0.5)
documents("data-model.md","backend/app/repositories/database.py","backend/app/repositories/tickets.py","backend/app/repositories/executions.py","backend/app/repositories/comparisons.py","backend/app/repositories/labels.py","backend/app/schemas/tickets.py","backend/app/schemas/executions.py","backend/app/schemas/comparisons.py","backend/app/schemas/bulk_jobs.py")
documents("design.md","frontend/src/app/AppShell.tsx","frontend/src/app/router.tsx","frontend/src/index.css","frontend/src/features/tickets/TicketListPage.tsx","frontend/src/features/tickets/NewTicketPage.tsx","frontend/src/features/tickets/TicketDetailPage.tsx","frontend/src/features/tickets/ImportExport.tsx","frontend/src/features/dashboard/DashboardPage.tsx","frontend/src/features/comparisons/ComparisonDetailPage.tsx")
documents("implementation.md","backend/app/main.py","backend/scripts/init_db.py")
related("implementation.md","requirements.md","architecture.md","data-model.md","ai-evaluation.md","design.md","DEPLOYMENT_DECISIONS.md","AGENTS.md","CLAUDE.md","README.md")
for s in ("sample_tickets_100","sample_tickets_template"):
    add("document:.context/implementation.md",f"table:.context/{s}.csv:{s}","documents",0.5)
documents("requirements.md","backend/app/core/taxonomy.py","backend/app/schemas/tickets.py")
add("table:.context/sample_tickets_template.csv:sample_tickets_template","file:backend/app/services/csv_import.py","defines_schema",0.8)
add("table:.context/sample_tickets_template.csv:sample_tickets_template","file:backend/tests/test_csv.py","related",0.5)
add("table:.context/sample_tickets_100.csv:sample_tickets_100","file:backend/tests/test_csv.py","related",0.5)
add("table:.context/sample_tickets_100.csv:sample_tickets_100","table:.context/sample_tickets_template.csv:sample_tickets_template","related",0.5)
out={"nodes":nodes,"edges":E}
# validation
scan=json.load(open('.ua/intermediate/scan-result.json'))
cat={f['path']:f['fileCategory'] for f in scan['files']}
ids={n['id'] for n in nodes}
assert len(ids)==len(nodes)
batch={n['filePath'] for n in nodes}
keys=[(e['source'],e['target'],e['type']) for e in E]
assert len(keys)==len(set(keys)),[k for k in keys if keys.count(k)>1]
ext=0
for e in E:
    assert e['source']!=e['target']
    assert e['source'] in ids,e
    t=e['target']
    if t in ids: continue
    ext+=1
    pre,path=t.split(':',1)
    assert path in cat,t
    assert path not in batch,t
    assert {'file':'code','document':'docs','config':'config'}[pre]==cat[path] or (pre=='file' and cat[path] in('markup','script')),t
for n in nodes:
    assert n['summary'] and 3<=len(n['tags'])<=5,n['id']
json.dump(out,open('.ua/intermediate/batch-6.json','w'),indent=1)
print(len(nodes),len(E),'external',ext)
json.load(open('.ua/intermediate/batch-6.json'))
