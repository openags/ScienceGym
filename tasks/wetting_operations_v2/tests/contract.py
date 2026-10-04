"""Original bounded synthetic contracts. No instruments, source data or scientific solver."""
from copy import deepcopy
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, math
ROOT=Path(__file__).resolve().parents[1]
def read(n): return json.loads((ROOT/n).read_text())
OPS={x['id']:x for x in read('operations.json')['operations']}
BRANCHES={x['id']:x for x in read('branches.json')['branches']}
CONFLICTS={x['id']:x for x in read('source_conflicts.json')['conflicts']}
UNKNOWNS={x['id']:x for x in read('unknown_parameters.json')['unknowns']}
CONTEXT=tuple(read('lineage_contract.json')['context_keys'])
OUTCOMES=('METADATA_OK','QUALIFICATION_HOLD','DATA_HOLD','ISOLATION_HOLD')
FIXTURE_IDS=tuple(r+':'+out for r in BRANCHES for out in OUTCOMES)
class ContractError(ValueError):pass
def require(ok,msg):
 if not ok: raise ContractError(msg)
def finite(v):
 require(type(v) in (int,float),'finite real number required, excluding bool')
 try:x=float(v)
 except (OverflowError,ValueError):raise ContractError('number overflow')
 require(math.isfinite(x),'nonfinite number');return x
def string(v):require(type(v) is str and bool(v),'nonempty identifier');return v
def exact(record,keys):require(type(record) is dict and set(record)==set(keys),'exact record fields required')
def strict(v):
 if type(v) is dict:
  require(all(type(k) is str for k in v),'string keys required')
  for x in v.values():strict(x)
 elif type(v) is list:
  for x in v:strict(x)
 elif type(v) is float:finite(v)
 elif type(v) in (str,bool,int) or v is None:pass
 else:raise ContractError('JSON type required')
def canonical(v):
 try:strict(v);return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)
 except (ValueError,TypeError,OverflowError,RecursionError) as exc:raise ContractError(str(exc))
def digest(v):return hashlib.sha256(canonical(v).encode()).hexdigest()
def scope_holds(operation_id,active_tags,include_qualification=True):
 require(operation_id in OPS,'unknown operation');require(type(active_tags) is list and all(type(t) is str for t in active_tags) and len(active_tags)==len(set(active_tags)),'unique scope tags')
 op=OPS[operation_id]
 return {'conflicts':[c for c in op['conflict_ids'] if set(CONFLICTS[c]['scope_tags']) & set(active_tags)],'qualification':[u for u in op['unknown_ids'] if not UNKNOWNS[u].get('scope_tags') or set(UNKNOWNS[u]['scope_tags']) & set(active_tags)] if include_qualification else [],'safe_closeout_always_reachable':True,'permission_to_execute':False}
def route_ancestors(route,material):
 require(route in BRANCHES and material in ('PDMS','CY','MULTI'),'route/material')
 families=BRANCHES[route]['family_scope'];require(material in families or (material=='MULTI' and len(families)>1),'material incompatible with route')
 found=set();visited=set()
 def visit(r,mat):
  if (r,mat) in visited:return
  visited.add((r,mat))
  for d in BRANCHES[r]['depends_on']:
   if r=='R03' and ((mat=='PDMS' and d=='R02') or (mat=='CY' and d=='R01')):continue
   allowed=BRANCHES[d]['family_scope'];child_mat=mat if mat in allowed or (mat=='MULTI' and len(allowed)>1) else allowed[0]
   if d=='R12':child_mat='MULTI'
   found.add(d);visit(d,child_mat)
 if route!='R15':visit(route,material)
 return sorted(found)
def macro_origin(record):
 exact(record,('cohort','time_s','volume_nL','evidence_kind','synthetic_only'))
 require(record['cohort']=='macro','55 nL origin restricted to macro cohort');require(record['evidence_kind']=='synthetic_observation' and record['synthetic_only'] is True,'synthetic fixture observation only')
 t=record['time_s'];v=record['volume_nL'];require(type(t) is list and type(v) is list and len(t)==len(v) and len(t)>=2,'paired time/volume arrays')
 t=[finite(x) for x in t];v=[finite(x) for x in v];require(all(x>0 for x in v),'positive volumes');require(all(b>a for a,b in zip(t,t[1:])),'strict timestamps')
 require(v[0]>=55,'placed record starts below macro analysis origin')
 exact_indices=[i for i,x in enumerate(v) if x==55]
 require(len(exact_indices)<=1,'ambiguous repeated threshold observations')
 crossings=[i for i in range(len(v)-1) if v[i]>55 and v[i+1]<55]
 require(len(crossings)+len(exact_indices)==1,'exactly one recorded downward crossing required')
 if exact_indices:
  i=exact_indices[0];require((i==0 or v[i-1]>55) and (i==len(v)-1 or v[i+1]<55),'crossing direction');bracket=[t[i],t[i]]
 else:i=crossings[0];bracket=[t[i],t[i+1]]
 return {'origin_bracket_s':bracket,'exact_origin_observed':bracket[0]==bracket[1],'interpolated_timestamp':None,'synthetic_only':True}
