#!/usr/bin/env python3
"""Standard-library static and synthetic bookkeeping tests; no acoustics execute."""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import contract_checks as c
R=Path(os.environ.get('BIANISOTROPIC_TASK_ROOT',Path(__file__).resolve().parents[1]))
def load(name): return c.strict_load(R/name)
def mutate(obj,key,value):
    out=copy.deepcopy(obj); out[key]=value; return out

class StaticPackageTests(unittest.TestCase):
    def test_json_is_strict_and_english_unicode_safe(self):
        for path in R.rglob('*.json'):
            with self.subTest(file=path.name):
                c.strict_load(path)
                text=path.read_text()
                self.assertFalse(any('\u4e00'<=char<='\u9fff' for char in text))
    def test_count_and_unique_ids(self):
        for file,key,count in [('operations.json','operations','operation_count'),('branches.json','branches','branch_count'),('unknown_parameters.json','unknowns','unknown_count')]:
            d=load(file); self.assertEqual(len(c.index(d[key])),d[count])
    def test_operation_contracts_are_explicit(self):
        for op in load('operations.json')['operations']:
            for key in ['actor','objects','tools','actions','preconditions','postconditions','required_completion_evidence','provenance','recovery','location_id']:
                self.assertTrue(op[key],(op['id'],key))
            self.assertEqual(op['execution_mode'],'design_only_no_runtime')
    def test_references_and_dependency_graph(self):
        ops=c.index(load('operations.json')['operations']); branches=c.index(load('branches.json')['branches'])
        ev=c.index(load('provenance.json')['evidence']); unknowns=c.index(load('unknown_parameters.json')['unknowns']); stations=c.index(load('station_contracts.json')['stations'])
        for op in ops.values():
            self.assertIn(op['location_id'],stations)
            for field,target in [('evidence_ids',ev),('unknown_parameter_ids',unknowns),('depends_on',ops)]:
                self.assertTrue(set(op[field]) <= set(target),op['id'])
        for b in branches.values():
            self.assertTrue(set(b['operation_ids'])<=set(ops))
            self.assertTrue(set(b['evidence_ids'])<=set(ev))
            self.assertTrue(set(b['unknown_parameter_ids'])<=set(unknowns))
        edges=load('dependencies.json')['edges']
        self.assertTrue(c.validate_dag(ops,[(x['from'],x['to']) for x in edges]))
        self.assertEqual({(x['from'],x['to']) for x in edges},{(d,o['id']) for o in ops.values() for d in o['depends_on']})
    def test_coverage_covers_every_branch_and_all_source_families(self):
        rows=load('coverage_matrix.json')['rows']; self.assertEqual(len(rows),12)
        covered={b for row in rows for b in row['branch_ids']}
        branches=set(c.index(load('branches.json')['branches']))
        self.assertEqual(covered,branches)
        for row in rows:
            self.assertTrue(row['source_locator'])
            self.assertTrue(row['conversion_implication'])
        self.assertFalse(rows[-1]['branch_ids'])
    def test_branch_dependencies_close_with_declared_prerequisite_receipts(self):
        branches=c.index(load('branches.json')['branches']);ops=c.index(load('operations.json')['operations'])
        for branch in branches.values():
            available=set(branch['operation_ids'])
            for parent in branch.get('requires_branch_receipts',[]):available.update(branches[parent]['operation_ids'])
            for op_id in branch['operation_ids']:
                self.assertTrue(set(ops[op_id]['depends_on'])<=available,(branch['id'],op_id))
            self.assertTrue({u for op_id in branch['operation_ids'] for u in ops[op_id]['unknown_parameter_ids']}<=set(branch['unknown_parameter_ids']))
    def test_main_and_si_identity_and_hash_records(self):
        a=load('source_access_audit.json')
        self.assertEqual([(s['id'],s['pages']) for s in a['sources']],[('main',9),('si',24)])
        for source in a['sources']:
            self.assertEqual(len(source['sha256']),64)
            self.assertTrue(source['valid_pdf'])
        self.assertIn('not obtained',a['closure']['peer_review_file'])
    @unittest.skipUnless(os.environ.get('BIANISOTROPIC_SOURCE_DIR'),'Optional private source bytes omitted from export')
    def test_optional_source_byte_hashes(self):
        source_dir=Path(os.environ['BIANISOTROPIC_SOURCE_DIR'])
        for s in load('source_access_audit.json')['sources']:
            data=(source_dir/s['local_file']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(),s['sha256'])
            self.assertEqual(len(data),s['bytes'])
    def test_only_60_degree_physical_angle(self):
        branches=load('branches.json')['branches']
        angles={b['angle_deg'] for b in branches if b['evidence_type']=='physical_measurement'}
        self.assertEqual(angles,{60})
        for b in branches:
            if b.get('angle_deg') in (70,80): self.assertIn(b['evidence_type'],('numerical_only','numerical_optimization'))
        self.assertEqual(c.index(branches)['RETRIEVAL_NUMERICAL']['physical_specimens'],0)
    def test_independent_numerical_branches(self):
        forbidden={'PRINT_LOAD','PRINT_RUN','PRINT_UNLOAD','PANEL_INSTALL','POINT_ACQUIRE'}
        for b in load('branches.json')['branches']:
            if b.get('physical_specimens')==0:
                self.assertFalse(forbidden & set(b['operation_ids']))
                self.assertFalse(b.get('requires_branch_receipts'))
                self.assertFalse(set(b['unknown_parameter_ids']) & {'U02','U03','U04','U05','U06','U07','U16','U18'})
    def test_nineteen_geometry_rows_and_unusual_coefficient_preserved(self):
        g=load('geometry_tables.json')
        self.assertEqual([len(g[f'table_{i}_{a}deg']['rows']) for i,a in [(1,60),(2,70),(3,80)]],[11,4,4])
        self.assertEqual(g['table_1_60deg']['rows'][3]['r_plus'],'0.31+0.028i')
        self.assertFalse(load('material_cards.json')['cards'][1]['fabrication_geometry_complete'])
    def test_reported_outcomes_remain_typed_and_distinct(self):
        out=c.index(load('source_outcomes.json')['records'])
        self.assertEqual(out['O04']['value'],0.81)
        self.assertEqual(out['O07']['value'],0.89)
        self.assertNotEqual(out['O04']['evidence_type'],out['O07']['evidence_type'])
        self.assertEqual(out['O09']['metric'],'fraction_of_transmitted_energy_in_desired_direction')
        self.assertEqual(out['O09']['value'],0.97)
        self.assertEqual(len(load('source_conflicts.json')['records']),6)
    def test_unknowns_have_no_silent_values_or_owners(self):
        for u in load('unknown_parameters.json')['unknowns']:
            self.assertIsNone(u['value']); self.assertEqual(u['status'],'unresolved')
            self.assertTrue(u['source_search']); self.assertEqual(u['owner'],'unassigned')
        for card in load('episode_input_contract.json')['cards']: self.assertIsNone(card['value'])
    def test_control_completeness_and_actor_boundary(self):
        controls=c.index(load('control_packages.json')['controls'])
        self.assertEqual(set(controls),{'CTRL_GSL_60','CTRL_GSL_70','CTRL_GSL_80','CTRL_LOSS','CTRL_TOPOLOGY','CTRL_BLANK','CTRL_DRIFT'})
        for b in load('branches.json')['branches']:
            self.assertTrue(set(b.get('control_ids',[]))<=set(controls))
        boundary=load('RELEASE_BOUNDARY.json'); self.assertFalse(boundary['loader_implemented'])
        self.assertIn('source_outcomes.json',boundary['evaluator_only'])
        public=json.dumps(load('agent_visible.json'))
        for s in ['0.93','0.96','0.97','0.81','0.89','0.028i']: self.assertNotIn(s,public)
    def test_export_has_no_sources_or_host_paths(self):
        for p in R.rglob('*'):
            if not p.is_file() or '__pycache__' in p.parts: continue
            self.assertIn(p.suffix,{'.md','.json','.py'})
            text=p.read_text()
            for path in ['/' + name + '/' for name in ('workspace','home','Users','root','mnt')]:
                self.assertNotIn(path,text,str(p))
    def test_export_manifest_covers_exact_payload_and_hashes(self):
        m=load('EXPORT_ALLOWLIST.json')
        actual={str(p.relative_to(R)) for p in R.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        self.assertEqual(set(m['allowlist']),actual)
        self.assertEqual(m['total_file_count_including_manifest'],len(actual))
        self.assertEqual(m['payload_file_count'],len(actual)-1)
        self.assertEqual({r['path'] for r in m['files']},actual-{'EXPORT_ALLOWLIST.json'})
        for item in m['files']:
            b=(R/item['path']).read_bytes(); self.assertEqual(len(b),item['bytes'])
            self.assertEqual(hashlib.sha256(b).hexdigest(),item['sha256'])

class AdversarialContractTests(unittest.TestCase):
    def test_strict_parser_rejects_duplicate_and_nonfinite_json(self):
        for raw in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with tempfile.TemporaryDirectory() as directory:
                path=Path(directory)/'fixture.json';path.write_text(raw)
                with self.subTest(raw=raw),self.assertRaises(ValueError):c.strict_load(path)
    def test_cycle_and_dangling_reference_rejected(self):
        self.assertTrue(c.validate_dag(['A','B'],[('A','B')]))
        for edges in [[('A','A')],[('A','B'),('B','A')],[('A','X')]]:
            with self.subTest(edges=edges),self.assertRaises(ValueError): c.validate_dag(['A','B'],edges)
    def test_unknown_card_rejects_empty_and_unqualified(self):
        good={'U':dict(value={'input':1},origin='qualified_episode_input',qualified=True,revision='r1',approver='fixture-author')}
        self.assertTrue(c.require_cards(['U'],good))
        for change in [None,{}, {'value':None},{'value':[]},{'value':{},'origin':'source_inferred'}]:
            with self.subTest(change=change),self.assertRaises(ValueError): c.require_cards(['U'],{'U':change})
        for key,value in [('origin','source_inferred'),('qualified',False),('revision',''),('approver',None)]:
            bad=copy.deepcopy(good); bad['U'][key]=value
            with self.assertRaises(ValueError): c.require_cards(['U'],bad)
    def panel(self):
        return dict(id='panel1',angle_deg=60,assembly_version=1,inspection_version=1,orientation='qualified_incident_face',sections=[dict(id=f's{i}',slot=i,status='accepted',build_id='b1',design_slots=list(range(1,12)),location='panel1') for i in range(1,10)])
    def test_panel_positive_and_duplicate_identity(self):
        p=self.panel(); self.assertTrue(c.validate_panel(p)); p['sections'][1]['id']='s1'
        with self.assertRaises(ValueError): c.validate_panel(p)
    def test_panel_wrong_order_orientation_and_stale_inspection(self):
        p=self.panel()
        for key,value in [('angle_deg',70),('orientation','reversed'),('inspection_version',0),('assembly_version',True)]:
            with self.subTest(key=key),self.assertRaises(ValueError): c.validate_panel(mutate(p,key,value))
        for key,value in [('design_slots',list(range(11,0,-1))),('location','other_panel'),('status','quarantined'),('build_id','')]:
            bad=copy.deepcopy(p); bad['sections'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): c.validate_panel(bad)
    def test_panel_missing_period_or_duplicate_slot(self):
        p=self.panel(); p['sections'].pop()
        with self.assertRaises(ValueError): c.validate_panel(p)
        p=self.panel();p['sections'][1]['slot']=1
        with self.assertRaises(ValueError):c.validate_panel(p)
    def test_thermal_motion_and_completion_gates(self):
        r=dict(job_complete=True,thermal_safe=True,motion_stopped=True,guard_release=True,job_id='b1',geometry_revision='g1')
        self.assertTrue(c.validate_build_release(r))
        for key in ('job_complete','thermal_safe','motion_stopped','guard_release'):
            for value in (False,1,None):
                with self.subTest(key=key,value=value),self.assertRaises(ValueError): c.validate_build_release(mutate(r,key,value))
    def scan(self):
        points=[dict(id='p1',xy=[0,0]),dict(id='p2',xy=[0.02,0])]
        condition=dict(zip(c.CONDITION_KEYS,['g1','f1','source1','mic1','daq1','phase1','air1',3000,'grid1']))
        context=dict(episode_id='episode1',branch_id='MEASURE_60',frequency_hz=3000,units='Pa',configuration_id='sample_transmission',run_id='run1',calibration_id='cal1',calibration_valid=True,panel_id='panel1',assembly_version=1,install_epoch=1,condition=condition,is_mock=True)
        records=[]
        for point in points:
            for repeat in range(1,5):
                records.append(dict(**{k:v for k,v in context.items() if k not in ('calibration_valid',)},raw_id=f"{point['id']}-{repeat}",point_id=point['id'],repeat_index=repeat,status='valid',content_hash=f'h{point["id"]}-{repeat}',clipped=False,settled=True,pose_xy=point['xy'],pose_receipt_id='pose-'+point['id'],calibration_current=True,timestamp=f'2026-01-01T00:00:0{repeat}+00:00'))
        return points,records,context
    def test_scan_positive_with_honest_failed_retry_retained(self):
        p,r,ctx=self.scan();self.assertTrue(c.validate_scan(p,r,ctx))
        failed=copy.deepcopy(r[0]);failed.update(raw_id='bad0',status='invalid',invalid_reason='clipped',clipped=True)
        self.assertTrue(c.validate_scan(p,[failed]+r,ctx))
    def test_empty_unknown_and_duplicate_schedule(self):
        p,r,ctx=self.scan()
        for bad in [[],None,[p[0],p[0]],[p[0],dict(id='p3',xy=p[0]['xy'])],[dict(id='p1',xy=[float('nan'),0])]]:
            with self.subTest(points=bad),self.assertRaises(ValueError): c.validate_scan(bad,r,ctx)
    def test_scan_missing_point_or_repeat_is_not_zero(self):
        p,r,ctx=self.scan()
        for rr in [r[:-1],r[:4],[]]:
            with self.subTest(size=len(rr)),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
    def test_scan_duplicate_raw_or_repeat_rejected(self):
        p,r,ctx=self.scan()
        for key,value in [('raw_id',r[0]['raw_id']),('repeat_index',1)]:
            rr=copy.deepcopy(r);rr[1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
    def test_scan_quality_and_pose_gate(self):
        p,r,ctx=self.scan()
        for key,value in [('clipped',True),('settled',False),('pose_xy',[2,3]),('pose_receipt_id',''),('content_hash',''),('calibration_current',False),('is_mock',False),('repeat_index',True),('status','pending')]:
            rr=copy.deepcopy(r);rr[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
    def test_scan_mixed_identity_and_calibration(self):
        p,r,ctx=self.scan()
        for key,value in [('episode_id','other-episode'),('branch_id','other-branch'),('units','volts'),('frequency_hz',4000),('configuration_id','sample_reflection'),('run_id','run2'),('calibration_id','cal2'),('panel_id','panel2'),('assembly_version',2),('install_epoch',2)]:
            rr=copy.deepcopy(r);rr[-1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
        with self.assertRaises(ValueError):c.validate_scan(p,r,mutate(ctx,'calibration_valid',False))
    def test_canonical_raw_fields_and_timestamp_are_enforced(self):
        p,r,ctx=self.scan()
        required=load('lineage_contract.json')['required_raw_keys']
        for key in required:
            rr=copy.deepcopy(r);rr[0].pop(key)
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
        for timestamp in ['not-a-time','2026-01-01T00:00:00',None]:
            rr=copy.deepcopy(r);rr[0]['timestamp']=timestamp
            with self.subTest(timestamp=timestamp),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
    def test_scan_condition_signature_mutation(self):
        p,r,ctx=self.scan()
        for key in c.CONDITION_KEYS:
            rr=copy.deepcopy(r);rr[0]['condition']=dict(rr[0]['condition']);rr[0]['condition'][key]='changed'
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_scan(p,rr,ctx)
    def pair(self):
        condition=dict(zip(c.CONDITION_KEYS,['g1','f1','source1','mic1','daq1','phase1','air1',3000,'grid1']))
        blank=dict(id='blank1',episode_id='episode1',branch_id='MEASURE_60',run_id='blank-run',assembly_version=None,install_epoch=None,configuration_id='blank_reflection',complete=True,representation='complex_pressure',raw_parent_ids=['raw-b'],is_mock=True,post_drift_valid=True,condition=condition,point_ids=['p1','p2'],panel_id='blank')
        sample=copy.deepcopy(blank);sample.update(id='sample1',run_id='sample-run',assembly_version=1,install_epoch=1,configuration_id='sample_reflection',raw_parent_ids=['raw-s'],panel_id='panel1')
        analysis=dict(mode='complex_sample_minus_blank',blank_id='blank1',sample_id='sample1',pair_validity_current=True,raw_parent_ids=['raw-b','raw-s'],expected_blank_run_id='blank-run',expected_sample_context={key:sample[key] for key in ('episode_id','branch_id','run_id','panel_id','assembly_version','install_epoch')})
        return blank,sample,analysis
    def test_valid_blank_subtraction_metadata(self):
        self.assertTrue(c.validate_reflection_pair(*self.pair()))
    def test_blank_frame_phase_source_daq_medium_mismatch(self):
        for key in c.CONDITION_KEYS:
            b,s,a=self.pair();s['condition'][key]='changed'
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_reflection_pair(b,s,a)
    def test_reflection_pair_requires_current_sample_installation_and_campaign(self):
        for key,value in [('episode_id','other-episode'),('branch_id','other-branch'),('run_id','old-run'),('panel_id','panel2'),('assembly_version',2),('install_epoch',2)]:
            b,s,a=self.pair();s[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_reflection_pair(b,s,a)
        b,s,a=self.pair();a.pop('expected_sample_context')
        with self.assertRaises(ValueError):c.validate_reflection_pair(b,s,a)
        b,s,a=self.pair();b['run_id']='other-blank-run'
        with self.assertRaises(ValueError):c.validate_reflection_pair(b,s,a)
    def test_magnitude_subtraction_stale_pair_and_wrong_parents(self):
        b,s,a=self.pair()
        for key,value in [('mode','magnitude_difference'),('pair_validity_current',False),('blank_id','old-blank'),('raw_parent_ids',['raw-s'])]:
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_reflection_pair(b,s,mutate(a,key,value))
    def test_blank_incomplete_wrong_region_or_failed_drift(self):
        b,s,a=self.pair()
        for key,value in [('complete',False),('configuration_id','sample_transmission'),('representation','magnitude'),('point_ids',['p2']),('post_drift_valid',False),('raw_parent_ids',[])]:
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_reflection_pair(b,mutate(s,key,value),a)
    def metric(self):
        return dict(name='transmitted_direction_share',denominator='total_transmitted_normal_flux',quantity='propagating_normal_flux',value=0.72,source_record_id='actual-synthetic-record',includes_evanescent_as_power=False)
    def test_truthful_nonpaper_outcome_is_valid(self):
        self.assertTrue(c.validate_metric(self.metric()))
    def test_denominator_and_pressure_squared_confusion(self):
        m=self.metric()
        for key,value in [('name','incident_to_target_efficiency'),('quantity','pressure_squared'),('denominator','incident_normal_flux'),('includes_evanescent_as_power',True),('value',float('nan')),('value',True),('source_record_id','')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):c.validate_metric(mutate(m,key,value))
    def jobs(self):
        j=dict(id='job1',kind='bianisotropic',evidence_type='synthetic_numerical_job_fixture',converged=True,field_artifact='field1',mesh_study_id='mesh1',angle_deg=70,cells_per_period=4,frequency_hz=3000,source_signature='source1',medium_card='air1',domain_card='domain1',PML_card='pml1',flux_definition='normal_incident_to_target')
        k=copy.deepcopy(j);k.update(id='job2',kind='ideal_GSL',field_artifact='field2')
        return j,k
    def test_numerical_pair_valid(self):self.assertTrue(c.validate_numerical_pair(*self.jobs()))
    def test_numerical_control_mismatch_and_nonconvergence(self):
        a,b=self.jobs()
        for key,value in [('id','job1'),('kind','bianisotropic'),('angle_deg',80),('cells_per_period',11),('converged',False),('mesh_study_id',''),('source_signature','other'),('evidence_type','physical')]:
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_numerical_pair(a,mutate(b,key,value))
    def retrieval(self):
        return [dict(job_id='r'+str(i),termination=t,converged=True,is_mock=True,geometry_revision='g1',probe_ids=['p1','p2','p3','p4'],pressures=([[1,0],[0.3,0.4],[0.2,0.5],[0.3,0.1]] if i==0 else [[0.2,0.4],[0.8,-0.2],[0.5,0.3],[-0.1,0.5]]),port_convention='qualified-sign-v1',frequency_hz=3000,medium_card_id='synthetic-medium',source_signature='synthetic-source',wavenumber_rad_m=55,cell_datum_m=0,probe_positions_m=[-0.06,-0.02,0.02,0.06]) for i,t in enumerate(['plane_wave_radiation','hard_wall'])]
    def test_retrieval_valid_and_independent_terminations(self):
        r=self.retrieval();self.assertTrue(c.validate_retrieval(r,100))
        for key,value in [('termination','plane_wave_radiation'),('job_id','r0'),('probe_ids',['p1','p2']),('frequency_hz',3001),('medium_card_id','other-medium'),('source_signature','other-source'),('probe_positions_m',[-0.06,-0.06,0.02,0.06]),('port_convention','different'),('geometry_revision','g2')]:
            rr=copy.deepcopy(r);rr[1][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_retrieval(rr,100)
    def test_retrieval_duplicated_state_and_aliased_probe_spacing_rejected(self):
        r=self.retrieval();r[1]['pressures']=copy.deepcopy(r[0]['pressures'])
        with self.assertRaises(ValueError):c.validate_retrieval(r,100)
        r=self.retrieval()
        for item in r:item['probe_positions_m']=[-0.1,-0.1+3.141592653589793/55,0.02,0.06]
        with self.assertRaises(ValueError):c.validate_retrieval(r,100)
    def test_retrieval_transformed_interface_conditioning_is_checked(self):
        # Synthetic algebra: separate probe/data conditioning can pass while
        # the actual normalized interface matrix is ill-conditioned.
        r=self.retrieval();epsilon=math.atan(1/22.25);k=55
        positions=[(-math.pi-epsilon)/k,(-math.pi+epsilon)/k,0.02,0.06]
        for idx,item in enumerate(r):
            item['probe_positions_m']=positions
            item['pressures']=([[math.cos(k*x),0] for x in positions] if idx==0 else [[0,-467*math.sin(k*x)] for x in positions])
        with self.assertRaisesRegex(ValueError,'interface pressure'):
            c.validate_retrieval(r,100)
    def test_retrieval_missing_or_nonfinite_complex_pressure(self):
        for pressure in [[],[[1,0]]*3,[[float('nan'),0]]*4,[[1]]*4]:
            r=self.retrieval();r[0]['pressures']=pressure
            with self.subTest(pressure=pressure),self.assertRaises(ValueError):c.validate_retrieval(r,100)
    def ga(self):
        cfg=dict(population=10,mutation_rate=0.2,retention_fraction=0.5,elite_mutates=False,crossover=False,generation_limit=1500,restarts_per_cell=50,objective_revision='obj1',bounds_revision='bounds1')
        runs=[dict(cell_id='cell1',restart=i,status='completed',history_id=f'h{i}',seed=i,generation_count=1500) for i in range(1,51)]
        return cfg,['cell1'],runs
    def test_ga_complete_and_failed_search_retained(self):
        cfg,cells,r=self.ga();self.assertTrue(c.validate_ga(cfg,cells,r))
        r[1].update(status='failed',failure_reason='solver failed',generation_count=40)
        self.assertTrue(c.validate_ga(cfg,cells,r))
    def test_ga_missing_restart_early_stop_or_hidden_crossover(self):
        cfg,cells,r=self.ga()
        for rr in [r[:-1],r+[r[0]]]:
            with self.assertRaises(ValueError):c.validate_ga(cfg,cells,rr)
        with self.assertRaises(ValueError):c.validate_ga(mutate(cfg,'crossover',True),cells,r)
        r[0]['generation_count']=1000
        with self.assertRaises(ValueError):c.validate_ga(cfg,cells,r)
    def test_actor_projection_rejects_top_level_and_nested_answers(self):
        p=dict(goal_id='MEASURE_60',inventory=[dict(id='panel1',location='store',status='accepted')],observations=[dict(id='obs1',observable='source_off',value=True,acquired=True)],qualified_card_ids=['card1'])
        self.assertEqual(c.actor_projection(p),p)
        for key in ['source_outcomes','reference_route','future_measurements','hidden_faults']:
            bad=copy.deepcopy(p);bad[key]=[0.97]
            with self.subTest(key=key),self.assertRaises(ValueError):c.actor_projection(bad)
        bad=copy.deepcopy(p);bad['observations'][0]['expected']=0.97
        with self.assertRaises(ValueError):c.actor_projection(bad)
        bad=copy.deepcopy(p);bad['observations'][0]['acquired']=False
        with self.assertRaises(ValueError):c.actor_projection(bad)
        bad=copy.deepcopy(p);bad['qualified_card_ids']=[{'source_outcomes':[0.93]}]
        with self.assertRaises(ValueError):c.actor_projection(bad)
    def test_preparation_and_calibration_archive_do_not_require_unrelated_stations(self):
        m=dict(raw_immutable=True,all_attempts_retained=True,lineage_complete=True,report_scoped=True,physical_campaign=True,measurement_selected=False,used_stations=['WS_PRINT','WS_ASSEMBLY'],custody_complete=True,cleanup_complete=True,print_job_terminal=True,print_thermal_safe=True,print_motion_stopped=True,print_guard_release=True,evidence_claim='synthetic_bookkeeping_only')
        self.assertTrue(c.validate_archive(m))
        for key in ('print_job_terminal','print_thermal_safe','print_motion_stopped','print_guard_release'):
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_archive(mutate(m,key,False))
        m=dict(raw_immutable=True,all_attempts_retained=True,lineage_complete=True,report_scoped=True,physical_campaign=True,measurement_selected=False,used_stations=['WS_GUIDE','WS_CALIBRATE'],custody_complete=True,cleanup_complete=True,source_off=True,motion_stopped=True,evidence_claim='synthetic_bookkeeping_only')
        self.assertTrue(c.validate_archive(m))
        branch=c.index(load('branches.json')['branches'])['QUALIFY_GUIDE']
        self.assertNotIn('U02',branch['unknown_parameter_ids'])
    def test_archive_cannot_skip_cleanup_drift_or_claim_execution(self):
        m=dict(raw_immutable=True,all_attempts_retained=True,lineage_complete=True,report_scoped=True,physical_campaign=True,measurement_selected=True,used_stations=['WS_GUIDE'],source_off=True,motion_stopped=True,custody_complete=True,cleanup_complete=True,post_drift_valid=True,evidence_claim='synthetic_bookkeeping_only')
        self.assertTrue(c.validate_archive(m))
        for key in ['raw_immutable','all_attempts_retained','lineage_complete','report_scoped','source_off','motion_stopped','custody_complete','cleanup_complete','post_drift_valid']:
            with self.subTest(key=key),self.assertRaises(ValueError):c.validate_archive(mutate(m,key,False))
        with self.assertRaises(ValueError):c.validate_archive(mutate(m,'evidence_claim','whole_paper_robot_execution_validated'))

if __name__=='__main__': unittest.main(verbosity=2)
