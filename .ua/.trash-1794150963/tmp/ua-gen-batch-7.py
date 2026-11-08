import json,glob,os
os.chdir('.ua')
inv={}
for p in glob.glob('tmp/batch-input-*.json'):
    for f in json.load(open(p))['files']:
        inv[f['path']]=f['fileCategory']
def n(i,t,name,fp,s,tags,c,notes=None):
    d=dict(id=i,type=t,name=name,filePath=fp,summary=s,tags=tags,complexity=c)
    if notes: d['languageNotes']=notes
    return d
nodes=[
 n('config:.mcp.json','config','.mcp.json','.mcp.json',
   'Project-scoped MCP server configuration that launches version-pinned Playwright and Chrome DevTools servers against an isolated Chrome for Testing binary. It limits Playwright to the local frontend and backend origins and turns off DevTools usage statistics and CrUX lookups while redacting network headers.',
   ['configuration','mcp','browser-automation','ui-testing','security'],'simple'),
 n('document:AGENTS.md','document','AGENTS.md','AGENTS.md',
   'Operating instructions for autonomous coding agents, covering required spec reading order, autonomy expectations, technical guardrails, per-phase definition of done, developer-experience deliverables, and scope exclusions. Its guardrails fix key rules such as server-side secrets, a shared taxonomy, withholding ground-truth labels from models, and bounded retries.',
   ['documentation','agent-instructions','guardrails','development','scope'],'moderate'),
 n('document:CLAUDE.md','document','CLAUDE.md','CLAUDE.md',
   'Claude Code entry-point instructions that pull in AGENTS.md, point to the progress and build-order documents, and list the backend and frontend test, lint, and build commands. It also sets the rules for the engineering skills library, including routing, security, and which actions need owner approval.',
   ['documentation','agent-instructions','development','entry-point','skills-routing'],'simple',
   'The @AGENTS.md line is Claude Code memory-import syntax, which loads the referenced file as part of these instructions.'),
 n('document:README.md','document','README.md','README.md',
   'Project overview for the single-user ShopKart ticket classification demo comparing Jev with a configurable GPT model, including a documentation map, stack summary, and local-first scope boundary. Its run guide covers MongoDB, backend, and frontend startup, Ollama-based local models, mock providers, health checks, and test-run reports.',
   ['documentation','entry-point','overview','getting-started','local-development'],'moderate'),
]
def e(s,t,ty,w): return dict(source=s,target=t,type=ty,direction='forward',weight=w)
doc=lambda p:'document:'+p
ctx=lambda x:'.context/'+x+'.md'
edges=[e(doc('CLAUDE.md'),doc('AGENTS.md'),'depends_on',0.6),
       e(doc('CLAUDE.md'),doc('README.md'),'related',0.5),
       e(doc('AGENTS.md'),doc('README.md'),'depends_on',0.6),
       e(doc('README.md'),doc('AGENTS.md'),'related',0.5),
       e(doc('README.md'),doc('CLAUDE.md'),'related',0.5)]
for x in 'requirements architecture data-model ai-evaluation design implementation code-size-standards'.split():
    edges.append(e(doc('AGENTS.md'),doc(ctx(x)),'depends_on',0.6))
edges.append(e(doc('AGENTS.md'),doc(ctx('PROGRESS')),'related',0.5))
for x in 'PROGRESS implementation code-size-standards'.split():
    edges.append(e(doc('CLAUDE.md'),doc(ctx(x)),'related',0.5))
for x in 'code-size-standards ROADMAP implementation design architecture requirements data-model ai-evaluation PROGRESS'.split():
    edges.append(e(doc('README.md'),doc(ctx(x)),'related',0.5))
edges.append(e(doc('README.md'),doc('e2e/README.md'),'related',0.5))
edges.append(e('config:.mcp.json',doc('e2e/README.md'),'related',0.5))
for p in ['backend/app/main.py','backend/scripts/init_db.py','backend/scripts/run_report.py']:
    edges.append(e(doc('README.md'),'file:'+p,'documents',0.5))
# every cross-batch target must be a real scanned file of the matching category
for ed in edges:
    t=ed['target']; kind,path=t.split(':',1)
    assert path in inv,t
    assert (kind=='document' and inv[path]=='docs') or (kind=='file' and inv[path] in('code','script')),t
    assert ed['source']!=t
assert len({(x['source'],x['target'],x['type']) for x in edges})==len(edges)
assert len(nodes)<=60 and len(edges)<=120
json.dump({'nodes':nodes,'edges':edges},open('intermediate/batch-7.json','w'),indent=2)
d=json.load(open('intermediate/batch-7.json'))
ids={x['id'] for x in d['nodes']}
print(len(d['nodes']),len(d['edges']),'cross-batch',sum(x['target'] not in ids for x in d['edges']))
