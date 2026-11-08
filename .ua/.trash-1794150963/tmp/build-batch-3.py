import json, math, os, re
P='frontend/src/'
inp=json.load(open('tmp/batch-input-3.json'))
res={r['path']:r for r in json.load(open('tmp/ua-file-extract-results-3.json'))['results']}
imports=inp['batchImportData']; nm=inp['neighborMap']
CN='Imports `cn` from the external npm package "cn" rather than the local "@/lib/utils" helper, so no project-internal import edge exists for it.'
F={
'app/AppShell.tsx':("Application layout route that renders the responsive sidebar and mobile navigation sheet, header with provider status badges and global ticket search, and the routed page outlet; it also keeps the document title in sync with the matched route.",['component','layout','navigation','entry-point','accessibility'],'complex',"Reads the page title from React Router's `useMatches` and each route's `handle.title`, keeping titles declared beside the routes."),
'app/PlaceholderPage.tsx':("Provides the honest stand-in page for features a later build phase delivers and the catch-all not-found page, both built on the shared empty state.",['component','placeholder','error-page','routing'],'simple',None),
'app/router.tsx':("Declares the browser router: AppShell as the layout route with child routes for the overview dashboard, tickets, compare, comparisons, executions, a placeholder settings page, and a not-found fallback.",['routing','entry-point','configuration','navigation'],'moderate',"Uses the React Router `handle` field to attach a title to each route, which AppShell consumes."),
'components/ConfirmDialog.tsx':("Reusable confirmation dialog for destructive actions that stays open with a pending label until the caller closes it after the request succeeds.",['component','dialog','confirmation','reusable'],'moderate',None),
'components/Detail.tsx':("Tiny presentational component rendering one labelled value inside a definition list, with a dash for missing values.",['component','presentational','reusable','utility'],'simple',None),
'components/ListControls.tsx':("Shared list-page controls: a dropdown filter with an All option and a pager showing the total, current page, and previous and next buttons.",['component','filtering','pagination','reusable'],'moderate',"Maps an \"all\" sentinel to an empty string because a Radix Select item cannot hold an empty value."),
'components/states.tsx':("Shared loading, error, and empty state components that give every page consistent async feedback, using status and alert ARIA roles.",['component','loading-state','error-handling','accessibility','reusable'],'moderate',None),
'components/ui/alert-dialog.tsx':("shadcn/ui alert dialog primitives wrapping Radix AlertDialog with project styling, including size variants plus action and cancel buttons built on Button.",['component','ui-primitive','shadcn','dialog','accessibility'],'moderate',CN),
'components/ui/badge.tsx':("shadcn/ui badge component with class-variance-authority variants and optional rendering through a Radix Slot.",['component','ui-primitive','shadcn','variants'],'simple',CN),
'components/ui/button.tsx':("shadcn/ui button defining the project's variant and size styles with class-variance-authority, with optional Radix Slot rendering; other UI primitives build on it.",['component','ui-primitive','shadcn','variants'],'moderate',CN),
'components/ui/card.tsx':("shadcn/ui card family of styled div wrappers for the header, title, description, action, content, and footer regions of a card.",['component','ui-primitive','shadcn','layout'],'moderate',CN),
'components/ui/dialog.tsx':("shadcn/ui modal dialog primitives wrapping Radix Dialog, with an overlay, optional close buttons, and header and footer layout helpers.",['component','ui-primitive','shadcn','dialog','accessibility'],'moderate',CN),
'components/ui/input.tsx':("shadcn/ui styled single-line text input wrapping the native input element.",['component','ui-primitive','shadcn','form'],'simple',CN),
'components/ui/label.tsx':("shadcn/ui form label wrapping the Radix Label primitive with project styling.",['component','ui-primitive','shadcn','form','accessibility'],'simple',CN),
'components/ui/select.tsx':("shadcn/ui dropdown select primitives wrapping Radix Select, with a styled trigger, portalled content, items, separators, and scroll buttons.",['component','ui-primitive','shadcn','form','accessibility'],'moderate',CN),
'components/ui/sheet.tsx':("shadcn/ui slide-in side panel built on the Radix Dialog primitive, supporting top, right, bottom, and left placement; AppShell uses it for mobile navigation.",['component','ui-primitive','shadcn','dialog','navigation'],'moderate',CN),
'components/ui/table.tsx':("shadcn/ui table family of styled semantic table elements, with a container that scrolls horizontally on overflow.",['component','ui-primitive','shadcn','table'],'moderate',CN),
'components/ui/textarea.tsx':("shadcn/ui styled multi-line text input wrapping the native textarea element.",['component','ui-primitive','shadcn','form'],'simple',CN),
'features/compare/ComparePage.tsx':("Compare workbench page where the user loads or creates a ticket, runs Jev and the LLM side by side, and sees the field agreement summary without any winner being chosen.",['component','page','comparison','workbench','entry-point'],'moderate',None),
'features/compare/ProviderColumn.tsx':("Renders one provider's side of the compare workbench: live status and elapsed timer, normalized classification fields with agreement markers, free text, and token and cost usage.",['component','comparison','provider-result','presentational'],'complex',"Shows confidence only for Jev and states that Jev does not support summary or resolution text instead of implying it generates free-form output."),
}
U=['component','ui-primitive','shadcn']
def u(s,*t): return (s,U+list(t),'simple')
Fn={
'app/AppShell.tsx':{
 'NavList':("Renders the main navigation links from the NAV table, highlighting the active route and notifying the caller on navigation.",['component','navigation','accessibility'],'simple'),
 'ThemeToggle':("Button that switches between light and dark themes through next-themes.",['component','theme','ui-control'],'simple'),
 'Sidebar':("Sidebar content with the brand link, navigation list, theme toggle, and version label, shared by desktop and mobile layouts.",['component','navigation','layout'],'simple'),
 'ProviderBadges':("Header badges showing whether the Jev and LLM providers are configured, based on the provider status query.",['component','provider-status','status-indicator'],'simple'),
 'GlobalSearch':("Header search form that navigates to the ticket list with the trimmed query in the URL.",['component','search','navigation','form'],'simple'),
 'AppShell':("Layout route component combining a skip link, desktop sidebar, mobile sheet, header, and routed outlet while syncing the document title from route handles.",['component','layout','navigation','accessibility'],'moderate'),
},
'app/PlaceholderPage.tsx':{
 'PlaceholderPage':("Shows a Not built yet empty state naming the feature and the build phase that delivers it, without fake data.",['component','placeholder','empty-state'],'simple'),
 'NotFoundPage':("Catch-all page showing a Page not found empty state with a link back to the overview.",['component','error-page','routing'],'simple'),
},
'components/ConfirmDialog.tsx':{'ConfirmDialog':("Controlled alert dialog for destructive actions that prevents auto-close on confirm and disables its buttons while pending.",['component','dialog','confirmation','reusable'],'simple')},
'components/Detail.tsx':{'Detail':("Renders a dt and dd pair for one labelled value, showing a dash when the value is missing.",['component','presentational','reusable'],'simple')},
'components/ListControls.tsx':{
 'FilterSelect':("Dropdown filter with an All option that reports an empty string when All is chosen, with optional display labels for options.",['component','filtering','form','reusable'],'simple'),
 'Pager':("Shows the item total and page position with previous and next buttons disabled at the range limits.",['component','pagination','reusable'],'simple'),
},
'components/states.tsx':{
 'LoadingState':("Spinner with a label in a status live region for pending data.",['component','loading-state','accessibility'],'simple'),
 'ErrorState':("Alert-role error message taken from an Error instance, with an optional Try again button.",['component','error-handling','accessibility'],'simple'),
 'EmptyState':("Dashed-border panel with an icon, title, optional explanation, and optional action for pages with nothing to show.",['component','empty-state','reusable'],'simple'),
},
'components/ui/alert-dialog.tsx':{
 'AlertDialog':u("Root wrapper of the Radix AlertDialog primitive that adds the data-slot attribute.",'dialog'),
 'AlertDialogTrigger':u("Wraps the Radix trigger element that opens the alert dialog.",'dialog'),
 'AlertDialogPortal':u("Wraps the Radix portal that renders alert dialog content outside the parent DOM tree.",'dialog'),
 'AlertDialogOverlay':u("Styled backdrop displayed behind the alert dialog.",'dialog'),
 'AlertDialogContent':u("Centered alert dialog panel with default and small sizes, rendered in a portal above the overlay.",'dialog'),
 'AlertDialogHeader':u("Layout container for the alert dialog title and description.",'dialog'),
 'AlertDialogFooter':u("Layout container for the alert dialog action buttons.",'dialog'),
 'AlertDialogMedia':u("Styled container for an icon or media element in the alert dialog.",'dialog'),
 'AlertDialogTitle':u("Styled Radix title element that names the alert dialog.",'dialog'),
 'AlertDialogDescription':u("Styled Radix description element for the alert dialog body text.",'dialog'),
 'AlertDialogAction':u("Radix confirm action rendered through Button so it accepts Button variants and sizes.",'dialog','button'),
 'AlertDialogCancel':u("Radix cancel action rendered through Button, defaulting to the outline variant.",'dialog','button'),
},
'components/ui/badge.tsx':{'Badge':u("Span-based badge applying a badgeVariants style, optionally rendering its child through a Radix Slot.",'variants')},
'components/ui/button.tsx':{'Button':u("Button applying buttonVariants variant and size styles, optionally rendering its child through a Radix Slot.",'variants')},
'components/ui/card.tsx':{
 'Card':u("Outer styled container of the card family.",'layout'),
 'CardHeader':u("Layout region for a card's title, description, and action.",'layout'),
 'CardTitle':u("Styled element for a card's heading text.",'layout'),
 'CardDescription':u("Styled element for a card's muted supporting text.",'layout'),
 'CardAction':u("Region positioning an action control in the card header.",'layout'),
 'CardContent':u("Main body region of a card.",'layout'),
 'CardFooter':u("Bottom region of a card for actions or secondary content.",'layout'),
},
'components/ui/dialog.tsx':{
 'Dialog':u("Root wrapper of the Radix Dialog primitive that adds the data-slot attribute.",'dialog'),
 'DialogTrigger':u("Wraps the Radix trigger element that opens the dialog.",'dialog'),
 'DialogPortal':u("Wraps the Radix portal that renders dialog content outside the parent DOM tree.",'dialog'),
 'DialogClose':u("Wraps the Radix close control for the dialog.",'dialog'),
 'DialogOverlay':u("Styled backdrop displayed behind the dialog.",'dialog'),
 'DialogContent':u("Dialog panel rendered in a portal above the overlay, with a close button shown by default.",'dialog'),
 'DialogHeader':u("Layout container for the dialog title and description.",'dialog'),
 'DialogFooter':u("Layout container for dialog actions with an optional outline Close button.",'dialog'),
 'DialogTitle':u("Styled Radix title element that names the dialog.",'dialog'),
 'DialogDescription':u("Styled Radix description element for the dialog body text.",'dialog'),
},
'components/ui/input.tsx':{'Input':u("Native input element with project styling and passed-through props.",'form')},
'components/ui/label.tsx':{'Label':u("Radix Label primitive with project styling for form fields.",'form')},
'components/ui/select.tsx':{
 'Select':u("Root wrapper of the Radix Select primitive that adds the data-slot attribute.",'form'),
 'SelectGroup':u("Styled grouping container for related select items.",'form'),
 'SelectValue':u("Wraps the Radix element that displays the selected value.",'form'),
 'SelectTrigger':u("Styled control showing the current value with a chevron, which opens the dropdown.",'form'),
 'SelectContent':u("Portalled dropdown panel with a viewport and scroll buttons, supporting item-aligned and popper positioning.",'form'),
 'SelectLabel':u("Styled label for a group of select items.",'form'),
 'SelectItem':u("Selectable option with a check indicator when chosen.",'form'),
 'SelectSeparator':u("Styled divider between select items or groups.",'form'),
 'SelectScrollUpButton':u("Chevron control that scrolls the select list upward.",'form'),
 'SelectScrollDownButton':u("Chevron control that scrolls the select list downward.",'form'),
},
'components/ui/sheet.tsx':{
 'Sheet':u("Root of the side panel, wrapping the Radix Dialog primitive.",'dialog'),
 'SheetTrigger':u("Wraps the Radix trigger element that opens the sheet.",'dialog'),
 'SheetClose':u("Wraps the Radix close control for the sheet.",'dialog'),
 'SheetOverlay':u("Internal styled backdrop displayed behind the sheet.",'dialog'),
 'SheetContent':u("Sliding panel with selectable side and an optional close button, rendered in a portal above the overlay.",'dialog','navigation'),
 'SheetHeader':u("Layout container for the sheet title and description.",'dialog'),
 'SheetFooter':u("Layout container pushed to the bottom of the sheet for actions.",'dialog'),
 'SheetTitle':u("Styled Radix title element that names the sheet.",'dialog'),
 'SheetDescription':u("Styled Radix description element for the sheet body text.",'dialog'),
},
'components/ui/table.tsx':{
 'Table':u("Table element inside a container that scrolls horizontally on overflow.",'table'),
 'TableHeader':u("Styled thead section of a table.",'table'),
 'TableBody':u("Styled tbody section of a table.",'table'),
 'TableFooter':u("Styled tfoot section of a table.",'table'),
 'TableRow':u("Styled tr element of a table.",'table'),
 'TableHead':u("Styled th header cell of a table.",'table'),
 'TableCell':u("Styled td data cell of a table.",'table'),
 'TableCaption':u("Styled caption element of a table.",'table'),
},
'components/ui/textarea.tsx':{'Textarea':u("Native textarea element with project styling and passed-through props.",'form')},
'features/compare/ComparePage.tsx':{
 'ExistingTicket':("Form that trims and uppercases a typed ticket ID and passes it to the caller to load.",['component','form','ticket-selection'],'simple'),
 'NewTicket':("Creates a ticket through the shared ticket form and reports the new ID, showing a toast on failure.",['component','form','ticket-creation'],'simple'),
 'TicketPanel':("Displays the loaded ticket's linked ID, title, and scrollable description.",['component','presentational','ticket-display'],'simple'),
 'Agreement':("Summarizes the comparison as completed, partial, or failed, and states that agreement is not accuracy and that no winner is chosen.",['component','comparison','status-indicator','evaluation'],'moderate'),
 'TicketChooser':("Toggles between loading an existing ticket and creating a new one, reporting the chosen ticket ID.",['component','ticket-selection','form'],'simple'),
 'ComparePage':("Page component that keeps the selected ticket in URL search params, starts paired provider runs, and lays out both provider columns and the agreement summary.",['component','page','comparison','workbench'],'moderate'),
},
'features/compare/ProviderColumn.tsx':{
 'StatusLine':("Shows the provider run as not run, running, or the final execution status with a matching icon.",['component','status-indicator','provider-result'],'simple'),
 'Match':("Renders an Agree or Differ marker for a compared field, or nothing when no comparison exists.",['component','comparison','status-indicator'],'simple'),
 'Fields':("Lists normalized classification fields with Jev-only confidence and per-field agreement markers.",['component','classification','comparison','provider-result'],'moderate'),
 'FreeText':("Shows the LLM summary and suggested resolution, and states that Jev does not support them.",['component','provider-result','free-text'],'simple'),
 'Usage':("Shows token counts, estimated cost, and server time for an execution, with explicit text when tokens or pricing are unavailable.",['component','usage','cost','metrics'],'simple'),
 'ColumnHeader':("Column heading with the provider label, a Fake AI badge for mock models, and a live elapsed timer.",['component','provider-result','timer'],'simple'),
 'RunStatus':("Polite live region combining the status line, the model used, and any run error message.",['component','status-indicator','accessibility'],'simple'),
 'ProviderColumn':("Card composing the header, status, fields, free text, and usage for one provider's run.",['component','comparison','provider-result','composition'],'simple'),
},
}
fid=lambda p:'file:'+P+p
gid=lambda p,n:f'function:{P}{p}:{n}'
nodes={}; edges=[]; seen=set()
def edge(s,t,ty,w):
    k=(s,t,ty)
    if s==t or k in seen: return
    seen.add(k); edges.append({"source":s,"target":t,"type":ty,"direction":"forward","weight":w})
