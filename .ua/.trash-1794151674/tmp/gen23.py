import json
D=json.load(open('.ua/tmp/batch-input-23.json'))
imp=D['batchImportData']
S={
"backend/app/api/tickets.py":("FastAPI router for ticket CRUD, notes, final-classification selection, and cascading delete, backed by the ticket and execution repositories.",["api-handler","tickets","crud","router"],"moderate"),
"backend/app/core/taxonomy.py":("Canonical ShopKart taxonomy: enums for category, priority, sentiment, status, channel, provider and job states, plus an active-version category map with validation helpers.",["taxonomy","enums","validation","domain-model"],"moderate"),
"backend/app/providers/base.py":("Provider adapter contract: input builder, normalized ProviderResult, safe ProviderFailure with HTTP-status mapping, and the Adapter protocol.",["provider","contract","error-handling","type-definition"],"moderate"),
"backend/app/providers/definitions.py":("Provider-facing instruction text and helpers that render category and subcategory criteria from the taxonomy.",["provider","prompt","taxonomy","utility"],"simple"),
"backend/app/providers/http.py":("Shared JSON HTTP client helpers with bounded retries and backoff for transient failures, raising safe ProviderFailure errors.",["http","retry","provider","utility"],"moderate"),
"backend/app/providers/jev.py":("Jev adapter that builds typed-decision requests for category and subcategory choices, parses outputs, sums usage, and returns a normalized classification.",["provider","jev","adapter","classification"],"moderate"),
"backend/app/providers/ollama.py":("Ollama LLM adapter that sends a schema-constrained chat request and normalizes the structured JSON reply into a classification result.",["provider","llm","ollama","adapter"],"moderate"),
"backend/app/providers/registry.py":("Resolves configured Jev, LLM and mock adapters from settings, reporting provider labels, readiness and requested model.",["registry","provider","factory","configuration"],"moderate"),
}
FN={
"backend/app/api/tickets.py":[("found",18,21,"Returns a ticket or raises 404."),("create_ticket",25,27,"Creates a ticket."),("list_tickets",31,60,"Lists tickets with filters and pagination."),("get_ticket",64,65,"Fetches one ticket."),("update_ticket",69,70,"Updates ticket fields."),("add_note",74,75,"Adds a note to a ticket."),("set_final_classification",79,84,"Stores the manually selected final classification."),("delete_ticket",88,98,"Deletes a ticket with its dependents.")],
"backend/app/core/taxonomy.py":[("set_active",137,138,"Sets the active taxonomy version and categories."),("reset",141,142,"Resets the taxonomy to defaults."),("active_version",145,146,"Returns the active taxonomy version."),("active_categories",149,150,"Returns active category-to-subcategory map."),("is_valid_pair",153,155,"Checks a category/subcategory pair is valid."),("as_dict",158,169,"Serializes the taxonomy for the API.")],
"backend/app/providers/base.py":[("build_input",49,65,"Builds the ProviderInput from a ticket, excluding ground truth."),("failure_for_status",118,135,"Maps an HTTP status to a safe ProviderFailure.")],
"backend/app/providers/definitions.py":[("category_criteria",27,28,"Renders category criteria text."),("subcategory_criteria",31,32,"Renders subcategory criteria text.")],
"backend/app/providers/http.py":[("get_json",23,32,"GET request returning parsed JSON."),("post_json",35,45,"POST request returning parsed JSON."),("pause",48,49,"Sleeps between retries."),("retry_wait",52,59,"Computes bounded backoff delay."),("send_once",62,82,"Sends one request and maps errors."),("send_with_retries",85,113,"Retries only transient failures with bounded attempts."),("request_json",116,147,"Public entry for JSON requests with retries.")],
"backend/app/providers/jev.py":[("choice",35,36,"Builds a choice option."),("build_request",39,54,"Builds the category decision request."),("build_subcategory_request",57,68,"Builds the subcategory decision request."),("parse_output",71,86,"Validates and parses Jev output."),("total_usage",89,101,"Sums usage across steps.")],
"backend/app/providers/ollama.py":[("schema",17,39,"JSON schema constraining the reply."),("system_prompt",42,53,"Builds the system prompt."),("build_request",56,77,"Builds the Ollama chat request.")],
"backend/app/providers/registry.py":[("provider_labels",17,26,"Returns display labels for providers."),("provider_ready",29,35,"Reports whether a provider is configured."),("requested_model",38,45,"Returns the requested model name."),("jev_adapter",48,61,"Creates the Jev adapter."),("llm_adapter",64,76,"Creates the LLM adapter."),("get_adapter",79,84,"Returns the adapter for a provider.")],
}
CL={
"backend/app/core/taxonomy.py":[("Category",11,17),("Priority",72,76),("Sentiment",79,82),("TicketStatus",85,89),("Channel",92,96),("Provider",99,101),("ExecutionStatus",104,110),("ComparisonStatus",113,116),("BulkJobStatus",119,125)],
"backend/app/providers/base.py":[("ProviderInput",32,46),("ProviderResult",68,76),("ProviderFailure",79,106),("Adapter",138,139)],
"backend/app/providers/jev.py":[("JevAdapter",104,160)],
"backend/app/providers/ollama.py":[("OllamaAdapter",80,121)],
}
nodes=[];edges=[]
def E(s,t,ty,w):edges.append({"source":s,"target":t,"type":ty,"direction":"forward","weight":w})
for p,(s,t,c) in S.items():
    f="file:"+p
    nodes.append({"id":f,"type":"file","name":p.split('/')[-1],"filePath":p,"summary":s,"tags":t,"complexity":c})
    for n,a,b,sm in FN.get(p,[]):
        i=f"function:{p}:{n}"
        nodes.append({"id":i,"type":"function","name":n,"filePath":p,"lineRange":[a,b],"summary":sm,"tags":["function",t[0],"helper"],"complexity":"simple" if b-a<30 else "moderate"})
        E(f,i,"contains",1.0)
    for n,a,b in CL.get(p,[]):
        i=f"class:{p}:{n}"
        nodes.append({"id":i,"type":"class","name":n,"filePath":p,"lineRange":[a,b],"summary":f"{n} definition in {p.split('/')[-1]}.","tags":["class",t[0],"definition"],"complexity":"simple" if b-a<30 else "moderate"})
        E(f,i,"contains",1.0)
    for x in imp[p]:E(f,"file:"+x,"imports",0.7)
E("class:backend/app/providers/jev.py:JevAdapter","class:backend/app/providers/base.py:Adapter","implements",0.9)
E("class:backend/app/providers/ollama.py:OllamaAdapter","class:backend/app/providers/base.py:Adapter","implements",0.9)
json.dump({"nodes":nodes,"edges":edges},open('.ua/intermediate/batch-23.json','w'))
print(len(nodes),len(edges))
