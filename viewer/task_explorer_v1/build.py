#!/usr/bin/env python3
"""Deterministic, standard-library-only adapters for twenty-four public task schemas."""
import argparse, json, pathlib, hashlib, html, textwrap, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from acoustic_adapters import adapt_wavefront, adapt_bianisotropic, adapt_edge, ACOUSTIC_COMMIT, PACKAGES as ACOUSTIC_PACKAGES
from mechanical_adapters import adapt_origami_memory, adapt_ring_origami, adapt_mechanical_backprop, MECHANICAL_COMMIT, PACKAGES as MECHANICAL_PACKAGES
from assembly_adapters import adapt_granular_assembly, adapt_beaded, adapt_thermal_jamming, ASSEMBLY_COMMIT, PACKAGES as ASSEMBLY_PACKAGES
from final_materials_adapters import adapt_horn_acoustics, adapt_mechanical_logic, adapt_cold_shape, FINAL_MATERIALS_COMMIT, PACKAGES as FINAL_MATERIALS_PACKAGES
from nature_materials_adapters import adapt_gear, adapt_hydrogel_optical, NATURE_MATERIALS_COMMIT, PACKAGES as NATURE_MATERIALS_PACKAGES
ROOT=pathlib.Path(__file__).resolve().parent
COMMIT='293e32da790303c1a17131e036235f69a5f342e0'
BASE=f'https://github.com/openags/ScienceGym/blob/{COMMIT}/tasks/'
COOLING_COMMIT='9a9472b996145ff7f7a4c138c7477b4e734d8835'
SOURCE_COMMITS={**{key:NATURE_MATERIALS_COMMIT for key in NATURE_MATERIALS_PACKAGES}, **{key:FINAL_MATERIALS_COMMIT for key in FINAL_MATERIALS_PACKAGES}, **{key:ASSEMBLY_COMMIT for key in ASSEMBLY_PACKAGES}, **{key:MECHANICAL_COMMIT for key in MECHANICAL_PACKAGES}, 'cooling':COOLING_COMMIT, **{key:ACOUSTIC_COMMIT for key in ACOUSTIC_PACKAGES}}
def source_commit(key): return SOURCE_COMMITS.get(key,COMMIT)
def source_base(key): return f'https://github.com/openags/ScienceGym/blob/{source_commit(key)}/tasks/'
NAMES={'cooling':'Directional radiative cooling','emvp':'Embedded extrusion-volumetric printing','prismatic':'Prismatic metamaterials','perovskite':'Perovskite solar modules','chiral':'Chiral metamaterials','microscopy':'Deconwolf microscopy','fibre':'Semiconductor fibres','thermoelectric':'Thermoelectric devices','dispim':'diSPIM microscopy','acoustic':'Helical acoustic metamaterials'}
COLORS={'cooling':'#68bfc7','emvp':'#e5a36e','prismatic':'#4db7ad','perovskite':'#ca7188','chiral':'#8d6bce','microscopy':'#268e96','fibre':'#dc8654','thermoelectric':'#d7aa36','dispim':'#598bd1','acoustic':'#8aaf58'}

def read(p,name): return json.loads((p/name).read_text())
def optional(p,name): return read(p,name) if (p/name).exists() else None
def source(p,name): return (source_base('cooling') if p.name=='directional_cooling_operations_v2' else BASE)+p.name+'/'+name

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
       'source_commit':source_commit(key),'source_folder':source_base(key)+p.name+'/','status':'Task-design reference; no task execution or scientific reproduction',
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


def prismatic_replace(items, replacements):
    """Replace a declared membership body once, without adding chronology.

    A changed source shape fails closed instead of dropping templates or guessing
    how overlapping loop bodies nest. The expansion contract supplies nesting.
    """
    result=list(items)
    for body,node in replacements:
        starts=[i for i in range(len(result)-len(body)+1) if result[i:i+len(body)]==body]
        if not body or len(starts)!=1:
            raise ValueError('Prismatic loop body must have one exact membership match: '+str(body))
        i=starts[0];result[i:i+len(body)]=[node]
    return result

def prismatic_loop(loop, children):
    meta=without(loop,{'body'})
    if isinstance(loop.get('values'),list):
        binding=(str(len(loop['values']))+' slot bindings, not specimens') if loop['loop_id']=='array_slots' else ', '.join(map(str,loop['values']))
    else:
        binding='unknown; supplied '+str(loop.get('values_from',loop.get('count_from','input required')))
    return {'type':'loop','label':loop['loop_id']+' · each '+loop['iterator']+' · '+binding,
            'meta':meta,'children':children,'ordered':False,'symbolic':True}