for p,(s,t,c,ln) in F.items():
    path=P+p; n={"id":fid(p),"type":"file","name":os.path.basename(p),"filePath":path,"summary":s,"tags":t,"complexity":c}
    if ln: n["languageNotes"]=ln
    nodes[n['id']]=n
    r=res[path]; lr={f['name']:f for f in r.get('functions',[])}; ex={e['name'] for e in r.get('exports',[])}
    fns=Fn.get(p,{})
    for name,f in lr.items():
        sig=name in ex or f['endLine']-f['startLine']+1>=10
        assert (name in fns)==sig,(p,name,sig)
    for name,(fs,ft,fc) in fns.items():
        f=lr[name]; i=gid(p,name)
        nodes[i]={"id":i,"type":"function","name":name,"filePath":path,"lineRange":[f['startLine'],f['endLine']],"summary":fs,"tags":ft,"complexity":fc}
        edge(fid(p),i,'contains',1.0)
        if name in ex: edge(fid(p),i,'exports',0.8)
    for t2 in imports[path]: edge(fid(p),'file:'+t2,'imports',0.7)
for a,b,c,d in [
 ('app/AppShell.tsx','NavList','lib/utils.ts','cn'),
 ('app/AppShell.tsx','ProviderBadges','lib/utils.ts','cn'),
 ('app/AppShell.tsx','ProviderBadges','services/queries.ts','useProviderStatus'),
 ('features/compare/ComparePage.tsx','NewTicket','services/queries.ts','useTaxonomy'),
 ('features/compare/ComparePage.tsx','NewTicket','features/tickets/hooks.ts','useCreateTicket'),
 ('features/compare/ComparePage.tsx','ComparePage','features/tickets/hooks.ts','useTicket'),
 ('features/compare/ComparePage.tsx','ComparePage','features/compare/useCompareRun.ts','useCompareRun'),
 ('features/compare/ProviderColumn.tsx','ColumnHeader','features/compare/useCompareRun.ts','useElapsed'),
 ('features/compare/ProviderColumn.tsx','ColumnHeader','features/compare/useCompareRun.ts','formatElapsed'),
 ('features/compare/ProviderColumn.tsx','Usage','lib/format.ts','formatCost'),
]: edge(gid(a,b),gid(c,d),'calls',0.8)
for a,b in [('app/AppShell.tsx','services/queries.ts'),('features/compare/ComparePage.tsx','features/compare/useCompareRun.ts'),('features/compare/ComparePage.tsx','features/tickets/hooks.ts'),('features/compare/ComparePage.tsx','services/queries.ts'),('features/compare/ProviderColumn.tsx','features/compare/useCompareRun.ts')]:
    edge(fid(a),fid(b),'depends_on',0.6)
