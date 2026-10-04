"""Independent contract mutation and pure in-memory semantic tests; no external action."""
import argparse, copy, hashlib, importlib.util, json, re, struct, sys, unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--source-review',type=Path,required=True);parser.add_argument('--paired-task',type=Path,required=True);args=parser.parse_args();sys.argv=sys.argv[:1]
SOURCE=args.source_review;TASK=args.paired_task
spec=importlib.util.spec_from_file_location('independent_guard_target',P/'semantic_controls.py');mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
G=mod.StaticSceneGuard;Rejected=mod.GuardRejected
j=lambda p:json.loads(p.read_text())
FILES=['asset_metadata.json','requirements_snapshot.json','unknowns_snapshot.json','source_conflicts_snapshot.json','branches_snapshot.json','source_facts_snapshot.json','stations_snapshot.json','operation_bindings.json','operation_binding_contract.json','asset_inventory.json','affordances.json','specimen_geometry.json','states.json']
DATA={f:j(P/f) for f in FILES}
def require(ok,message):
    if not ok:raise ValueError(message)
def validate(d,plan):
    require(d['asset_metadata.json']['physical_execution_enabled'] is False,'execution flag')
    require(d['asset_metadata.json']['completed_conversion_increment']==0,'completion claim')
    require(d['asset_metadata.json']['scientific_result_reproduced'] is False,'scientific claim')
    require(d['states.json']['physical_execution_enabled'] is False,'state flag')
    req=d['requirements_snapshot.json']['assets'];ids={a['id'] for a in req}
    require(ids=={f'A{i:02}' for i in range(1,13)} and len(req)==12,'asset set')
    inv=d['asset_inventory.json']['assets'];require({a['id'] for a in inv}==ids and len(inv)==12,'inventory families')
    owners={o['name']:a['id'] for a in inv for o in a['objects']};names=[o['name'] for a in inv for o in a['objects']];require(len(names)==len(set(names)),'object duplicate')
    for a in inv:
        require(a['root']=='ASSET.'+a['id'] and a['root'] in names,'asset root')
    anchors=d['affordances.json']['anchors'];anames=[a['name'] for a in anchors];require(len(anames)==len(set(anames)),'anchor duplicate')
    amap={a['name']:a for a in anchors}
    require(all(a['qualified_pose'] is False and a['physical_execution_enabled'] is False for a in anchors),'anchor qualification boundary')
    require(d['affordances.json']['semantic_only'] is True,'semantic boundary')
    for a in req:
        for n in a['required_semantic_anchors']:require('ANCHOR.'+a['id']+'.'+n in amap,'required anchor')
    expected={f'ANCHOR.R{i:02}.{r}' for i in range(1,17) for r in ['primary','control']}
    require({n for n in anames if re.fullmatch(r'ANCHOR\.R\d\d\.(primary|control)',n)}==expected,'operation selector set')
    rows=d['operation_bindings.json']['bindings'];require(rows==d['operation_binding_contract.json']['operations'],'contract binding mismatch')
    require({r['operation_id'] for r in rows}=={f'R{i:02}' for i in range(1,17)} and len(rows)==16,'operation set')
    paired={r['operation_id']:r for r in plan['operation_bindings']}
    for r in rows:
        require(r['physical_execution_enabled'] is False and r['qualified_pose'] is None,'qualified binding')
        p=paired[r['operation_id']]
        require(r['asset_ids']==p['asset_ids'],'paired asset assignment')
        require(p['root_node_ids']==['ASSET.'+x for x in r['asset_ids']],'paired roots')
        require(p['anchor_ids']==[r['primary_anchor'],r['control_anchor']],'paired anchor assignment')
        require(p['physical_qualified'] is False,'paired physical claim')
        require(p['primary_asset_id']==r['primary_asset_id'],'paired primary asset')
        require(p['primary_target']==r['primary_target'] and p['control_target']==r['control_target'],'paired target mesh')
        for role in ['primary','control']:
            a=amap[r[role+'_anchor']]
            require(r[role+'_target'] in names,'missing target')
            require(owners[r[role+'_target']]==r['primary_asset_id'],'target owner')
            require(a['target_mesh']==r[role+'_target'],'anchor target mismatch')
            require(a['owner']==r['primary_asset_id'],'anchor owner mismatch')
            require(p['anchor_positions_m'][a['name']]==a['position_m'],'paired anchor coordinates')
            require(a['qualified_pose'] is False and a['physical_execution_enabled'] is False,'anchor permission')
    unknown=d['unknowns_snapshot.json']['unknowns'];require({x['id'] for x in unknown}=={f'U{i:02}' for i in range(1,17)} and len(unknown)==16,'unknown set')
    require(all(x['execution_blocking'] is True for x in unknown),'unknown execution gates')
    conflict=d['source_conflicts_snapshot.json']['conflicts'];require({x['id'] for x in conflict}=={f'C{i:02}' for i in range(1,6)} and len(conflict)==5,'conflict set')
    b={b['id']:b for b in d['branches_snapshot.json']['branches']};require(set(b)=={f'B{i:02}' for i in range(1,10)},'branch set')
    require(all(b[i]['classification'].endswith('_unexecuted') for i in ['B04','B05','B07','B08']),'symbolic branch execution')
    g=d['specimen_geometry.json'];require(g['square_and_pad_count']==480 and g['square_rotation_deg']==20 and g['source_mesh_or_code_used'] is False and g['solid_material_simulated'] is False,'geometry boundary')
    require(g['source_nominal_dimensions_mm']=={'length':306,'width':64,'height':40,'square_side':4.8,'hinge':.2,'pad_side':3.6,'square_counts':[48,10]},'source dimensions')