def prismatic_nodes(branch, branches):
    """Author/evaluator membership view; no inferred serial execution path."""
    loops={x['loop_id']:x for x in branch['loops']}
    expansion=branch['loop_expansion']
    if len(loops)!=len(branch['loops']):raise ValueError('Duplicate prismatic loop ID')
    if expansion['type']=='subcampaign_dispatch':
        dispatch=loops[expansion['outer']]
        if not isinstance(dispatch['body'],str):raise ValueError('Unknown dispatch body schema')
        children=[]
        for bid in dispatch['values']:
            child=branches[bid]
            if child['loop_expansion']['type']=='subcampaign_dispatch':raise ValueError('Recursive campaign dispatch')
            children.append({'type':'obligations','label':bid+' · '+child['title'],
                'meta':{'order':'Independent subcampaign; no chronology between branches',
                        'branch_id':bid,'source_pointer':'/branches/'+str(list(branches).index(bid)),
                        'loop_expansion':child['loop_expansion']},
                'children':prismatic_nodes(child,branches),'ordered':False})
        return [{'type':'obligations','label':'Independent subcampaign dispatch · each branch retains its own loops',
                 'meta':{'dispatch':dispatch,'loop_expansion':expansion,
                         'order':'No edges or shared sample identity inferred between subcampaigns'},
                 'children':children,'ordered':False}]

    replacements=[]
    used=set()
    def node(lid):
        loop=loops[lid];used.add(lid);children=list(loop['body'])
        if 'inner_repetitions' in loop:
            repetition=loop['inner_repetitions']
            children=[{'type':'loop','label':repetition['input']+' · supplied count: '+('unknown' if repetition['value'] is None else str(repetition['value'])),
                       'meta':repetition,'children':children,'ordered':False,'symbolic':True}]
        return prismatic_loop(loop,children)

    kind=expansion['type']
    if kind in ('nested','nested_with_setup'):
        outer=expansion['outer']
        expected_inner={'target_attempts':['attempts_per_target'],
                        'hinge_material':['target_attempts','attempts_per_target'],
                        'array_thickness':['target_attempts','attempts_per_target'],
                        'target_class':['target_ids_for_class','attempts_per_target'],
                        'pneumatic_programs':['attempts_per_program']}
        if expansion.get('inner')!=expected_inner.get(outer):
            raise ValueError('Unknown prismatic inner binding: '+str(expansion.get('inner')))
        outer_node=node(outer)
        inner=[]
        if kind=='nested_with_setup':
            setup=expansion['per_outer_setup_loop'];inner.append((loops[setup]['body'],node(setup)))
        # Boundary targets are selected by class, not one global Cartesian grid.
        if outer in ('hinge_material','array_thickness','target_class'):
            target=node('target_attempts')
            if outer=='array_thickness':
                target['meta']={**target['meta'],'targets_from':expansion['condition_target_grid']['targets_from'],
                                'null_target_list_blocks':expansion['condition_target_grid']['null_target_list_blocks']}
            if outer=='target_class':
                target['meta']={**target['meta'],'targets_from':expansion['target_ids_from'],
                                'null_class_target_list_blocks':expansion['null_class_target_list_blocks']}
            inner.append((loops['target_attempts']['body'],target))
            outer_node['children']=prismatic_replace(outer_node['children'],inner)
        elif outer=='pneumatic_programs':
            outer_node['children']=[{'type':'loop','label':'attempts_per_program · supplied repetitions required',
                'meta':{'input':expansion['inner'][0],'counts_from':expansion['counts_from'],
                        'no_inferred_four_programs':expansion['no_inferred_four_programs']},
                'children':outer_node['children'],'ordered':False,'symbolic':True}]
        elif outer!='target_attempts':raise ValueError('Unknown prismatic outer loop: '+outer)
        replacements.append((loops[outer]['body'],outer_node))
    elif kind=='sequential_then_nested':
        for lid in [expansion['setup_loop'],expansion['observation_nesting'][0]]:
            replacements.append((loops[lid]['body'],node(lid)))
    elif kind=='sequential_stages':
        for stage in expansion['stages']:
            lid=stage['loop'];replacements.append((loops[lid]['body'],node(lid)))
    else:raise ValueError('Unknown prismatic loop expansion type: '+kind)
    if used!=set(loops):raise ValueError('Unmapped prismatic loops: '+str(set(loops)-used))
    children=prismatic_replace(branch['operation_ids'],replacements)
    # CUBE_SWITCH is a between-condition obligation, not an unconditional step.
    for loop in loops.values():
        if loop.get('between_conditions'):
            body=loop['between_conditions']
            children=prismatic_replace(children,[(body,{'type':'obligations',
                'label':'Between conditions only · '+loop['loop_id'],
                'meta':{'between_conditions':body,'identity_option':loop['identity_option']},
                'children':body,'ordered':False})])
    nodes=[{'type':'obligations','label':'Operation template membership · partial order only',
            'meta':{'order':'No list-order edges asserted; inspect explicit dependencies and loop_expansion',
                    'loop_expansion':expansion},'children':children,'ordered':False}]
    if branch['conditional_recovery_operation_ids']:
        nodes.append({'type':'obligations','label':'Conditional recovery only · not a required normal-route step',
                      'meta':{'activation':'Only when source recovery conditions apply'},
                      'children':list(branch['conditional_recovery_operation_ids']),'ordered':False})
    return nodes

def adapt_prismatic(p):
    f=core(p,'prismatic'); raw=read(p,'operations.json'); b=read(p,'branches.json')
    f['status']='Author/evaluator logical inspector; symbolic task design only; no embodied execution, simulation or actor projection'
    f['default_route']='CUBE_HINGE_COMPARISON'
    f['dependencies']=read(p,'dependencies.json')
    f['context']['branch_policy']=without(b,{'branches'})
    f['context']['operation_policy']=without(raw,{'operations'})
    # Preserve complete public reference contracts, with their source visibility tags.
    for name in ['control_packages','material_cards','asset_needs','source_conflicts','source_outcomes',
                 'agent_visible','RELEASE_BOUNDARY','episode_input_contract','station_contracts',
                 'mock_contract','coverage_matrix','nonmanual_scope','source_access_audit']:
        f['context'][name]=read(p,name+'.json')
    f['context']['provenance']=read(p,'provenance.json')
    f['context']['independent_source_audit']=read(p,'independent_source_audit/audit.json')
    name='independent_source_audit/audit.json'
    f['source_files'][name]={'url':source(p,name),'sha256':hashlib.sha256((p/name).read_bytes()).hexdigest()}
    for original,mapped in zip(raw['operations'],f['operations']):
        mapped['unknowns']=original['unknown_parameter_ids']
        mapped['objects']=['No per-operation target-asset-role list supplied; inspect material, station and lineage contracts']
        mapped['acceptance']='No per-operation observable_completion field supplied; inspect postconditions and family evaluator acceptance (reference only)'
    branches={r['id']:r for r in b['branches']}
    for i,r in enumerate(b['branches']):
        selected_ids=[r['id']]
        if r['loop_expansion']['type']=='subcampaign_dispatch':selected_ids=r['loops'][0]['values']
        controls=[c for c in f['context']['control_packages']['control_packages'] if set(c['branch_ids'])&set(selected_ids)]
        f['routes'].append({'id':r['id'],'label':r['title'],'nodes':prismatic_nodes(r,branches),
            'controls':controls,
            'basis':'Unordered operation-template membership with source-declared nested loops; only explicit dependencies constrain order. No cardinalities expanded or execution claimed.',
            'detail':without(r,{'id','title'}),'source_file':'branches.json','source_pointer':f'/branches/{i}'})
    return f