A,PP,CD,LC,ST='app/AppShell.tsx','app/PlaceholderPage.tsx','components/ConfirmDialog.tsx','components/ListControls.tsx','components/states.tsx'
AD,DL,SH,BT,SL='components/ui/alert-dialog.tsx','components/ui/dialog.tsx','components/ui/sheet.tsx','components/ui/button.tsx','components/ui/select.tsx'
CP,PC='features/compare/ComparePage.tsx','features/compare/ProviderColumn.tsx'
for a,b,c,d in [
 (A,'Sidebar',A,'NavList'),(A,'Sidebar',A,'ThemeToggle'),(A,'AppShell',A,'Sidebar'),(A,'AppShell',A,'ProviderBadges'),(A,'AppShell',A,'GlobalSearch'),
 (A,'AppShell',SH,'SheetContent'),
 (PP,'PlaceholderPage',ST,'EmptyState'),(PP,'NotFoundPage',ST,'EmptyState'),
 (CD,'ConfirmDialog',AD,'AlertDialogContent'),(CD,'ConfirmDialog',AD,'AlertDialogAction'),(CD,'ConfirmDialog',AD,'AlertDialogCancel'),
 (LC,'FilterSelect',SL,'SelectContent'),(LC,'FilterSelect',SL,'SelectTrigger'),(LC,'Pager',BT,'Button'),
 (ST,'ErrorState',BT,'Button'),
 (AD,'AlertDialogContent',AD,'AlertDialogPortal'),(AD,'AlertDialogContent',AD,'AlertDialogOverlay'),(AD,'AlertDialogAction',BT,'Button'),(AD,'AlertDialogCancel',BT,'Button'),
 (DL,'DialogContent',DL,'DialogPortal'),(DL,'DialogContent',DL,'DialogOverlay'),(DL,'DialogContent',BT,'Button'),(DL,'DialogFooter',BT,'Button'),
 (SL,'SelectContent',SL,'SelectScrollUpButton'),(SL,'SelectContent',SL,'SelectScrollDownButton'),
 (SH,'SheetContent',SH,'SheetOverlay'),(SH,'SheetContent',BT,'Button'),
 (CP,'NewTicket','features/tickets/TicketForm.tsx','TicketForm'),(CP,'TicketChooser',CP,'ExistingTicket'),(CP,'TicketChooser',CP,'NewTicket'),
 (CP,'ComparePage',CP,'TicketChooser'),(CP,'ComparePage',CP,'TicketPanel'),(CP,'ComparePage',CP,'Agreement'),(CP,'ComparePage',PC,'ProviderColumn'),
 (CP,'ComparePage',ST,'LoadingState'),(CP,'ComparePage',ST,'ErrorState'),
 (PC,'RunStatus',PC,'StatusLine'),(PC,'Fields',PC,'Match'),
 (PC,'ProviderColumn',PC,'ColumnHeader'),(PC,'ProviderColumn',PC,'RunStatus'),(PC,'ProviderColumn',PC,'Fields'),(PC,'ProviderColumn',PC,'FreeText'),(PC,'ProviderColumn',PC,'Usage'),
]: edge(gid(a,b),gid(c,d),'contains',1.0)
batch=[f['path'] for f in inp['files']]
assert sorted(batch)==sorted(P+k for k in F)
for n in nodes.values():
    assert n['summary'] and 3<=len(n['tags'])<=5 and all(re.fullmatch(r'[a-z0-9-]+',t) for t in n['tags']),n['id']
    assert len(set(n['tags']))==len(n['tags']),n['id']
