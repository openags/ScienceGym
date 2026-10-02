#!/usr/bin/env python3
"""Deterministic, standard-library-only adapters for seven public task schemas."""
import argparse, json, pathlib, hashlib, html, textwrap
ROOT=pathlib.Path(__file__).resolve().parent
COMMIT='ebf366bde7d8b8fd0899165d168a9f8f7c43c8ca'
BASE=f'https://github.com/openags/ScienceGym/blob/{COMMIT}/tasks/'
NAMES={'perovskite':'Perovskite solar modules','chiral':'Chiral metamaterials','microscopy':'Deconwolf microscopy','fibre':'Semiconductor fibres','thermoelectric':'Thermoelectric devices','dispim':'diSPIM microscopy','acoustic':'Helical acoustic metamaterials'}
COLORS={'perovskite':'#ca7188','chiral':'#8d6bce','microscopy':'#268e96','fibre':'#dc8654','thermoelectric':'#d7aa36','dispim':'#598bd1','acoustic':'#8aaf58'}

def read(p,name): return json.loads((p/name).read_text())
def optional(p,name): return read(p,name) if (p/name).exists() else None
def source(p,name): return BASE+p.name+'/'+name

def without(d,keys): return {k:v for k,v in d.items() if k not in keys}
def refs(items): return list(items)
def unique_shared(f):
    """Losslessly pool repeated operation values; decoded by the inspector."""
    pool=[]; ids={}
    for op in f['operations']:
        for key in ['provenance','actions','acceptance','recovery','objects','detail']:
            v=op.get(key)
            if v is None: continue
            encoded=json.dumps(v,ensure_ascii=False,separators=(',',':'))
            if len(encoded)>120:
                if encoded not in ids: ids[encoded]=len(pool);pool.append(v)
                op[key]={'$shared':ids[encoded]}
    for route in f['routes']:
        for key,v in list(route.get('detail',{}).items()):
            encoded=json.dumps(v,ensure_ascii=False,separators=(',',':'))
            if len(encoded)>80 and key not in ['phases','source_reported_parameters','parameters']:
                if encoded not in ids: ids[encoded]=len(pool);pool.append(v)
                route['detail'][key]={'$shared':ids[encoded]}
    f['shared']=pool
    return f