def emvp_nodes(configuration, controls):
    """Preserve source lists as viewing order, never invent dependency edges.

    Mixed comparisons dispatch their exact condition routes. Control-package
    dimension contracts are separate from operation membership because this
    schema supplies no per-dimension operation-body binding.
    """
    routes=configuration.get('condition_routes')
    if routes is not None:
        if not routes or len({r['condition_id'] for r in routes})!=len(routes):
            raise ValueError('EmVP condition routes must be nonempty and unique')
        if any(not r['operation_ids'] or len(set(r['operation_ids']))!=len(r['operation_ids']) for r in routes):
            raise ValueError('EmVP condition operation lists must be nonempty and unique')
        if set(configuration['operation_ids'])!={oid for r in routes for oid in r['operation_ids']}:
            raise ValueError('EmVP condition routes must exactly cover the membership union')
        membership=[{'type':'obligations','label':'Condition '+r['condition_id']+' · separate allocated specimen route',
            'meta':{'order':'Source-authored viewing order only; apply actual condition-scoped dependencies',
                    **without(r,{'operation_ids'})},'children':list(r['operation_ids']),'ordered':False}
                    for r in routes]
        nodes=[{'type':'obligations','label':'Required comparison conditions · no shared-vial serial route',
                'meta':{'order':configuration['membership_semantics']},'children':membership,'ordered':False}]
    else:
        nodes=[{'type':'obligations','label':'Operation membership · authored viewing order only',
                'meta':{'order':'No list-adjacency edges asserted; apply declared dependencies only'},
                'children':list(configuration['operation_ids']),'ordered':False}]
    for control in controls:
        # Preserve the source's two named levels without guessing operation
        # bodies or turning state/region/site lists into independent specimens.
        inner={'type':'condition','label':'Inner observations · '+', '.join(control['inner_loop']),
               'meta':{key:control[key] for key in ['inner_loop','ordered_states','within_specimen_sites',
                       'required_outputs','loop_semantics'] if key in control}}
        outer={'type':'loop','label':'Outer allocation · '+', '.join(control['outer_loop'])+' · specimen count unknown',
               'meta':{'outer_loop':control['outer_loop'],'replication':control['replication'],
                       **({'condition_axes':control['condition_axes']} if 'condition_axes' in control else {}),
                       'binding':'Symbolic coverage only; no operation-body binding supplied by this schema'},
               'children':[inner],'ordered':False,'symbolic':True}
        nodes.append({'type':'obligations','label':control['id']+' · '+control['comparison'],
                      'meta':{'order':'Comparison coverage, not extra operation occurrences or successful repetitions',
                              'control_package':control},'children':[outer],'ordered':False})
    return nodes