def stack_timing(record):
 exact(record,('stack_id','start_s','end_s','plane_time_s','z_um','side_time_s','environment_interval_s','sync_tolerance_s','synthetic_only'))
 string(record['stack_id']);require(record['synthetic_only'] is True,'synthetic only')
 start,end,tol=map(finite,(record['start_s'],record['end_s'],record['sync_tolerance_s']));require(math.isfinite(end-start),'finite derived duration');require(start>=0 and end>start and tol>=0,'ordered scan bounds and nonnegative supplied tolerance')
 t,z,side=(record[k] for k in ('plane_time_s','z_um','side_time_s'));require(all(type(x) is list for x in (t,z,side)) and len(t)==len(z)>=2 and len(side)>0,'plane records and side times')
 t,z,side=[[finite(v) for v in arr] for arr in (t,z,side)];require(all(b>a for a,b in zip(t,t[1:])),'ordered plane times');require(all(b>a for a,b in zip(z,z[1:])) or all(b<a for a,b in zip(z,z[1:])),'strict scan direction');require(start<=t[0] and t[-1]<=end,'planes within scan interval')
 require(all(b>a for a,b in zip(side,side[1:])),'ordered side times');require(all(min(abs(p-s) for s in side)<=tol for p in t),'side/plane synchronization exceeds qualified tolerance')
 env=record['environment_interval_s'];require(type(env) is list and len(env)==2,'environment interval');a,b=map(finite,env);require(a<=start<end<=b,'environment does not cover whole stack')
 return {'duration_s':end-start,'instantaneous':False,'plane_count':len(t),'scientific_resolution_validated':False}
def repeat_ledger(rows):
 require(type(rows) is list and len(rows)>0,'nonempty ledger');droplets={};points=set();samples=set();spots=set()
 for row in rows:
  exact(row,('sample_id','spot_id','droplet_id','timepoint_id','cohort_id'))
  for v in row.values():string(v)
  d=row['droplet_id'];parent=(row['sample_id'],row['spot_id']);require(d not in droplets or droplets[d]==parent,'droplet parentage changed');droplets[d]=parent
  key=(d,row['timepoint_id']);require(key not in points,'duplicated timepoint / cross-cohort double count');points.add(key);samples.add(row['sample_id']);spots.add(parent)
 return {'distinct_droplets':len(droplets),'distinct_samples':len(samples),'distinct_spots':len(spots),'timepoints':len(points),'statistical_independence_established':False,'source_cohort_overlap_resolved':False}
def coordinate_layers(rows):
 require(type(rows) is list and rows,'coordinate rows');ids=set();kinds={}
 for row in rows:
  exact(row,('point_id','kind','xyz_m','raw_parent_id','method_revision','directly_measured'))
  pid=string(row['point_id']);require(pid not in ids,'duplicate point ID');ids.add(pid);kind=row['kind'];require(kind in ('observed','manual_annotation','imputed','inferred_reference'),'coordinate kind');string(row['raw_parent_id']);string(row['method_revision'])
  require(type(row['xyz_m']) is list and len(row['xyz_m'])==3,'three coordinates');[finite(v) for v in row['xyz_m']]
  require(type(row['directly_measured']) is bool and row['directly_measured']==(kind=='observed'),'imputed/inferred/annotated field cannot become direct observation');kinds[pid]=kind
 return kinds
def marker_correspondence(record):
 exact(record,('array_id','pairs','boundary_evidence_id','boundary_stationary','synthetic_only'));string(record['array_id']);string(record['boundary_evidence_id']);require(record['synthetic_only'] is True and record['boundary_stationary'] is True,'qualified synthetic stationary boundary required')
 pairs=record['pairs'];require(type(pairs) is list and len(pairs)>=3,'at least three declared correspondences');left=[];right=[]
 for p in pairs:
  require(type(p) is list and len(p)==2,'matching pair');left.append(string(p[0]));right.append(string(p[1]))
 require(len(set(left))==len(left) and len(set(right))==len(right),'matching must be one-to-one')
 return {'pair_count':len(pairs),'reference_kind':'inferred_reference','captured_reference_image':False,'graph_solver_executed':False}