ic=sum(e['type']=='imports' for e in edges); assert ic==sum(len(v) for v in imports.values()),ic
nf=set(); ns=set()
for f,ls in nm.items():
    for x in ls:
        nf.add('file:'+x['path']); ns|={f'function:{x["path"]}:{s}' for s in x['symbols']}
imp={'file:'+t for v in imports.values() for t in v}
bad=[e for e in edges if e['source'] not in nodes or not(e['target'] in nodes or e['target'] in nf or e['target'] in imp or e['target'] in ns)]
assert not bad,bad
parts=math.ceil(max(len(nodes)/60,len(edges)/120))
files=sorted(batch); size=math.ceil(len(files)/parts); out=[]
for k in range(parts):
    fs=set(files[k*size:(k+1)*size]); pn=[n for n in nodes.values() if n['filePath'] in fs]; ids={n['id'] for n in pn}
    pe=[e for e in edges if e['source'] in ids]
    name=f'intermediate/batch-3-part-{k+1}.json'
    with open(name,'w') as fh: json.dump({"nodes":pn,"edges":pe},fh,indent=1,ensure_ascii=False)
    chk=json.load(open(name)); out.append((name,len(chk['nodes']),len(chk['edges'])))
print(len(nodes),len(edges),parts,out,'imports',ic)
assert sum(o[1] for o in out)==len(nodes) and sum(o[2] for o in out)==len(edges)