def adapt_emvp(p):
    raw=read(p,'operations.json'); prov=read(p,'provenance.json'); b=read(p,'branches.json')
    controls=read(p,'control_packages.json'); control_map={c['id']:c for c in controls['packages']}
    if len(control_map)!=len(controls['packages']):raise ValueError('Duplicate EmVP control package ID')
    sources={s['id']:s for s in prov['sources']}
    f={'id':'emvp','label':NAMES['emvp'],'title':prov['title'],'doi':prov['doi'],'color':COLORS['emvp'],
       'source_commit':COMMIT,'source_folder':BASE+p.name+'/',
       'status':'Author/evaluator logical inspector; source-bounded task design only; no physical simulation, actor projection or robot execution',
       'default_route':'POSITIVE_HELIX','operations':[],'routes':[],
       'evidence':{item['id']:{**item,'source_document':sources[item['source']],
                              'url':sources[item['source']]['url']} for item in prov['locators']},
       'source_files':{fn.relative_to(p).as_posix():{'url':source(p,fn.relative_to(p).as_posix()),
                       'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()}
                       for fn in sorted(p.rglob('*.json'))},
       'context':{'branch_policy':without(b,{'configurations'}),'operation_policy':without(raw,{'operations'})},
       'dependencies':read(p,'dependencies.json')}
    aliases={'unknown_parameters':'unknowns','evaluator_reference':'acceptance','lineage_contract':'lineage'}
    for name in ['unknown_parameters','evaluator_reference','lineage_contract','control_packages','material_cards',
                 'asset_needs','source_conflicts','source_outcomes','agent_visible','RELEASE_BOUNDARY',
                 'episode_input_contract','station_contracts','mock_contract','coverage_matrix','nonmanual_scope',
                 'source_access_audit','provenance','STATUS']:
        f['context'][aliases.get(name,name)]=read(p,name+'.json')
    f['context']['independent_source_audit']=read(p,'independent_source_audit/audit.json')
    for i,o in enumerate(raw['operations']):
        f['operations'].append({'id':o['id'],'title':o['label'],'stage':o['station'],
            'actions':[o['physical_action']],
            'objects':['No per-operation object-role list supplied; inspect material, station and lineage contracts'],
            'pre':o['preconditions'],
            'post':['No postconditions field supplied; completion evidence is shown separately and is not a state-transition receipt'],
            'sources':o['source_refs'],'provenance':o['provenance'],'acceptance':o['completion_evidence'],
            'recovery':o['recovery'],'unknowns':o['required_unknowns'],'loop':None,
            'detail':{'kind':o['kind'],'schema_note':'physical_action is an authored interface; completion_evidence is a required record, not observed success'},
            'source_file':'operations.json','source_pointer':f'/operations/{i}'})
    operation_ids={op['id'] for op in f['operations']}
    for i,r in enumerate(b['configurations']):
        if len(set(r['operation_ids']))!=len(r['operation_ids']):raise ValueError('Duplicate EmVP membership ID')
        if not set(r['operation_ids'])<=operation_ids:raise ValueError('Unknown EmVP operation ID')
        bound=[control_map[cid] for cid in r['control_package_ids']]
        f['routes'].append({'id':r['id'],'label':r['goal'],'nodes':emvp_nodes(r,bound),'controls':bound,
            'basis':'Source-authored viewing order, not a causal sequence. Only declared dependencies constrain execution; condition routes use separate specimen allocations. Counts, gates and comparison coverage remain unresolved where the source says so.',
            'detail':without(r,{'id','goal'}),'source_file':'branches.json','source_pointer':f'/configurations/{i}'})
    return f

# This schema names its package differently from the public navigation key.
PACKAGE_NAMES={**ASSEMBLY_PACKAGES, **MECHANICAL_PACKAGES, 'cooling':'directional_cooling_operations_v2', **ACOUSTIC_PACKAGES}
def package_name(key): return PACKAGE_NAMES.get(key,key+'_operations_v2')

# Explicit source-loop scopes. These bind metadata only, never expanded bodies.
# L_MAP counts the three separate route leaves, not three repetitions in each leaf.
COOLING_LOOP_ROUTES={
    'L_OPT':('OPT_HEMISPHERICAL',),
    'L_ANGLE':('OPT_ANGULAR',),
    'L_TRACK':('TRACKED_STAGNATION','PID_POWER','MAP_CLEAR_DAY','MAP_HAZY_NOON'),
    'L_PID':('PID_POWER',),
    'L_MAP':('MAP_CLEAR_DAY','MAP_CLEAR_NIGHT','MAP_HAZY_NOON'),
    'L_REPEAT':None,
}

def cooling_nodes(branch,dependencies):
    """Keep route membership once and loop contracts separate from occurrences.

    Dependencies are receipt obligations, not list adjacency. The declared loop
    bodies are preserved in metadata; they do not define an inferred global
    nesting or supply missing schedules, counts, or station transfers.
    """
    members=branch['operation_ids']
    if not members or len(set(members))!=len(members):
        raise ValueError('Cooling operation membership must be nonempty and unique')
    loops=dependencies['loops']
    if len({loop['id'] for loop in loops})!=len(loops):
        raise ValueError('Duplicate cooling loop ID')
    if {loop['id'] for loop in loops}!=set(COOLING_LOOP_ROUTES):
        raise ValueError('Unknown or missing cooling loop scope')
    nodes=[{'type':'obligations','label':'Operation membership · receipt dependencies only',
            'meta':{'order':'No chronological adjacency edges are inferred; apply explicit receipt dependencies and conditional gates'},
            'children':list(members),'ordered':False}]
    for loop in loops:
        routes=COOLING_LOOP_ROUTES[loop['id']]
        if routes is not None and branch['id'] not in routes:continue
        if not set(loop['body'])<=set(members):
            raise ValueError('Cooling loop body is outside declared route membership: '+loop['id'])
        scope=('Three independent condition leaves; this view is '+branch['id']+' only. Independent repeats remain supplied inputs.'
               if loop['id']=='L_MAP' else
               'Work-order allocation across samples/sessions; no local repetition count or global nesting inferred.'
               if loop['id']=='L_REPEAT' else
               'Applicable route contract; body is metadata, not extra operation occurrences or completed repetitions.')
        nodes.append({'type':'loop','label':loop['id']+' · unexpanded schedule / count contract',
                      'meta':{'loop':loop,'scope':scope},'children':[],
                      'ordered':False,'symbolic':True})
    nodes.append({'type':'condition','label':'Required transport · each actual station change',
                  'meta':{'transport_rule':dependencies['transport_rule'],
                          'display':'The single MOVE template does not satisfy all required physical transfer instances'}})
    return nodes

def adapt_cooling(p):
    f=core(p,'cooling');raw=read(p,'operations.json');b=read(p,'branches.json')
    prov=read(p,'provenance.json');dep=read(p,'dependencies.json')
    f['status']='Author/evaluator logical inspector; source-bounded task design only; no physical simulation, actor projection or robot execution'
    f['default_route']='TRACKED_STAGNATION'
    f['dependencies']=dep
    f['context']['branch_policy']=without(b,{'branches'})
    f['context']['operation_policy']=without(raw,{'operations'})
    for name in ['control_packages','material_cards','asset_needs','source_conflicts','source_outcomes',
                 'agent_visible','RELEASE_BOUNDARY','episode_input_contract','station_contracts',
                 'mock_contract','coverage_matrix','nonmanual_scope','source_access_audit','provenance',
                 'STATUS','VERIFICATION']:
        f['context'][name]=read(p,name+'.json')
    f['context']['independent_review']=read(p,'independent_review/audit.json')
    f['source_files']={fn.relative_to(p).as_posix():{'url':source(p,fn.relative_to(p).as_posix()),
                       'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()}
                       for fn in sorted(p.rglob('*.json'))}
    f['evidence']={key:{**item,'url':prov['source_ids'][item['source_id']]}
                   for key,item in prov['evidence'].items()}
    mapped_fields={'id','title','location_id','operator_actions','manipulated_objects',
                   'preconditions','postconditions','evidence_ids','provenance',
                   'completion_evidence','recovery','unknown_parameter_ids'}
    for original,mapped in zip(raw['operations'],f['operations']):
        mapped['actions']=original['operator_actions']
        mapped['objects']=original['manipulated_objects']
        mapped['acceptance']=original['completion_evidence']
        mapped['unknowns']=original['unknown_parameter_ids']
        mapped['detail']=without(original,mapped_fields)
    operation_ids={op['id'] for op in f['operations']}
    if len(operation_ids)!=len(f['operations']):raise ValueError('Duplicate cooling operation ID')
    controls=f['context']['control_packages']['control_packages']
    control_map={control['id']:control for control in controls}
    if len(control_map)!=len(controls):raise ValueError('Duplicate cooling control ID')
    branches=b['branches']
    if len({branch['id'] for branch in branches})!=len(branches):raise ValueError('Duplicate cooling branch ID')
    for i,r in enumerate(branches):
        if not set(r['operation_ids'])<=operation_ids:raise ValueError('Unknown cooling operation ID')
        f['routes'].append({'id':r['id'],'label':r['title'],
            'nodes':cooling_nodes(r,dep),'controls':[control_map[key] for key in r['control_ids']],
            'basis':'Unordered operation membership with explicit receipt dependencies and conditional gates. Loop contracts remain symbolic; no unknown counts, global chronology, sample replication or transport instances are invented.',
            'detail':without(r,{'id','title'}),'source_file':'branches.json','source_pointer':f'/branches/{i}'})
    return f

ADAPTERS={'gear':adapt_gear,'hydrogel_optical':adapt_hydrogel_optical,'horn_acoustics':adapt_horn_acoustics,'mechanical_logic':adapt_mechanical_logic,'cold_shape':adapt_cold_shape,'granular_assembly':adapt_granular_assembly,'beaded':adapt_beaded,'thermal_jamming':adapt_thermal_jamming,'origami_memory':adapt_origami_memory,'ring_origami':adapt_ring_origami,'mechanical_backprop':adapt_mechanical_backprop,'wavefront':adapt_wavefront,'bianisotropic':adapt_bianisotropic,'edge':adapt_edge,'cooling':adapt_cooling,'emvp':adapt_emvp,'perovskite':adapt_perovskite,'chiral':adapt_chiral,'microscopy':adapt_microscopy,'fibre':adapt_fibre,'thermoelectric':adapt_thermoelectric,'dispim':adapt_dispim,'acoustic':adapt_acoustic,'prismatic':adapt_prismatic}

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
        label=textwrap.shorten(route['label'],width=48 if f['id'] in {*FINAL_MATERIALS_PACKAGES, *NATURE_MATERIALS_PACKAGES} else 54,placeholder='…')
        out.append(f'<text x="1014" y="{y+38}" fill="#e4ecf7" font-size="12">{e(label)}</text>')
    for idx,(node,depth) in enumerate(rows):
        y=365+idx*rowh;x=48+depth*28;w=900-depth*28
        if node['type']=='op':
            op=ops[node['id']];label=op['title']; badge=node['id'];fill='#1b2935';col=f['color']
            loop=op.get('loop'); tail=(' ↻ repeat contract' if loop else '')
            if f['id'] in {*MECHANICAL_PACKAGES, *ASSEMBLY_PACKAGES, *NATURE_MATERIALS_PACKAGES} and node.get('meta'):
                source_node=node['meta'].get('source_node', {})
                if isinstance(source_node,dict):
                    if source_node.get('destination_station'): label+=' · destination: '+source_node['destination_station']
                    if source_node.get('transfer_id'): badge+=' · '+source_node['transfer_id']
                    if source_node.get('from'): label+=' · '+source_node['from']+' → '+source_node['to']
                    bindings=source_node.get('bindings', {})
                    if bindings.get('phase_id'): label+=' · phase: '+bindings['phase_id']
                    if bindings.get('active_force_role'): label+=' · '+bindings['active_force_role']
        else: label=node['label'];badge=node['type'].upper();fill='#2a2c2b' if node['type']=='loop' else '#23313e';col='#e8bf69';tail=''
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="64" rx="8" fill="{fill}" stroke="{col}" stroke-opacity=".5"/>')
        out.append(f'<text x="{x+14}" y="{y+20}" fill="{col}" font-size="12" font-weight="700">{idx+1:02d} · {e(badge+tail)}</text>')
        for k,line in enumerate(textwrap.wrap(label,99-depth*3)[:2]):out.append(f'<text x="{x+14}" y="{y+40+k*16}" fill="#edf3fc" font-size="14">{e(line)}</text>')
        # Display connectors only at root ordered level; group children can be loop bodies or unordered obligations.
        if idx+1<len(rows) and depth==0 and rows[idx+1][1]==0 and node['type']=='op' and rows[idx+1][0]['type']=='op':
            out.append(f'<path d="M{int(x+w/2)},{y+64}v12" stroke="#708399" stroke-dasharray="3 3" marker-end="url(#arrow)"/>')
    out.append(f'<text x="48" y="{height-24}" class="small">Source snapshot {f["source_commit"][:12]} · Full branch routes and operation details: {f["id"]}.md and interactive explorer</text></svg>')
    result='\n'.join(out)
    if f['id']=='prismatic':
        result=result.replace('operation definitions · 12 route / branch records', 'operation templates · 12 configurations · 7 practical families')
        result=result.replace('· every listed step', '· symbolic membership')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'No adjacency arrows: template membership is unordered. Only declared source dependencies constrain order.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only.', 'Symbolic nested loop membership for the designated configuration, plus all 12 configurations. No chronological adjacency edges are inferred.')
    if f['id']=='emvp':
        result=result.replace('operation definitions · 19 route / branch records', 'operation templates · 19 configurations · 5 practical families')
        result=result.replace('· every listed step', '· authored viewing order')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'No adjacency arrows: authored viewing order is not causality. Conditions retain separate sample allocations.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only.', 'Source-authored viewing order for the selected configuration, plus all 19 configurations. No chronological adjacency edges are inferred.')
    if f['id']=='cooling':
        result=result.replace('Loop bodies are shown once with original loop metadata in the interactive inspector.', 'Loop bodies, counts and nesting text remain unexpanded metadata; no extra operation occurrences are added.')
        result=result.replace('operation definitions · 11 route / branch records', 'operation definitions · 11 physical route leaves · 6 loop contracts · 14 input gates')
        result=result.replace('· every listed step', '· unordered membership')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'No adjacency arrows: dependencies require receipts. Loops, sample allocation and physical transfers remain obligations.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only.', 'Unordered operation membership for the designated leaf, plus all 11 physical route leaves. No chronological adjacency edges are inferred.')
    if f['id'] in MECHANICAL_PACKAGES:
        result=result.replace('· every listed step', '· source template view')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'Source templates only. Typed scopes, bindings and conditional paths remain obligations; no execution is claimed.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector.', 'Source template view for the designated physical branch, with the complete physical, preparation, campaign and nonmanual index. Nested bodies are displayed once without instantiation. Exact conditions and bindings remain in the inspector and Markdown.')
    if f['id'] in NATURE_MATERIALS_PACKAGES:
        warning = {'gear': 'DESIGN ONLY · 19 distinct specimen families; geometry conflicts open. Numerical and illustrative scope stay separate.',
                   'hydrogel_optical': 'SOURCE-INCOMPLETE · Four Extended Data image sets uninspected; power/data conflicts open; Video 9 accelerated 20x.'}[f['id']]
        order = ('Gear arrows preserve authored recipe order, not historical chronology; allocation and repeated counts stay unresolved.' if f['id']=='gear' else
                 'CLOSED QUALIFIED SERVICES ONLY · Unordered membership; per-service phase order only; unresolved inputs block execution.')
        result=result.replace('DESIGN REFERENCE ONLY · Reported scientific stages + separately authored robot handling', html.escape(warning))
        result=result.replace('· every listed step', '· authored navigation / source template')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', html.escape(order))
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector.', html.escape(f['source_warnings']+' Gear recipes retain declared authored order; hydrogel lists are unordered memberships. Navigation is not source chronology.'))
    if f['id'] in FINAL_MATERIALS_PACKAGES:
        warning = {'horn_acoustics': 'DESIGN ONLY · Paired physical maps; focusing/splitting numerical. Technical reads are not specimen replicates.',
                   'mechanical_logic': 'SOURCE-INCOMPLETE · source_complete=false · Main figure panels and nine actual movies remain uninspected.',
                   'cold_shape': 'CLOSED QUALIFIED SERVICES ONLY · Eight movies and source workbook unread; derived fits are not independent validation.'}[f['id']]
        result=result.replace('DESIGN REFERENCE ONLY · Reported scientific stages + separately authored robot handling', html.escape(warning))
        result=result.replace('· every listed step', '· unordered source membership')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'No adjacency arrows. Physical, service and nonmanual scopes stay distinct; unresolved inputs block execution.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector.', 'Unordered source operation membership with separate physical, numerical, derived-analysis, explanatory and extension dispositions. Repeats retain their stated scopes without instantiation. Source access and closed-service boundaries remain explicit.')
    if f['id'] in ASSEMBLY_PACKAGES:
        result=result.replace('· every listed step', '· source template view')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'Unexpanded source templates. Choice arms remain exclusive; memberships, repeats and device ownership are not executions.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector.', 'Source template view with all physical configurations and separate numerical, device, external-input and reference scope. Memberships have no inferred chronology; typed beaded choices remain exclusive and counts unexpanded.')
    if f['id'] in ACOUSTIC_PACKAGES:
        result=result.replace('· every listed step', '· unordered membership')
        result=result.replace('Dashes = reference display order, not proven source chronology. Branch choices are not connected to each other.', 'No adjacency arrows. Physical, numerical, shared-preparation and campaign records remain distinct; nothing is executed.')
        result=result.replace('All operations in the first or designated complete reference route, plus the full branch index. Dashed connectors show authored reference order only. Loop bodies are shown once with original loop metadata in the interactive inspector.', 'Unordered operation membership for one physical design, with a complete index that labels numerical dispositions separately. Loop contracts are unexpanded metadata and missing inputs remain blocked.')
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
                if n.get('meta'): lines.append(indent+'  - Source occurrence binding: '+json.dumps(n['meta'],ensure_ascii=False,separators=(',',':')))
            else:
                lines.append(f'{indent}- **{n["type"].upper()}: {n["label"]}**')
                if n.get('meta'):lines.append(indent+'  - Binding: '+json.dumps(n['meta'],ensure_ascii=False,separators=(',',':')))
        lines.extend(['','<details><summary>Branch state, choices, lineage and loop obligations</summary>','', '```json',json.dumps({k:resolve(f,v) for k,v in r['detail'].items()},ensure_ascii=False,indent=2),'```','','</details>',''])
    lines.extend(['## Operation contracts','','Every operation is clickable in the offline inspector, with robot actions, target objects, pre/post state, provenance, unknowns and acceptance/recovery. Raw task JSON is the source of truth; this visualization is a public evaluator/reference view, not an agent prompt.',''])
    if f['id'] in MECHANICAL_PACKAGES:
        lines.extend(['## Reference contracts and boundaries', '', 'Representation counts: ' + json.dumps(f['summary_counts'], ensure_ascii=False) + '.', '',
          'All source JSON, dependency rules, controls, lineage, unknowns, source conflicts, unread-video gates and release boundaries remain exact. Numerical training is not physical self-updating hardware. Ring torque is derived semi-experimentally from matched measured force and geometry; it is not directly measured torque. Proposals and conceptual extensions remain separate from physical designs.', '',
          'Origami-memory memberships are unordered. Ring preparation, condition, trial and concurrent bodies preserve the source grammar without expanding missing counts. Backprop uses the authoritative typed reference tree with distinct forward/adjoint operation entries, transfer contracts and phase bindings. A displayed template is not a trial, specimen or completed result.', ''])
        for name, entry in f['source_files'].items(): lines.append(f'- [{name}]({entry["url"]})')
        lines.append('')
    if f['id'] in NATURE_MATERIALS_PACKAGES:
        lines.extend(['## Reference contracts and boundaries', '', 'Representation counts: ' + json.dumps(f['summary_counts'], ensure_ascii=False) + '.', '',
          f['source_warnings'], '',
          'Every source JSON document, operation field, branch record, preparation binding, unknown gate, source conflict, control, custody rule and access audit is retained. Navigation labels and view classifications are authored; original records and pointers remain authoritative. No unknown specimen, cycle or transfer count is instantiated, and no source outcome is actor-visible feedback or newly measured acceptance.', '',
          'Gear preparation is a separate once-per-allocated-object recipe. Per-condition lists preserve source-declared authored order and every TRANSFER destination without joining preparation, conditions or alternate reuse entries into one historical specimen trace. Numerical operations remain modeled; derived damping and comparison records require measured/control parents. Illustrative demonstrations never become physical trials.', '',
          'Hydrogel operation lists remain membership. Only declared branch lineage and the six-phase order within each service constrain order. Condition axes are not automatically crossed; source cycle counts do not supply independent specimens. Closed chemistry, laser, UV and thermal services expose no executable hazardous recipes. Four Extended Data captions do not close the image-access gap; accelerated sampled video never establishes real-time dynamics.', '',
          'No actor loader, task runner, physical simulation, scientific solver, new scene or robot execution is implemented.', ''])
        for name, entry in f['source_files'].items(): lines.append(f'- [{name}]({entry["url"]})')
        lines.append('')
    if f['id'] in FINAL_MATERIALS_PACKAGES:
        lines.extend(['## Reference contracts and boundaries', '', 'Representation counts: ' + json.dumps(f['summary_counts'], ensure_ascii=False) + '.', '',
          f['source_warnings'], '',
          'Every source JSON document, operation field, branch record, dependency, unknown gate, control, conditional postcondition, custody rule and access audit is retained. Lists remain membership; global loop catalogs apply only to their stated scopes. No empty loop, source inventory, truth-table case, technical readout or cycle is silently promoted to an independent specimen or completed experiment.', '',
          'ReMM remains source-incomplete with main panels and movie contents uninspected. Cold-shape hazardous processes remain inside qualified closed services; robot interface actions and autonomous service/analysis ownership remain distinct. Its two derived-fit navigation views retain the original numerical_or_analytical_only source classification and are not additional branches or independent validation.', '',
          'Horn physical/derived closure retains matched-map parents and physical cleanup. Numerical focusing and beam splitting never become physical acquisition. These projections implement no actor loader, physical simulation, trusted event backend, new scene or robot execution.', ''])
        for name, entry in f['source_files'].items(): lines.append(f'- [{name}]({entry["url"]})')
        lines.append('')
    if f['id'] in ASSEMBLY_PACKAGES:
        lines.extend(['## Reference contracts and boundaries', '', 'Representation counts: ' + json.dumps(f['summary_counts'], ensure_ascii=False) + '.', '',
          'All source JSON, scoped dependencies, preparation alternatives, controls, lineage, unknown inputs, factual parameters, source conflicts and access gates remain exact. These are static author/evaluator views. No fabricated chronology, sample count, measured outcome, solver run, robot execution or preparation credit is introduced.', '',
          'Granular and thermal configurations retain operation memberships once, with explicit causal constraints and symbolic repeats. Beaded views preserve the authoritative sequence/loop/choice/dispatch grammar and every occurrence binding. Mutually exclusive arms are displayed for inspection, never selected or concatenated into one specimen history. Conditional recovery remains conditional. Thermal scope sections have explicitly authored navigation IDs, not invented scientific branches.', ''])
        for name, entry in f['source_files'].items(): lines.append(f'- [{name}]({entry["url"]})')
        lines.append('')
    if f['id'] in ACOUSTIC_PACKAGES:
        lines.extend(['## Reference contracts and boundaries', '',
          'Representation counts: ' + json.dumps(f['summary_counts'], ensure_ascii=False) + '.', '',
          'The complete source contracts remain in the inspector, including unknown inputs, source conflicts, allocation/lineage, dependencies, actor allowlists and independent source audits. Numerical work is distinct from physical preparation and acquisition. All operation lists are membership; no chronology, new schedule, default value, sample count or observed result is inferred.', '',
          'This public author/evaluator inspector is not actor-safe input. No runtime projection, solver, task loader, physical simulation, new storyboard or robot execution is implemented.', ''])
        for name, entry in f['source_files'].items():
            lines.append(f'- [{name}]({entry["url"]})')
        lines.append('')
    if f['id']=='cooling':
        lines.extend(['## Reference contracts and boundaries','',
          'All 56 operations, 11 physical route leaves, 6 loop contracts and 14 unresolved input gates are retained. Each operation list is membership under explicit receipt dependencies, not a mandatory chronology. Symbolic loop metadata preserves original bodies, counts and nesting text without adding repeated operation occurrences or guessed schedules.','',
          'The three thermal-map conditions remain separate leaves. One white and one black device are paired conditions, not two independent replicates of each condition. Seven map channels, PID targets, angular observations and timepoints do not supply independent sample counts. Unknown allocation, technical repeats and sessions remain null.','',
          'Every actual station change still requires a qualified physical MOVE instance with carrier and identity receipts. Preparation or calibration must be performed or originate from an explicit documented handoff. Conditional gates stay conditional, including night versus daylight shading and current assembly revision. Device processes are separate from robot actions; completion evidence is a requirement, not an execution receipt.','',
          'No task loader, evaluator execution, physical simulation, scientific solver or robot controller is supplied. Models and application concepts remain nonmanual scope.',''])
        for key in ['dependencies','control_packages','unknown_parameters','source_conflicts','lineage_contract','episode_input_contract','agent_visible','RELEASE_BOUNDARY','evaluator_reference','independent_review/audit']:
            lines.append(f'- [{key.replace("_", " ")}]({f["source_files"][key+".json"]["url"]})')
        lines.append('')
    if f['id']=='emvp':
        lines.extend(['## Reference contracts and boundaries','',
          'All 53 templates, 19 configurations, 5 practical families, 15 comparison packages and 30 unresolved gates are inspectable. There is no additional whole-paper execution route. Single-material cage conditions retain three separate source routes. Control dimensions describe symbolic coverage without adding operation repetitions. Unknown specimen counts stay null; physical states, analysis regions and hardness sites are not independent specimens.','',
          'Operation completion evidence is not a post-state or execution receipt. Geometry, instrument qualification, source conflicts, lineage and external analysis handoffs remain open obligations. No physical simulation, actor projection or scientific backend is supplied.',''])
        for key in ['control_packages','unknown_parameters','source_conflicts','lineage_contract','episode_input_contract','agent_visible','RELEASE_BOUNDARY','evaluator_reference','independent_source_audit/audit']:
            lines.append(f'- [{key.replace("_", " ")}]({f["source_files"][key+".json"]["url"]})')
        lines.append('')
    if f['id']=='prismatic':
        lines.extend(['## Reference contracts and boundaries','',
          'This is an author/evaluator logical inspector. Operation lists are membership inventories, not a fixed solution. Null repetition counts remain blocked inputs. Conditional recovery is not a required normal step. The whole-paper configuration dispatches independent subcampaigns without merging identity or output claims.','',
          'All 49 operation templates, 12 configurations and 7 practical families are retained. Cube material × target coverage contains 16 scheduled cells, not 16 specimens or successful states. Thickness × target coverage remains blocked while its target list is null.',''])
        for key in ['control_packages','unknown_parameters','source_conflicts','lineage_contract','agent_visible','RELEASE_BOUNDARY','evaluator_reference','independent_source_audit/audit']:
            filename=key+'.json'
            lines.append(f'- [{key.replace("_", " ")}]({f["source_files"][filename]["url"]})')
        lines.append('')
        result='\n'.join(lines)
        return result.replace('numbered rows preserve reference-list occurrences.', 'rows show unordered template membership; only declared dependencies impose order.')
    result='\n'.join(lines)
    if f['id'] in NATURE_MATERIALS_PACKAGES:
        result=result.replace('numbered rows preserve reference-list occurrences. A loop body is shown once and must be repeated under its original binding, not treated as executed.', 'rows are authored navigation over exact source records. Gear recipes preserve source-declared authored order; hydrogel memberships have no adjacency order. Conditions and repeats are not expanded or executed.')
    if f['id'] in {*MECHANICAL_PACKAGES, *ASSEMBLY_PACKAGES, *FINAL_MATERIALS_PACKAGES}:
        result=result.replace('numbered rows preserve reference-list occurrences. A loop body is shown once and must be repeated under its original binding, not treated as executed.', 'rows retain the source display structure only. Membership has no inferred chronology. Where the source supplies a typed body, one unexpanded template is shown; no condition, trial or specimen count is inferred.')
    if f['id']=='cooling' or f['id'] in ACOUSTIC_PACKAGES:
        result=result.replace('numbered rows preserve reference-list occurrences. A loop body is shown once and must be repeated under its original binding, not treated as executed.', 'rows preserve source operation membership once, without chronology. Loop bodies, count text and nesting obligations are retained as metadata, not added occurrences or executed repetitions.')
    return result