def angle_comparison(record):
 exact(record,('theta_star_rad','psi_rad','theta_r_rad','theta_r_kind','psi_fit_field','displacement_fit_fields','synthetic_only'))
 require(record['synthetic_only'] is True,'synthetic only');a,p,r=map(finite,(record['theta_star_rad'],record['psi_rad'],record['theta_r_rad']));require(0<=a<=math.pi and 0<=r<=math.pi and -math.pi<=p<=math.pi,'radian range')
 require(record['psi_fit_field']=='P1_current_placement','surface tangent must use current placement P1');require(record['displacement_fit_fields']==['Ur','Uz'],'separate displacement fits');require(record['theta_r_kind'] in ('synthetic_independent_reference','source_reference_only'),'reference evidence kind')
 model=r-p;residual=a-model;require(math.isfinite(model) and math.isfinite(residual),'finite angle output')
 return {'model_theta_r_minus_psi_rad':model,'residual_rad':residual,'comparison_kind':'source_reference_model' if record['theta_r_kind']=='source_reference_only' else 'synthetic_independent_reference_model','new_measurement_gate_satisfied':False,'observed_depinning':False}
def traction_area(record):
 exact(record,('tractions_Pa','triangle_areas_m2','area_measure','window_policy_id','conflict_dispositions','sector_angle_rad','synthetic_only'))
 require(record['synthetic_only'] is True,'synthetic only');require(record['area_measure'] in ('reference_physical_area','deformed_physical_area'),'explicit physical area measure');string(record['window_policy_id'])
 require(record['conflict_dispositions']=={'C02':'synthetic_scope_choice','C03':'synthetic_dimensional_audit'},'both integration conflicts require explicit synthetic dispositions')
 t,a=record['tractions_Pa'],record['triangle_areas_m2'];require(type(t) is list and type(a) is list and len(t)==len(a)>0,'one area per traction');angle=finite(record['sector_angle_rad']);require(0<angle<=2*math.pi,'bounded positive sector angle')
 values=[]
 for tr,area in zip(t,a):
  require(type(tr) is list and len(tr)==3,'traction vector');tr=[finite(v) for v in tr];area=finite(area);require(area>0,'positive physical triangle area');v=math.hypot(*tr)*area;require(math.isfinite(v),'finite traction-area product');values.append(v)
 try:total=math.fsum(values)
 except OverflowError:raise ContractError('integration overflow')
 require(math.isfinite(total),'finite integral');return {'sum_magnitude_times_area':total,'unit':'N','sector_angle_rad':angle,'equilibrium_force_balance_established':False,'scientific_model_validated':False}
def age_eligibility(record):
 exact(record,('material_family','cure_utc','experiment_utc','storage_receipt_id','custody_basis','synthetic_only'))
 require(record['synthetic_only'] is True,'synthetic fixture only');require(record['material_family'] in ('PDMS','CY'),'known family');string(record['storage_receipt_id']);require(record['custody_basis']=='synthetic_dated_custody','file timestamp or simulated timer cannot certify custody')
 times=[]
 for key in ('cure_utc','experiment_utc'):
  try:t=datetime.fromisoformat(record[key].replace('Z','+00:00'))
  except (ValueError,TypeError,AttributeError):raise ContractError('ISO custody timestamp')
  require(t.tzinfo is not None and t.utcoffset().total_seconds()==0,'explicit UTC time');times.append(t)
 weeks=(times[1]-times[0]).total_seconds()/(7*86400);minimum=1 if record['material_family']=='PDMS' else 2
 return {'eligible_synthetic_window':minimum<=weeks<=3,'age_weeks':weeks,'real_storage_qualified':False}
def humidity_semantics(record):
 exact(record,('setpoint_percent','measured_percent','stability_pp','sensor_accuracy_pp','claimed_absolute_accuracy_pp','synthetic_only'))
 require(record['synthetic_only'] is True,'synthetic only');s,m,st,ac,cl=[finite(record[k]) for k in ('setpoint_percent','measured_percent','stability_pp','sensor_accuracy_pp','claimed_absolute_accuracy_pp')]
 require(0<=s<=100 and 0<=m<=100 and st>=0 and ac>0 and cl>=ac,'humidity domain or unsupported absolute accuracy claim')
 return {'stability_distinct_from_accuracy':True,'absolute_accuracy_validated':False}
def retry_lineage(before,after):
 keys=('attempt_id','sample_id','spot_id','droplet_id','acquisition_id','qualified_spot_receipt','previous_failure_id')
 for r in (before,after):
  exact(r,keys)
  for x in r.values():string(x)
 for k in ('attempt_id','spot_id','droplet_id','acquisition_id','qualified_spot_receipt'):require(before[k]!=after[k],'retry must not reuse '+k)
 require(before['previous_failure_id']==after['previous_failure_id'],'prior failure must remain linked');return {'prior_failure_retained':True,'physical_retry_executed':False}