def core(p,key,opfile='operations.json',provenancefile='provenance.json'):
    raw=read(p,opfile); prov=read(p,provenancefile)
    f={'id':key,'label':NAMES[key],'title':prov.get('title',NAMES[key]),'doi':prov.get('doi',raw.get('doi','')),'color':COLORS[key],
       'source_commit':COMMIT,'source_folder':BASE+p.name+'/','status':'Task-design reference; no task execution or scientific reproduction',
       'operations':[],'routes':[],'context':{},'dependencies':{},'source_files':{}}
    for fn in sorted(p.glob('*.json')):
        f['source_files'][fn.name]={'url':source(p,fn.name),'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()}
    f['evidence']=prov.get('evidence',prov.get('references',{}))
    if isinstance(f['evidence'],list): f['evidence']={x['id']:x for x in f['evidence']}
    for i,o in enumerate(raw['operations']):
        provenance=o.get('provenance',{})
        f['operations'].append({'id':o['id'],'title':o['title'],'stage':o.get('location_id',''),
            'actions':o.get('actions',[]),'objects':o.get('target_asset_roles',[]),'pre':o.get('preconditions',[]),'post':o.get('postconditions',[]),
            'sources':o.get('evidence_ids',o.get('source_route_ids',[])),'provenance':provenance,
            'acceptance':o.get('observable_completion','Postconditions are a design contract, not an execution receipt. See family acceptance rules.'),
            'recovery':o.get('recovery',[]),'loop':o.get('loop'),'unknowns':provenance.get('unknown_source_parameters',provenance.get('unknown_ids',[])),
            'detail':without(o,{'id','title','location_id','actions','target_asset_roles','preconditions','postconditions','evidence_ids','source_route_ids','provenance','observable_completion','recovery','loop'}),
            'source_file':opfile,'source_pointer':f'/operations/{i}'})
    f['context']['unknowns']=optional(p,'unknown_parameters.json')
    evaluator=optional(p,'evaluator_reference.json')
    f['context']['acceptance']=evaluator if evaluator else optional(p,'mock_contract.json')
    f['context']['lineage']=optional(p,'lineage_contract.json')
    return f

def adapt_chiral(p):
    f=core(p,'chiral'); b=read(p,'branches.json'); dep=read(p,'dependencies.json')
    # Adjacency already exists in explicit branch arrays. Keep authored dependency
    # semantics and joins here, avoiding a second 600-edge copy of the same arrays.
    f['dependencies']=without(dep,{'within_branch_edges'})
    f['dependencies']['explicit_edge_source']=source(p,'dependencies.json')
    f['context']['branch_policy']=without(b,{'branches'})
    for i,r in enumerate(b['branches']):
        f['routes'].append({'id':r['id'],'label':r['label'],'nodes':refs(r['operation_sequence']),
           'basis':'Authored within-branch reference order; not recovered author chronology',
           'detail':without(r,{'id','label','operation_sequence','reported_result_fixture'}),
           'reported_result_fixture_source':source(p,'branches.json')+f'#L1',
           'source_file':'branches.json','source_pointer':f'/branches/{i}/operation_sequence'})
    return f

def adapt_thermoelectric(p):
    f=core(p,'thermoelectric'); f['default_route']='PAIRED_TWO'; b=read(p,'branches.json')
    f['dependencies']={'partial_order':b['partial_order'],'transport':'MOVE is an explicit insertion obligation at each station change; displayed sequences are not silently expanded.'}
    f['context']['branch_policy']=without(b,{'branches','manufacturing_prefixes'})
    for i,r in enumerate(b['branches']):
        f['routes'].append({'id':r['id'],'label':r['label'],'nodes':refs(r['full_operation_sequence']),
            'basis':'Authored reference sequence; independent material phases may be reordered subject to stated constraints',
            'detail':without(r,{'id','label','full_operation_sequence'}),'source_file':'branches.json','source_pointer':f'/branches/{i}/full_operation_sequence'})
    return f

def adapt_fibre(p):
    f=core(p,'fibre'); f['default_route']='OPTO_SI'; b=read(p,'branches.json')
    f['dependencies']={'transport':'MOVE is required wherever the source contract changes stations. It is not silently inserted or counted as already executed.',
       'cardinality_policy':b.get('cardinality_policy'),'pn_prefix_binding':b.get('pn_prefix_binding')}
    f['context']['branch_policy']=without(b,{'branches','manufacturing_prefixes'})
    for i,r in enumerate(b['branches']):
        f['routes'].append({'id':r['id'],'label':r['label'],'nodes':refs(r['full_operation_sequence']),
            'basis':'Authored reference linearization; repeated IDs are separate occurrences and remain in order',
            'detail':without(r,{'id','label','full_operation_sequence'}),'source_file':'branches.json','source_pointer':f'/branches/{i}/full_operation_sequence'})
    return f

def adapt_perovskite(p):
    f=core(p,'perovskite'); raw=read(p,'operations.json'); b=read(p,'branches.json')
    f['default_route']='SPIN_MODULES'
    f['dependencies']={'partial_order':b['partial_order'], 'count_warning':b['count_warning']}
    f['context']['branch_policy']=without(b,{'branches','partial_order'})
    f['context']['service_definitions']=raw['service_definitions']
    f['context']['identity_binding']=raw['identity_binding']
    for name in ['control_packages.json','material_cards.json','granularity_gaps.json','RELEASE_BOUNDARY.json','agent_visible.json','coverage_matrix.json']:
        f['context'][name.removesuffix('.json')]=read(p,name)
    for o,mapped in zip(raw['operations'],f['operations']):
        mapped['unknowns']=o.get('unknown_ids',[])
        mapped['objects']=['No per-operation asset-role list supplied; inspect the bound service card, material cards and identity rules']
        bound=[s for sid,s in raw['service_definitions'].items() if o['id'].startswith(sid+'_')]
        if len(bound)>1:
            bound=sorted(bound,key=lambda s:len(s['id']),reverse=True)[:1]
        if bound: mapped['detail']['service_card']=bound[0]
    for i,r in enumerate(b['branches']):
        f['routes'].append({'id':r['id'],'label':r['label'],'nodes':refs(r['full_operation_sequence']),
            'basis':'Authored reference order; condition and replicate obligations are not silently expanded',
            'detail':without(r,{'id','label','full_operation_sequence'}),'source_file':'branches.json','source_pointer':f'/branches/{i}/full_operation_sequence'})
    return f

def acoustic_nodes(items):
    out=[]
    for x in items:
        if isinstance(x,str): out.append(x)
        elif 'loop_variable' in x:
            out.append({'type':'loop','label':'For each '+x['loop_variable'],'meta':without(x,{'body'}),'children':acoustic_nodes(x['body'])})
        elif 'set_condition' in x:
            out.append({'type':'group','label':'Set condition: '+str(x['set_condition']),'meta':without(x,{'steps'}),'children':acoustic_nodes(x['steps'])})
        elif 'verify_condition' in x:
            out.append({'type':'condition','label':'Verify '+str(x['verify_condition']),'meta':x})
        else: raise ValueError('Unknown acoustic step schema: '+str(x))
    return out

def adapt_acoustic(p):
    f=core(p,'acoustic'); b=read(p,'branches.json'); f['dependencies']=read(p,'dependencies.json')
    f['context']['branch_policy']=without(b,{'branches'})
    for i,r in enumerate(b['branches']):
        nodes=refs(r['prelude'])
        for phase in r['phases']:
            nodes.append({'type':'group','label':phase['title_en'],'meta':without(phase,{'steps','title_en'}),'children':acoustic_nodes(phase['steps'])})
        nodes+=refs(r['epilogue'])
        f['routes'].append({'id':r['id'],'label':r['label'],'nodes':nodes,
            'basis':'Authored phase order with unexpanded nested loops; values and completion rules retained verbatim',
            'detail':without(r,{'id','label','phases','prelude','epilogue'}),'source_file':'branches.json','source_pointer':f'/branches/{i}'})
    f['default_route']='WHOLE_PAPER_PRACTICAL'
    return f

def adapt_dispim(p):
    raw=read(p,'OPERATIONS.json'); prov=raw['provenance']; b=read(p,'BRANCHES.json')
    f={'id':'dispim','label':NAMES['dispim'],'title':prov['title'],'doi':prov['doi'],'color':COLORS['dispim'],'source_commit':COMMIT,
       'source_folder':BASE+p.name+'/','status':'Static authored task design; no hardware, physics or execution', 'operations':[],'routes':[],
       'source_files':{fn.name:{'url':source(p,fn.name),'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.glob('*.json'))},
       'evidence':{'main':prov['main'],'supplement':prov['supplement']},'context':{'global_unknowns':raw['global_unknowns'],'global_rules':raw['global_rules'],'source_version':prov['main_version'],'design_gaps':read(p,'DESIGN_GAPS.json')},
       'dependencies':{'branch_contracts':b['branches'],'source_issues':b['source_issues']}}
    for i,o in enumerate(raw['operations']):
        f['operations'].append({'id':o['op_id'],'title':o['name_en'],'stage':o['stage'],'actions':[o['authored_robot_handling']],
            'objects':o['asset_ids'],'pre':o['preconditions'],'post':o['postconditions'],'sources':o['evidence'],
            'acceptance':o['observable_evidence'],'recovery':o['failure_or_recovery'],'unknowns':o['unknown_parameters'],
            'loop':o['repeat'],'provenance':{'source_fact':o['source_fact'],'kind':o['provenance_kind'],'source_steps':o['source_steps'],'robot_handling':'Authored task interface; not source human trajectory'},
            'source_file':'OPERATIONS.json','source_pointer':f'/operations/{i}','detail':{'execution_status':o['execution_status'],'motion_contract':o['motion_contract']}})
    for i,r in enumerate(b['route_templates']):
        f['routes'].append({'id':r['route_id'],'label':r['name_en'],'nodes':refs(r['operation_sequence']),
            'basis':'Authored reference route with source-step mappings; repeated P001/P004 occurrences intentionally retained',
            'detail':without(r,{'route_id','name_en','operation_sequence'}),'source_file':'BRANCHES.json','source_pointer':f'/route_templates/{i}'})
    full=read(p,'FIRST_COMPLETE_ROUTE.json'); f['context']['acceptance']=full['completion_evaluator'];f['context']['coverage']=full['source_step_coverage']
    f['context']['authored_sequence_note']=full['authored_sequence_note']
    return f

def adapt_microscopy(p):
    raw=read(p,'operation_sequences.json'); prov=read(p,'source_bindings.json'); interaction=read(p,'interaction_design.json'); ev=read(p,'evaluator_reference.json')
    f={'id':'microscopy','label':NAMES['microscopy'],'title':prov['title'],'doi':prov['doi'],'color':COLORS['microscopy'],'source_commit':COMMIT,
       'source_folder':BASE+p.name+'/','status':'Paper-wide source-reported program plus authored gap connectors; preset outputs only; no real-world execution',
       'operations':[],'routes':[],'evidence':prov['references'],'macros':interaction['macros'],
       'source_files':{fn.name:{'url':source(p,fn.name),'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()} for fn in sorted(p.glob('*.json'))},
       'context':{'acceptance':without(ev,{'branch_requirements'}),'recovery':read(p,'recovery_design.json'),'scope':read(p,'paper_coverage.json')},
       'dependencies':{'branch_contracts':ev['branch_requirements'],'rule':'Preparation edges are explicit in evaluator reference. Acquisition lists are obligations, not invented global chronology; source order annotations are retained.'}}
    for i,b in enumerate(raw['wet_lab_branches']):
        nodes=[]
        for j,o in enumerate(b['preparation']):
            f['operations'].append({'id':o['id'],'title':o['label'],'stage':o['kind'],'actions':[], 'action_macro':o['interaction_macro'],
              'objects':[b['carrier'],'same branch specimen and source-listed material tokens'],'pre':[o['precondition_state']],'post':[o['output_state']],
              'sources':o['source_refs'],'acceptance':o['transition_evidence'],'recovery':'See family recovery cases; authored task behavior, not laboratory rescue advice.',
              'unknowns':o['unknowns'],'loop':{'repeats':o['reported_parameters']['repeats']} if 'repeats' in o['reported_parameters'] else None,
              'provenance':{'reported_parameter_status':o['reported_parameter_status'],'interaction_macro':'Authored task interface','unknown_parameter_policy':o['unknown_parameter_policy']},
              'detail':{'reported_parameters':o['reported_parameters'],'required_for_branch':o['required_for_branch']},
              'source_file':'operation_sequences.json','source_pointer':f'/wet_lab_branches/{i}/preparation/{j}'})
            nodes+=refs([o['id']])
        acquisitions=[]
        for j,a in enumerate(b['acquisition_variants']):
            f['operations'].append({'id':a['id'],'title':'Acquire: '+a['id'].replace('_',' '),'stage':a['station'],'actions':[],'action_macro':'acquire',
             'objects':[b['carrier'],a['objective'],a['detector']], 'pre':['prepared specimen: '+b['prepared_state']],'post':['Raw acquisition record required; exact state token not supplied in this variant record'],
             'sources':a['source_refs'],'acceptance':['Immutable specimen/carrier/field/modality record; family acquisition acceptance gates apply'],
             'recovery':'See family recovery cases for focus, saturation, station, interrupted stack and field identity.',
             'unknowns':a.get('unknowns',[]),'loop':None,'provenance':{'parameters':'source-reported except labeled gaps','handling':'Authored acquisition macro','order':a.get('order','No relative variant order specified')},
             'detail':without(a,{'id','station','detector','objective','source_refs','unknowns'}), 'source_file':'operation_sequences.json','source_pointer':f'/wet_lab_branches/{i}/acquisition_variants/{j}'})
            acquisitions+=refs([a['id']])
        nodes.append({'type':'obligations','label':'Acquisition variants: required / allowed choice rules in branch contract','meta':{'order':'Only explicit per-variant order labels constrain the shown list; no edges between unordered variants'},'children':acquisitions})
        unload_id=b['id']+'__unload';analysis_id=b['id']+'__analysis'
        f['operations'].append({'id':unload_id,'title':'Unload, archive specimen and clean station','stage':'closeout','actions':[],'action_macro':'unload','objects':[b['carrier']],
          'pre':['Acquisition finished or canceled'],'post':['Specimen archived; stage empty, shutter closed, station idle'],'sources':[],
          'acceptance':['Observable lineage and safe terminal state, per authored unload macro'],'recovery':'Family recovery cases apply','unknowns':[], 'loop':None,
          'provenance':{'kind':'Authored macro reference; inspector ID assigned for navigation, not a new reported source operation'},'detail':{},'source_file':'interaction_design.json','source_pointer':'/macros/unload'})
        f['operations'].append({'id':analysis_id,'title':'Compare and preserve derived records','stage':'analysis','actions':b['analysis_actions'],'objects':['immutable raw acquisition records'],
          'pre':['Saved immutable records'],'post':['Required analysis records; exact state tokens unspecified'],'sources':b['source_refs'],'acceptance':b['analysis_actions'],
          'recovery':'Family data-parent and analysis recovery rules apply','unknowns':b['source_gaps'],'loop':None,
          'provenance':{'kind':'Source-bound analysis obligations; displayed in authored handling order'},'detail':{},'source_file':'operation_sequences.json','source_pointer':f'/wet_lab_branches/{i}/analysis_actions'})
        nodes+=refs([unload_id,analysis_id])
        f['routes'].append({'id':b['id'],'label':b['title'],'nodes':nodes,'basis':'Preparation list and authored handling sequence; acquisition obligations do not imply a single source order',
          'detail':without(b,{'id','title','preparation','acquisition_variants','analysis_actions'}),'source_file':'operation_sequences.json','source_pointer':f'/wet_lab_branches/{i}'})
    for i,b in enumerate(raw['data_workstation_branches']):
        seq=[]
        for j,action in enumerate(b['actions']):
            oid=b['id']+'__action_'+str(j+1);seq.append(oid)
            f['operations'].append({'id':oid,'title':action,'stage':'data workstation','actions':[action],'objects':b['inputs'],'pre':['Source-matched inputs required; no per-action state predicate supplied'],
              'post':['Preserve result record; no per-action state predicate supplied'],'sources':b['source_refs'],'acceptance':['Family data requirements apply'],'recovery':'Family recovery rules apply','unknowns':b['unknowns'],
              'loop':None,'provenance':{'kind':'Authored navigation ID for source-bound data-action list; list order is not a proven execution dependency'},'detail':{},
              'source_file':'operation_sequences.json','source_pointer':f'/data_workstation_branches/{i}/actions/{j}'})
        f['routes'].append({'id':b['id'],'label':b['title'],'nodes':[{'type':'obligations','label':'Data-action obligations; order not asserted','meta':{},'children':refs(seq)}],
           'basis':'Listed data obligations; no chronological arrows asserted','detail':without(b,{'id','title','actions'}),'source_file':'operation_sequences.json','source_pointer':f'/data_workstation_branches/{i}'})
    return f

ADAPTERS={'perovskite':adapt_perovskite,'chiral':adapt_chiral,'microscopy':adapt_microscopy,'fibre':adapt_fibre,'thermoelectric':adapt_thermoelectric,'dispim':adapt_dispim,'acoustic':adapt_acoustic}

def walk(nodes,depth=0):
    for n in nodes:
        if isinstance(n,str): n={'type':'op','id':n}
        yield n,depth
        if 'children' in n: yield from walk(n['children'],depth+1)

def resolve(f,v): return f['shared'][v['$shared']] if isinstance(v,dict) and '$shared' in v else v

def svg(f):
    r=next((r for r in f['routes'] if r['id']==f.get('default_route')),f['routes'][0]); ops={o['id']:o for o in f['operations']}; rows=list(walk(r['nodes']))
    width=1440; rowh=76; height=max(420+len(rows)*rowh,400+len(f['routes'])*55)
    e=html.escape; out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',f'<title id="title">{e(f["label"])} task routes</title>',f'<desc id="desc">All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector. No scientific execution claimed.</desc>', '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="none" stroke="#708399"/></marker></defs>', '<style>text{font-family:Arial,sans-serif} .muted{fill:#a9b7c8;font-size:16px}.title{fill:#f4f7fc;font-weight:700}.small{fill:#a9b7c8;font-size:14px}</style>',f'<rect width="{width}" height="{height}" fill="#101820"/>',f'<rect x="0" y="0" width="{width}" height="8" fill="{f["color"]}"/>', '<text x="48" y="62" class="muted">SCIENCEGYM / TASK EXPLORER</text>',f'<text x="48" y="118" font-size="38" class="title">{e(f["label"])}</text>', f'<text x="48" y="156" class="muted">{len(f["operations"])} operation definitions · {len(f["routes"])} route / branch records · 0 validated runnable whole-paper tasks</text>', '<rect x="48" y="182" width="1344" height="72" rx="10" fill="#25303b"/>','<text x="68" y="211" fill="#e8bf69" font-size="16">DESIGN REFERENCE ONLY · Reported scientific stages + separately authored robot handling</text>','<text x="68" y="236" class="small">Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.</text>',f'<text x="48" y="292" class="title" font-size="22">Route {e(r["id"])} · every listed step</text>']
    for j,line in enumerate(textwrap.wrap(r['label'],84)):out.append(f'<text x="48" y="{320+j*21}" class="muted">{e(line)}</text>')
    out.append('<text x="1000" y="292" class="title" font-size="22">All route choices</text>')
    for i,route in enumerate(f['routes']):
        y=333+i*55
        out.append(f'<rect x="1000" y="{y}" width="392" height="48" rx="6" fill="#1b2935"/>')
        out.append(f'<text x="1014" y="{y+19}" fill="{f["color"]}" font-size="13" font-weight="700">{e(route["id"])}</text>')
        label=textwrap.shorten(route['label'],width=54,placeholder='…')
        out.append(f'<text x="1014" y="{y+38}" fill="#e4ecf7" font-size="12">{e(label)}</text>')
    for idx,(node,depth) in enumerate(rows):
        y=365+idx*rowh;x=48+depth*28;w=900-depth*28
        if node['type']=='op':
            op=ops[node['id']];label=op['title']; badge=node['id'];fill='#1b2935';col=f['color']
            loop=op.get('loop'); tail=(' ↻ repeat contract' if loop else '')
        else: label=node['label'];badge=node['type'].upper();fill='#2a2c2b' if node['type']=='loop' else '#23313e';col='#e8bf69';tail=''
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="64" rx="8" fill="{fill}" stroke="{col}" stroke-opacity=".5"/>')
        out.append(f'<text x="{x+14}" y="{y+20}" fill="{col}" font-size="12" font-weight="700">{idx+1:02d} · {e(badge+tail)}</text>')
        for k,line in enumerate(textwrap.wrap(label,99-depth*3)[:2]):out.append(f'<text x="{x+14}" y="{y+40+k*16}" fill="#edf3fc" font-size="14">{e(line)}</text>')
        # Display connectors only at root ordered level; group children can be loop bodies or unordered obligations.
        if idx+1<len(rows) and depth==0 and rows[idx+1][1]==0 and node['type']=='op' and rows[idx+1][0]['type']=='op':
            out.append(f'<path d="M{int(x+w/2)},{y+64}v12" stroke="#708399" stroke-dasharray="3 3" marker-end="url(#arrow)"/>')
    out.append(f'<text x="48" y="{height-24}" class="small">Source snapshot {COMMIT[:12]} · Full branch routes and operation details: {f["id"]}.md and interactive explorer</text></svg>')
    result='\n'.join(out)
    result=result.replace('<text ', '<text font-family="Arial, sans-serif" ')
    result=result.replace('class="muted"', 'fill="#a9b7c8" font-size="16"').replace('class="small"', 'fill="#a9b7c8" font-size="14"').replace('class="title"', 'fill="#f4f7fc" font-weight="700"')
    return result

def md(f):
    lines=[f'# {f["label"]}: task route map','',f'![{f["label"]} route diagram](../diagrams/{f["id"]}.svg)','',f'Paper: **{f["title"]}** · [DOI](https://doi.org/{f["doi"]})','',f'{f["status"]}. Counts describe task representation, not experiments or success.','', '**Reading rule:** numbered rows preserve reference-list occurrences. A loop body is shown once and must be repeated under its original binding, not treated as executed. An unordered obligation group has no inferred chronological edges. Source-reported scientific facts and authored handling are distinct.','',f'[Immutable source task package]({f["source_folder"]}) · [Interactive inspector](../index.html)','']
    ops={o['id']:o for o in f['operations']}
    for r in f['routes']:
        lines.extend([f'## {r["id"]} — {r["label"]}','',r['basis'],'',f'[Exact route source]({f["source_files"][r["source_file"]]["url"]}) · JSON pointer: `{r["source_pointer"]}`',''])
        for n,depth in walk(r['nodes']):
            indent='  '*depth
            if n['type']=='op':
                o=ops[n['id']]; repeat=' · **repeat contract**' if o.get('loop') else ''
                lines.append(f'{indent}- `{o["id"]}` {o["title"]}{repeat}')
            else:
                lines.append(f'{indent}- **{n["type"].upper()}: {n["label"]}**')
                if n.get('meta'):lines.append(indent+'  - Binding: '+json.dumps(n['meta'],ensure_ascii=False,separators=(',',':')))
        lines.extend(['','<details><summary>Branch state, choices, lineage and loop obligations</summary>','', '```json',json.dumps({k:resolve(f,v) for k,v in r['detail'].items()},ensure_ascii=False,indent=2),'```','','</details>',''])
    lines.extend(['## Operation contracts','','Every operation is clickable in the offline inspector, with robot actions, target objects, pre/post state, provenance, unknowns and acceptance/recovery. Raw task JSON is the source of truth; this visualization is a public evaluator/reference view, not an agent prompt.',''])
    return '\n'.join(lines)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--tasks',type=pathlib.Path,default=ROOT.parent.parent/'tasks');parser.add_argument('--only',choices=list(ADAPTERS));args=parser.parse_args()
    keys=[args.only] if args.only else list(ADAPTERS);manifest=[]
    for key in keys:
        f=unique_shared(ADAPTERS[key](args.tasks/(key+'_operations_v2')))
        encoded=json.dumps(f,ensure_ascii=False,separators=(',',':'))
        (ROOT/'data'/f'{key}.json').write_text(encoded+'\n');(ROOT/'data'/f'{key}.js').write_text('window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA['+json.dumps(key)+']='+encoded+';\n')
        (ROOT/'diagrams'/f'{key}.svg').write_text(svg(f));(ROOT/'docs'/f'{key}.md').write_text(md(f))
        manifest.append({'id':key,'operations':len(f['operations']),'routes':len(f['routes']),'bytes':len(encoded.encode())})
        print(manifest[-1])
    (ROOT/'manifest.json').write_text(json.dumps({'commit':COMMIT,'families':manifest},indent=2)+'\n')
if __name__=='__main__':main()
