import json,os
ex=json.load(open('.ua/tmp/ua-file-extract-results-24.json'))['results']
imp=json.load(open('.ua/tmp/ua-file-analyzer-input-24.json'))['batchImportData']
S={
'backend/app/repositories/executions.py':("MongoDB data-access layer for provider execution records: insert, update, lookup, bulk-run resume queries, cancellation of running attempts and filtered search.",["repository","mongodb","executions","data-access"]),
'backend/app/repositories/tickets.py':("MongoDB data-access layer for tickets: ID generation, insert/update, fingerprint duplicate checks, cascading delete, search and status counts.",["repository","mongodb","tickets","data-access"]),
'backend/app/schemas/bulk_jobs.py':("Pydantic schemas for bulk classification jobs: creation request, per-ticket outcomes, stored job and job list.",["schema","pydantic","bulk-jobs","validation"]),
'backend/app/schemas/classification.py':("Pydantic models for ticket classification results, manual final classification and the normalized provider result contract, validated against the shared taxonomy.",["schema","pydantic","classification","validation"]),
'backend/app/services/executions.py':("Runs a single provider attempt on a ticket, records success or failure as an execution log with cost fields and redacted payloads.",["service","executions","provider-adapter","cost-calculation"]),
'backend/app/services/tickets.py':("Ticket business logic: creation with fingerprint dedupe, updates, notes, and setting the final classification from a usable run.",["service","tickets","business-logic","validation"]),
'backend/tests/test_live_adapters.py':("Tests for the live Jev and Ollama provider adapters using mocked HTTP: two-step Jev flow, token counting, failure safety, structured JSON parsing and registry selection.",["test","provider-adapter","jev","ollama"]),
}
FS={
'failed':'Builds a failed execution record from a provider error.','attempt':'Performs one provider call and persists the resulting execution log.','cost_fields':'Computes token and cost fields for an execution.','run':'Runs the configured provider on a ticket and returns the saved execution.',
'create':'Creates a ticket with duplicate detection.','update':'Updates ticket fields.','add_note':'Appends a note to a ticket.','run_result':'Fetches a usable execution result for a ticket.','set_classification':'Sets the manual final classification from a run result.',
}
nodes=[];edges=[]
def cx(n): return 'simple' if n<50 else 'moderate' if n<=200 else 'complex'
for r in ex:
    p=r['path'];s,t=S[p]
    nodes.append(dict(id='file:'+p,type='file',name=os.path.basename(p),filePath=p,summary=s,tags=t,complexity=cx(r['nonEmptyLines'])))
    for q in imp[p]: edges.append(dict(source='file:'+p,target='file:'+q,type='imports',direction='forward',weight=0.7))
    test='tests/' in p
    for f in r.get('functions',[]):
        fid=f'function:{p}:{f["name"]}'
        sm=FS.get(f['name']) or (f'Test case: {f["name"].replace("test_","").replace("_"," ")}.' if test and f['name'].startswith('test_') else (f'Pytest fixture or helper `{f["name"]}` for adapter tests.' if test else f'Repository function `{f["name"]}` querying MongoDB.'))
        tg=['test'] if test else (['repository','mongodb'] if 'repositories' in p else ['service'])
        nodes.append(dict(id=fid,type='function',name=f['name'],filePath=p,lineRange=[f['startLine'],f['endLine']],summary=sm,tags=tg+['function'],complexity=cx(f['endLine']-f['startLine']+1)))
        edges+= [dict(source='file:'+p,target=fid,type='contains',direction='forward',weight=1.0),dict(source='file:'+p,target=fid,type='exports',direction='forward',weight=0.8)] if not test else [dict(source='file:'+p,target=fid,type='contains',direction='forward',weight=1.0)]
    for c in r.get('classes',[]):
        cid=f'class:{p}:{c["name"]}'
        nodes.append(dict(id=cid,type='class',name=c['name'],filePath=p,lineRange=[c['startLine'],c['endLine']],summary=f'Class {c["name"]} defined in {os.path.basename(p)}.',tags=['class','schema'] if 'schemas' in p else ['class','exception'],complexity='simple'))
        edges+=[dict(source='file:'+p,target=cid,type='contains',direction='forward',weight=1.0),dict(source='file:'+p,target=cid,type='exports',direction='forward',weight=0.8)]
for p in ['backend/app/services/executions.py','backend/app/services/tickets.py']: pass
edges.append(dict(source='file:backend/tests/test_live_adapters.py',target='file:backend/app/providers/jev.py',type='depends_on',direction='forward',weight=0.6))
edges.append(dict(source='file:backend/app/providers/jev.py',target='file:backend/tests/test_live_adapters.py',type='tested_by',direction='forward',weight=0.5))
edges=[e for e in edges if not(e['type']=='depends_on')]
json.dump(dict(nodes=nodes,edges=edges),open('.ua/intermediate/batch-24.json','w'),indent=1)
print(len(nodes),len(edges))