PLAN=j(TASK/'asset_binding_plan.json')
FIELDS={'mechanics':['commissioned_limits','calibrated_loadcell','contact_zero','fixture_locked','safe_stop_policy'],'camera':['scale_distortion','focus_visibility','reference_frame','pad_identity_mask'],'sync':['clock_mapping','capture_ready','buffer_ready','load_unload_tags'],'plan':['frozen_repeat_policy','order_policy','recovery_policy','stopping_policy']}
def docked():
    g=G();g.prepare(specimen='independent-sample',geometry_revision='authored-display',build_receipt='test-build',fixture_receipt='test-fixture',treatment_revision='none');g.dock(specimen=g.specimen,carrier='carrier',branch='B03',grasp_zone='carrier.handle_right',supported=True);return g
def receipt(g,kind,fields=None):
    return dict(kind=kind,specimen=g.specimen,carrier=g.carrier,branch=g.branch,epoch=g.epoch,test_only=True,fields=fields if fields is not None else {k:True for k in FIELDS[kind]})
def qualified():
    g=docked()
    for kind in FIELDS:g.record_test_receipt(**receipt(g,kind))
    return g
class PackageChecks(unittest.TestCase):
    def test_actual_package_and_paired_selectors(self):validate(DATA,PLAN)
    def test_exact_accepted_snapshots(self):
        for dest,source in [('requirements_snapshot.json','asset_requirements.json'),('source_facts_snapshot.json','source_facts.json'),('unknowns_snapshot.json','unknowns.json'),('source_conflicts_snapshot.json','source_conflicts.json'),('branches_snapshot.json','branches.json'),('stations_snapshot.json','station_contracts.json')]:
            with self.subTest(snapshot=dest):self.assertEqual(DATA[dest],j(SOURCE/source))
    def test_paired_operation_assets(self):
        task_ops={o['id']:o for o in j(TASK/'operations.json')['operations']}
        for r in DATA['operation_bindings.json']['bindings']:
            with self.subTest(operation=r['operation_id']):self.assertEqual(task_ops[r['operation_id']]['asset_ids'],r['asset_ids'])
    def test_glb_container_integrity_no_external_resources(self):
        raw=(P/'geometry/conformal_lab.glb').read_bytes();magic,version,total=struct.unpack_from('<4sII',raw);self.assertEqual((magic,version,total),(b'glTF',2,len(raw)))
        size,kind=struct.unpack_from('<I4s',raw,12);self.assertEqual(kind,b'JSON');doc=json.loads(raw[20:20+size]);self.assertEqual(len(doc['scenes']),1);self.assertNotIn('images',doc)
        for buf in doc.get('buffers',[]):self.assertNotIn('uri',buf)
        self.assertFalse(doc.get('animations'));self.assertFalse(doc.get('cameras'))
    def test_reject_mutated_packages(self):
        mutations=[('missing_unknown',lambda d:d['unknowns_snapshot.json']['unknowns'].pop()),('closed_unknown',lambda d:d['unknowns_snapshot.json']['unknowns'][0].update(execution_blocking=False)),('missing_conflict',lambda d:d['source_conflicts_snapshot.json']['conflicts'].pop()),('physical_execution',lambda d:d['asset_metadata.json'].update(physical_execution_enabled=True)),('completion_increment',lambda d:d['asset_metadata.json'].update(completed_conversion_increment=1)),('science_claim',lambda d:d['asset_metadata.json'].update(scientific_result_reproduced=True)),('missing_asset',lambda d:d['asset_inventory.json']['assets'].pop()),('missing_anchor',lambda d:d['affordances.json']['anchors'].pop()),('duplicate_anchor',lambda d:d['affordances.json']['anchors'].append(d['affordances.json']['anchors'][0])),('qualified_anchor',lambda d:d['affordances.json']['anchors'][0].update(qualified_pose=True)),('wrong_binding',lambda d:d['operation_bindings.json']['bindings'][0].update(primary_target='missing')),('symbolic_becomes_physical',lambda d:d['branches_snapshot.json']['branches'][3].update(classification='physical_experiment')),('source_scalar_drift',lambda d:d['specimen_geometry.json']['source_nominal_dimensions_mm'].update(length=300)),('source_mesh_used',lambda d:d['specimen_geometry.json'].update(source_mesh_or_code_used=True))]
        for name,mutate in mutations:
            with self.subTest(mutation=name):
                d=copy.deepcopy(DATA);mutate(d)
                with self.assertRaises(ValueError):validate(d,PLAN)
    def test_reject_paired_selector_drift(self):
        for field,value in [('asset_ids',['A01']),('anchor_ids',['ANCHOR.R02.primary','ANCHOR.R02.control']),('root_node_ids',['ASSET.A01']),('physical_qualified',True),('primary_asset_id','A01'),('primary_target','missing'),('control_target','missing'),('anchor_positions_m',{'ANCHOR.R01.primary':[0,0,0],'ANCHOR.R01.control':[0,0,0]})]:
            p=copy.deepcopy(PLAN);p['operation_bindings'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):validate(DATA,p)