def write_release_manifest():
    files=[]
    for path in sorted(ROOT.rglob('*')):
        relative=path.relative_to(ROOT)
        if (not path.is_file() or any(part.startswith('.') or part=='__pycache__' for part in relative.parts)
                or path.name in {'release_manifest.json','ScienceGym-Task-Explorer.html'}
                or path.suffix not in {'.md','.js','.json','.py','.html','.css','.svg'}):continue
        payload=path.read_bytes()
        files.append({'path':relative.as_posix(),'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()})
    (ROOT/'release_manifest.json').write_text(json.dumps({'source_commit':COMMIT,'source_commits':{key:source_commit(key) for key in ADAPTERS},
        'repository_destination':'viewer/task_explorer_v1/','files':files},indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--tasks',type=pathlib.Path,default=ROOT.parent.parent/'tasks');parser.add_argument('--only',choices=list(ADAPTERS));args=parser.parse_args()
    keys=[args.only] if args.only else list(ADAPTERS);manifest=[]
    for key in keys:
        f=unique_shared(ADAPTERS[key](args.tasks/package_name(key)))
        encoded=json.dumps(f,ensure_ascii=False,separators=(',',':'))
        (ROOT/'data'/f'{key}.json').write_text(encoded+'\n');(ROOT/'data'/f'{key}.js').write_text('window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA['+json.dumps(key)+']='+encoded+';\n')
        (ROOT/'diagrams'/f'{key}.svg').write_text(svg(f));(ROOT/'docs'/f'{key}.md').write_text(md(f))
        manifest.append({'id':key,'operations':len(f['operations']),'routes':len(f['routes']),'bytes':len(encoded.encode())})
        print(manifest[-1])
    if args.only:
        manifest=[]
        for key in ADAPTERS:
            data_path=ROOT/'data'/f'{key}.json'
            if not data_path.exists():raise ValueError('Build all families before using --only')
            f=json.loads(data_path.read_text())
            manifest.append({'id':key,'operations':len(f['operations']),'routes':len(f['routes']),
                             'bytes':len(data_path.read_bytes().rstrip(b'\n'))})
    (ROOT/'manifest.json').write_text(json.dumps({'commit':COMMIT,'source_commits':{key:source_commit(key) for key in ADAPTERS},'families':manifest},indent=2)+'\n')
    write_release_manifest()
if __name__=='__main__':main()