def fixture(fid):
 require(type(fid) is str and fid in FIXTURE_IDS,'evaluator-selected known fixture required');route,out=fid.split(':');ctx={k:fid+':'+k for k in CONTEXT};ctx['route_id']=route;ctx['material_id']=BRANCHES[route]['family_scope'][0] if len(BRANCHES[route]['family_scope'])==1 else 'MULTI';ctx['sample_id']=fid+':campaign_bundle_not_specimen';ctx['scope_tags']=sorted({s for c in CONFLICTS.values() if route in c['route_ids'] for s in c['scope_tags']})
 events=[];registry={};last=None
 def add(op,role=None,payload=None):
  nonlocal last
  n=len(events)+1;eid=fid+':E'+str(n);rid=fid+':REC'+str(n);data={'synthetic_only':True,'physical_qualified':False,'physical_execution':False,'source_outcome_used':False,'status':out,'record_type':OPS[op]['required_record_type']}
  if payload:data.update(payload)
  data['constituent_lineages']=[{'material_id':m,'sample_id':fid+':'+m+':sample','spot_id':fid+':'+m+':spot','droplet_id':fid+':'+m+':droplet','preparation_ancestry':route_ancestors(op[:3],m.split('_')[0]),'synthetic_only':True,'independent_specimen_count':None} for m in OPS[op]['material_ids']]
  record={'evidence_id':rid,'operation_id':op,'context':deepcopy(ctx),'role':role or OPS[op]['evidence_role'],'depends_on':[last] if last else [],'payload':data};registry[rid]=record;events.append({'event_id':eid,'operation_id':op,'evidence_id':rid});last=rid
 if route!='R15':
  operations=BRANCHES[route]['route_operation_ids']
  count=1 if out=='QUALIFICATION_HOLD' else max(1,len(operations)//2) if out=='DATA_HOLD' else len(operations)
  for op in operations[:count]:add(op,payload={'upstream_ancestry':route_ancestors(route,ctx['material_id']),'disposition':'metadata_only_no_real_qualification' if out=='METADATA_OK' else 'held_or_failed','scope_hold':scope_holds(op,ctx['scope_tags'])})
 # Safety path is independent of missing normal scientific ancestors; never creates observations.
 add('R15_O01',payload={'safe_release_observed_synthetic':out!='ISOLATION_HOLD','disposition':'held_contained' if out=='ISOLATION_HOLD' else 'isolated_synthetic'})
 add('R15_O02',payload={'physical_removed':False,'disposition':'held_contained' if out=='ISOLATION_HOLD' else 'custody_metadata_only'})
 add('R15_O03',payload={'attempts_preserved':True,'archive_payload_hash':digest({'fixture':fid,'outcome':out,'observed_operation_ids':[x['operation_id'] for x in events]})})
 add('R15_O04',payload={'route_status':'synthetic_metadata_complete' if out=='METADATA_OK' else 'held','unattempted_routes':[r for r in BRANCHES if r not in (route,'R15')],'whole_paper_execution_complete':False})
 return {'fixture_id':fid,'context':ctx,'events':events,'registry':registry,'registry_digest':digest(registry)}
def evaluate(events,registry,expected_fixture_id):
 expected=fixture(expected_fixture_id);require(type(events) is list and type(registry) is dict,'events and evaluator registry required');require(canonical(registry)==canonical(expected['registry']),'registry is not evaluator-pinned finite evidence');require(len(events)==len(expected['events']),'missing/extra event occurrence')
 target={e['event_id']:e for e in expected['events']};seen=set();records_seen=set()
 for event in events:
  exact(event,('event_id','operation_id','evidence_id'))
  for x in event.values():string(x)
  eid=event['event_id'];require(eid in target and eid not in seen,'unknown or duplicate occurrence');require(event==target[eid],'operation/evidence/occurrence mismatch');receipt=registry[event['evidence_id']];require(set(receipt['depends_on'])<=records_seen,'dependency order violated');require(receipt['context']==expected['context'],'context mismatch');require(receipt['role']==OPS[event['operation_id']]['evidence_role'],'request is not observation')
  seen.add(eid);records_seen.add(event['evidence_id'])
 return {'contract_passed':True,'synthetic_route_metadata_complete':expected_fixture_id.endswith(':METADATA_OK'),'safe_closeout_accounted_for':True,'whole_paper_execution_complete':False,'physical_execution':False,'physical_simulation':False,'scientific_reproduction':False,'validated_runnable_whole_paper_tasks':0,'source_data_reanalysis':False}