class IndependentSemantics(unittest.TestCase):
    def test_each_required_field_and_truthy_substitute_rejected(self):
        for kind,fields in FIELDS.items():
            for field in fields:
                for val in [None,False,1,'true']:
                    g=docked();d={k:True for k in fields};d[field]=val
                    with self.subTest(kind=kind,field=field,value=val),self.assertRaises(Rejected):g.record_test_receipt(**receipt(g,kind,d))
    def test_each_missing_receipt_rejected(self):
        for omitted in FIELDS:
            g=docked()
            for kind in FIELDS:
                if kind!=omitted:g.record_test_receipt(**receipt(g,kind))
            with self.subTest(omitted=omitted),self.assertRaises(Rejected):g.arm_static(run_id='test-run',visual_guard_closed=True)
    def test_stale_receipt_after_fixture_epoch_change_rejected(self):
        g=qualified();old=receipt(g,'mechanics');g.change_fixture(next_branch='B02',specimen=g.specimen,treatment_revision='none');g.dock(specimen=g.specimen,carrier='carrier',branch='B02',grasp_zone='carrier.handle_right',supported=True)
        with self.assertRaises(Rejected):g.record_test_receipt(**old)
    def test_fault_and_quarantine_survive_closeout(self):
        g=qualified();g.fault('independent loss of sync');g.closeout(safe_state_receipt=True,disposition='quarantine')
        self.assertTrue(g.faulted and g.quarantined);self.assertTrue(any(e[0]=='test_fault' for e in g.events))
        with self.assertRaises(Rejected):g.dock(specimen=g.specimen,carrier='carrier',branch='B03',grasp_zone='carrier.handle_right',supported=True)
    def test_source_outcome_cannot_serve_as_qualification(self):
        g=docked()
        with self.assertRaises(Rejected):g.record_test_receipt(**{**receipt(g,'mechanics'),'kind':'paper_fit_error'})
    def test_real_execution_rejected_after_nominal_closeout(self):
        g=qualified();r=g.arm_static(run_id='test-run',visual_guard_closed=True);self.assertFalse(r['physical_permission']);g.finish_static(unloaded=True,disarmed=True,recovery_ok=True);r=g.closeout(safe_state_receipt=True,disposition='storage');self.assertFalse(r['scientific_validation'])
        with self.assertRaises(Rejected):g.execute_physical('move',distance_mm=20)
    def test_analysis_is_never_success_or_global_injectivity_proof(self):
        base=dict(mode='boundary_inference',physical_or_numerical='numerical',interior_targets_used=False,det_f_positive=True,global_injectivity_verified=False,normalization_nonzero=True,closed_boundary=True,conventions_reviewed=True,source_conflicts_resolved=True)
        good=mod.analysis_guard(**base);self.assertFalse(good['scientific_success']);self.assertEqual(good['global_geometry_status'],'unverified')
        for delta in [{'interior_targets_used':True},{'det_f_positive':False},{'normalization_nonzero':False},{'closed_boundary':False},{'conventions_reviewed':False},{'source_conflicts_resolved':False},{'physical_or_numerical':'physical+numerical'},{'mode':'spring_solver'}]:
            with self.subTest(delta=delta),self.assertRaises(Rejected):mod.analysis_guard(**{**base,**delta})
