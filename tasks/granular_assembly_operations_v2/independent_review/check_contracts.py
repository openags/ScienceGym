import json, pathlib, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
D={p.stem:json.loads(p.read_text()) for p in ROOT.glob('*.json')}
O={x['id']:x for x in D['operations']['operations']}; C={x['id']:x for x in D['branches']['configurations']}; R={x['configuration_id']:x for x in D['dependencies']['routes']}
S={x['id'] for x in D['station_contracts']['stations']}; U={x['id'] for x in D['unknown_parameters']['unknowns']}; P={x['id'] for x in D['provenance']['references']}; K={x['id'] for x in D['control_packages']['control_packages']}
checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
def reach(edges,a,b):
 seen={a};pending=[a]
 while pending:
  n=pending.pop()
  for x,y in edges:
   if x==n and y not in seen:seen.add(y);pending.append(y)
 return b in seen
def acyclic(nodes,edges):
 incoming={n:0 for n in nodes};adj={n:[] for n in nodes}
 for a,b in edges:
  if a not in incoming or b not in incoming:return False
  incoming[b]+=1;adj[a].append(b)
 q=[n for n,v in incoming.items() if not v];n=0
 while q:
  x=q.pop();n+=1
  for y in adj[x]:
   incoming[y]-=1
   if not incoming[y]:q.append(y)
 return n==len(nodes)
check('All operation station references resolve', all(o['station'] in S for o in O.values()))
check('All operation source references resolve',all(set(o['source_refs'])<=P for o in O.values()))
check('All operation input gates resolve',all(set(o['required_unknowns'])<=U for o in O.values()))
check('Every configuration resolves operations and controls',all(set(c['operation_ids'])<=O.keys() and set(c['control_package_ids'])<=K for c in C.values()))
check('Every configuration has a route',set(C)==set(R))
check('All route and arm graphs are acyclic and reference local nodes',all(acyclic(r['suggested_operation_ids'],r['causal_edges']) and all(acyclic(a['operation_ids'],a['causal_edges']) for a in r.get('arm_routes',[])) for r in R.values()))
fields=['actor','manipulated_objects_and_tools','robot_actions','preconditions','completion_evidence','source_station','target_station','completion_state']
check('Every physical operation has actor/object/tool/precondition/evidence fields',all(all(o.get(f) for f in fields) for o in O.values() if o['kind']!='analysis_handoff'))
check('Robot and device actions are separate',all(isinstance(o.get('device_actions'),list) for o in O.values()))
check('Fabrication includes actual manipulations',all(len(O[x]['robot_actions'])>=3 for x in ['SANDWICH','FILM','COAT','CUSTOM_PARTICLES','GUIDE_FAB']))
a=R['TRAPPED_COLLISION']['arm_routes']; s=next(x for x in a if x['arm']=='Stage1trapped');t=next(x for x in a if x['arm']=='shape_adaptedtrapped')
check('Stage1 collision excludes prior postcure', 'POSTCURE' not in s['operation_ids'] and 'postcured' in s['forbidden_prior_states'])
check('Adapted collision has cure then baseline then impact',reach(t['causal_edges'],'POSTCURE','COLLISION_BASELINE') and reach(t['causal_edges'],'COLLISION_BASELINE','COLLIDE_TRAPPED'))
check('Both collision arms have distinct baseline and postimage',all(reach(x['causal_edges'],'COLLISION_BASELINE','COLLIDE_TRAPPED') and reach(x['causal_edges'],'COLLIDE_TRAPPED','IMAGE') for x in a))
check('Free-fall observation follows event',reach(R['FREEFALL_SURFACES']['causal_edges'],'DROP_BEAD','IMAGE'))
check('Patterned surface is verified before collision',reach(R['SURFACE_TRIO']['causal_edges'],'VERIFY_TRAPS','DROP_BEAD'))
check('PUF analysis is downstream of actual acquisition and geometry',reach(R['PUF_HIERARCHY']['causal_edges'],'AUTH_IMAGE','CONTACT_ANALYSIS') and reach(R['PUF_HIERARCHY']['causal_edges'],'CONTACT_ANALYSIS','AUTH_ANALYSIS'))
check('Stability baseline/challenge/postimage lineage ordered',all(reach(R[r]['causal_edges'],'COAT','BASELINE') and reach(R[r]['causal_edges'],'BASELINE',op) and reach(R[r]['causal_edges'],op,'REIMAGE') for r,op in [('STABILITY_CONTAMINATION','CONTAMINATE'),('STABILITY_DROP','DROP_ARRAY'),('STABILITY_SONICATION','SONICATE'),('STABILITY_AGING','AGE')]))
check('Custom particles manufactured before charge and acquired before analysis',all(reach(R[r]['causal_edges'],'CUSTOM_PARTICLES','WEIGH_CHARGE') and reach(R[r]['causal_edges'],'IMAGE','FLUORESCENCE') and reach(R[r]['causal_edges'],'FLUORESCENCE','CONTACT_ANALYSIS') for r in ['SHAPED_HARD_PUA','SHAPED_SOFT_PUA']))
check('Reuse record precedes reset',reach(R['TRAP_REUSE']['causal_edges'],'IMAGE','REUSE_RESET'))
check('Destructive remnant acquisition follows removal',all(reach(R[r]['causal_edges'],'IMAGE','REMOVE_BEADS') and reach(R[r]['causal_edges'],'REMOVE_BEADS','SEM_EDS') for r in ['INTERFACE_SEM','RESIN_TRANSFER_EDS']))
check('Known source conflicts retained',{'C_BEAD_SIZE','C_YSZ_ENERGY','C_DOSE_UNITS','C_STABILITY_LOCATOR','C_UNIVERSAL_POSTCURE'}<={x['id'] for x in D['source_conflicts']['conflicts']})
check('No physical execution or scientific validation claimed',not D['RELEASE_BOUNDARY']['robot_execution'] and not D['RELEASE_BOUNDARY']['scientific_validation'] and not D['RELEASE_BOUNDARY']['physics_execution'])
check('Actor projection excludes future source outcomes',any('source_outcomes' in x for x in D['agent_visible']['exclude']) and D['RELEASE_BOUNDARY']['loader_implemented'] is False)
check('Unread movies/data and source bytes caveats remain',len(D['source_access_audit']['sources_unread'])>=7 and next(x for x in D['provenance']['sources'] if x['id']=='MAIN')['sha256'] is None)
result={'scope':'Independent static design-contract checks; not physical execution, real instrument authentication, scientific replication or runtime-loader validation.','passed':sum(x['passed'] for x in checks),'total':len(checks),'checks':checks,'input_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.json') if p.name not in ['STATUS.json','EXPORT_ALLOWLIST.json']}}
(ROOT/'independent_review/contract_check_results.json').write_text(json.dumps(result,indent=2));print(json.dumps({'passed':result['passed'],'total':result['total'],'failures':[x['check'] for x in checks if not x['passed']]},indent=2));raise SystemExit(not all(x['passed'] for x in checks))