if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    inputs={f:hashlib.sha256((P/f).read_bytes()).hexdigest() for f in FILES+['semantic_controls.py','geometry/conformal_lab.glb','tests/independent_package_audit.py']}
    paired_hashes={'operations.json':hashlib.sha256((TASK/'operations.json').read_bytes()).hexdigest()}
    projection=json.dumps(PLAN['operation_bindings'],sort_keys=True,separators=(',',':')).encode();paired_projection_hash=hashlib.sha256(projection).hexdigest()
    out={'schema':'sciencegym.independent_asset_contract_tests.v1','passed':result.wasSuccessful(),'test_methods':result.testsRun,'failed_methods':len(result.failures),'errored_methods':len(result.errors),'package_negative_mutations':22,'qualification_bad_field_cases':sum(len(v) for v in FIELDS.values())*4,'source_review_label':'accepted-source-review','paired_task_label':TASK.name,'inspected_sha256':inputs,'paired_inspected_sha256':paired_hashes,'paired_selector_projection_sha256':paired_projection_hash,'paired_projection_definition':'Canonical JSON of asset_binding_plan.json operation_bindings only; sort_keys=True, compact comma/colon separators, UTF-8. Status and final_asset_hashes excluded to prevent a sealing hash cycle.','boundary':'Pure in-memory guards, package data and portable-container integrity only; no physical or scientific validation.'}
    (P/'review/independent_package_audit.json').write_text(json.dumps(out,indent=2)+'\n');raise SystemExit(not result.wasSuccessful())
