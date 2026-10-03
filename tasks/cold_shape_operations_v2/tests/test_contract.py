import copy
import pathlib
import unittest
from contract import *
ROOT=pathlib.Path(__file__).resolve().parents[1]
class ContractTests(unittest.TestCase):
    def setUp(self): self.d=load(ROOT)
    def bad(self,fn,*args):
        with self.assertRaises(ContractError):fn(*args)
    def plan(self,b='TENSILE_RT'):
        bm={x['id']:x for x in self.d['branches.json']['branches']}
        cr=next(x for x in self.d['condition_requirements.json']['branches'] if x['branch_id']==b)
        dims=cr['required_dimensions']; names=list(dims)
        combos=list(itertools.product(*(dims[k] for k in names))) if names else [()]
        cells=[{'id':'cell_'+str(i),**dict(zip(names,vals))} for i,vals in enumerate(combos)]
        return {'phase_schedules':{b:bm[b]['phase_order']},'mode':'selected_episode','branch_ids':[b],'gate_cards':{u:{'gate_id':u,'status':'qualified','qualification_receipt':'synthetic_q_'+u,'revision':'v1','payload':{f:'synthetic_qualified_'+f for f in next(x for x in self.d['episode_input_contract.json']['cards'] if x['unknown_id']==u)['required_fields']}} for u in bm[b]['unknown_parameter_ids']},'conditions':{b:cells},'replicate_counts':{b:1},'cycles':{b:bm[b]['source_cycles']},'retry_limit':1}
    def fixture(self):
        r={'synthetic':True,'data_class':'measurement_raw','record_id':'R1','sample_id':'S1','version':'v1','branch_id':'TENSILE_RT','condition_key':'B1_RT','phase':'program_or_measure','attempt_id':'A1','raw_sha256':'a'*64,'calibration_id':'C1','setup_signature':'SET1','receipt_id':'REC1','timestamp_utc':'2026-10-03T00:00:00Z','quality':'accepted','temperature_C':25,'material_variant':'B1'}
        c={'objects':{'S1':'v1'},'consumed':[],'calibrations':{'C1':'SET1'},'conditions':{'TENSILE_RT':['B1_RT']},'phases':{'TENSILE_RT':['program_or_measure']},'materials':{'S1':'B1'}}
        return r,c
    def trace(self):
        return [{'phase':p,'synthetic':True,'job_id':'J1','sample_id':'S1','sequence':i,'receipt_id':'R'+str(i),'guard_closed':True,'qualified':True,'program_hash':'hash','stored_energy_released':True,'safe_to_handle':True} for i,p in enumerate(PHASES)]
    def test_static_package(self):self.assertEqual(validate_package(self.d)['physical_branches'],32)
    def test_missing_file(self):self.d.pop('state_contract.json');self.bad(validate_package,self.d)
    def test_gate_default(self):self.d['unknown_parameters.json']['unknowns'][0]['default']='guess';self.bad(validate_package,self.d)
    def test_wrong_doi(self):self.d['operations.json']['doi']='wrong';self.bad(validate_package,self.d)
    def test_duplicate_operation(self):self.d['operations.json']['operations'][1]['id']='PLAN';self.bad(validate_package,self.d)
    def test_invalid_port(self):self.d['operations.json']['operations'][0]['interface_port']='unknown';self.bad(validate_package,self.d)
    def test_actor_boundary(self):next(o for o in self.d['operations.json']['operations'] if o['kind']=='service_autonomous')['actor']='robot';self.bad(validate_package,self.d)
    def test_invented_postcure(self):next(b for b in self.d['branches.json']['branches'] if b['id']=='FABRICATE')['conditions']['post_cure_default']='UV';self.bad(validate_package,self.d)
    def test_missing_ancestor_gate(self):next(b for b in self.d['branches.json']['branches'] if b['id']=='TENSILE_RT')['unknown_parameter_ids'].remove('U_PRINT');self.bad(validate_package,self.d)
    def test_branch_cycle(self):self.d['branches.json']['branches'][0]['required_branch_ids']=['TENSILE_RT'];self.bad(validate_package,self.d)
    def test_alt_recipe_leak(self):next(b for b in self.d['branches.json']['branches'] if b['id']=='ALT_RESIN_BATCH')['conditions']['primary_additives_inherited']=True;self.bad(validate_package,self.d)
    def test_movie_overclaim(self):self.d['source_access_audit.json']['read_scope']['movie_bytes']=8;self.bad(validate_package,self.d)
    def test_electrical_overclaim(self):next(b for b in self.d['branches.json']['branches'] if b['id']=='ELECTRONIC_STRIP')['conditions']['resistance_invariance_claim']=True;self.bad(validate_package,self.d)
    def test_source_unit_rewrite(self):next(b for b in self.d['branches.json']['branches'] if b['id']=='TENSILE_HOT')['conditions']['stress_axis_source_unit']='MPa';self.bad(validate_package,self.d)
    def test_plan_positive(self):self.assertTrue(validate_plan(self.plan(),self.d))
    def test_empty_schedule(self):p=self.plan();p['conditions']['TENSILE_RT']=[];self.bad(validate_plan,p,self.d)
    def test_unknown_repeat(self):p=self.plan();p['replicate_counts']['TENSILE_RT']=None;self.bad(validate_plan,p,self.d)
    def test_boolean_repeat(self):p=self.plan();p['replicate_counts']['TENSILE_RT']=True;self.bad(validate_plan,p,self.d)
    def test_unresolved_gate(self):p=self.plan();p['gate_cards'].pop('U_CAD');self.bad(validate_plan,p,self.d)
    def test_unqualified_card(self):p=self.plan();p['gate_cards']['U_CAD']['status']='requested';self.bad(validate_plan,p,self.d)
    def test_whole_paper_promotion(self):p=self.plan();p['mode']='whole_paper';self.bad(validate_plan,p,self.d)
    def test_cycle_schedule_mismatch(self):p=self.plan('HINGE_FORTY_CYCLES');p['cycles']['HINGE_FORTY_CYCLES']=10;self.bad(validate_plan,p,self.d)
    def test_service_positive(self):self.assertTrue(validate_service_trace(self.trace(),'J1','S1'))
    def test_service_request_not_completion(self):self.bad(validate_service_trace,self.trace()[:5],'J1','S1')
    def test_service_reordered(self):t=self.trace();t[5],t[6]=t[6],t[5];self.bad(validate_service_trace,t,'J1','S1')
    def test_service_guard(self):t=self.trace();t[4]['guard_closed']=False;self.bad(validate_service_trace,t,'J1','S1')
    def test_service_hot_unload(self):t=self.trace();t[6]['safe_to_handle']=False;self.bad(validate_service_trace,t,'J1','S1')
    def test_service_substitution(self):t=self.trace();t[5]['sample_id']='S2';self.bad(validate_service_trace,t,'J1','S1')
    def test_service_receipt_reuse(self):t=self.trace();t[5]['receipt_id']=t[3]['receipt_id'];self.bad(validate_service_trace,t,'J1','S1')
    def test_measurement_positive(self):r,c=self.fixture();self.assertTrue(validate_record(r,c,True))
    def test_live_evidence_refused(self):r,c=self.fixture();self.bad(validate_record,r,c)
    def test_source_is_not_measurement(self):r,c=self.fixture();r['data_class']='source_simulation';self.bad(validate_record,r,c,True)
    def test_stale_version(self):r,c=self.fixture();r['version']='v0';self.bad(validate_record,r,c,True)
    def test_destroyed_reuse(self):r,c=self.fixture();c['consumed']=['S1'];self.bad(validate_record,r,c,True)
    def test_calibration_scope(self):r,c=self.fixture();r['setup_signature']='SET2';self.bad(validate_record,r,c,True)
    def test_material_substitution(self):r,c=self.fixture();r['material_variant']='B2';self.bad(validate_record,r,c,True)
    def test_nonfinite_readback(self):r,c=self.fixture();r['temperature_C']=float('nan');self.bad(validate_record,r,c,True)
    def test_literature_substitution(self):r,c=self.fixture();r['source_outcome_substituted']=True;self.bad(validate_record,r,c,True)
    def test_unlabeled_mock(self):r,c=self.fixture();r.pop('synthetic');self.bad(validate_record,r,c,True)
    def test_undeclared_phase(self):r,c=self.fixture();r['phase']='imagined';self.bad(validate_record,r,c,True)
    def test_cycle_positive_and_missing(self):
        rs=[{'cycle_index':i,'sample_id':'S1','program_receipt':'p'+str(i),'release_receipt':'l'+str(i),'recovery_receipt':'r'+str(i),'integrity_receipt':'q'+str(i)} for i in range(1,41)]
        self.assertTrue(validate_cycle_history(rs,40,'S1'));self.bad(validate_cycle_history,[rs[i-1] for i in [1,10,20,30,40]],40,'S1')
    def test_cycle_specimen_swap(self):
        rs=[{'cycle_index':1,'sample_id':'S2','program_receipt':'p','release_receipt':'l','recovery_receipt':'r','integrity_receipt':'q'}];self.bad(validate_cycle_history,rs,1,'S1')
    def campaign(self):
        p=self.plan();bid='TENSILE_RT';b=next(x for x in self.d['branches.json']['branches'] if x['id']==bid);rows=[]
        ctx={'objects':{},'calibrations':{},'service_bindings':{}};p['evidence_context']=ctx
        for cell in p['conditions'][bid]:
            key=cell['id'];sid='sample_'+key;prefix=key+'_';mat=cell['material'];cal=prefix+'cal';setup=prefix+'setup'
            ctx['objects'][sid]={'version':'v1','location':'WS_QC','state':'accepted','acceptance_receipt':prefix+'acceptance','material_variant':mat};ctx['calibrations'][cal]=setup
            phases=[{'phase':ph,'receipt_id':prefix+'phase'+str(i),'condition_key':key,'sample_id':sid,'version':'v1'} for i,ph in enumerate(p['phase_schedules'][bid])]
            controls=[{'control_id':c['id'],'receipt_id':prefix+c['id']} for c in self.d['control_packages.json']['controls'] if c['scope']=='all specimen branches' or isinstance(c['scope'],list) and bid in c['scope']]
            binding={'job_id':prefix+'job','sample_id':sid,'version':'v1','station_id':'WS_MECH','port_id':'safe_fixture_exchange','condition_key':key,'fixture_id':prefix+'fixture','calibration_id':cal,'setup_signature':setup,'material_variant':mat}
            ctx['service_bindings'][binding['job_id']]=binding
            trace=self.trace()
            for event in trace:event.update({**binding,'receipt_id':prefix+'service_'+event['phase']})
            move={'synthetic':True,'sample_id':sid,'version':'v1','from_station':'WS_QC','to_station':'WS_MECH','route_id':'T04','tethers_connected':False,'source_safe_release_receipt':prefix+'move1','retention_receipt':prefix+'move2','destination_ready_receipt':prefix+'move3','arrival_identity_receipt':prefix+'move4','arrival_version':'v1','arrival_sample_id':sid}
            raw,_=self.fixture();raw.update({'sample_id':sid,'condition_key':key,'calibration_id':cal,'setup_signature':setup,'material_variant':mat,'receipt_id':prefix+'raw','record_id':prefix+'rawid'})
            needed=next(x for x in self.d['condition_requirements.json']['branches'] if x['branch_id']==bid)['required_observation_phases']
            raw_records=[{**raw,'phase':ph,'receipt_id':prefix+'raw'+str(i),'record_id':prefix+'rawid'+str(i)} for i,ph in enumerate(needed)]
            ops=[{'operation_id':i,'receipt_id':prefix+'op_'+i,'sample_id':sid,'version':'v1','condition_key':key} for i in b['operation_ids']]
            rows.append({'branch_id':bid,'condition_key':key,'synthetic':True,'status':'accepted','custody_receipt':prefix+'custody','cleanup_receipt':prefix+'cleanup','prerequisite_receipts':[{'branch_id':'FABRICATE','status':'accepted','receipt_id':'prior_fabrication'}],'replicates':[{'sample_id':sid,'version':'v1','phase_receipts':phases,'control_receipts':controls,'physical_events':[{'kind':'transfer','record':move},{'kind':'service','service':'TENSILE','events':trace}],'raw_records':raw_records,'operation_receipts':ops}]})
        return p,rows
    def test_campaign_positive(self):
        p,r=self.campaign();self.assertFalse(evaluate_campaign(p,r,self.d)['physical_execution_validated'])
    def test_campaign_missing(self):self.bad(evaluate_campaign,self.plan(),[],self.d)
    def test_campaign_cleanup(self):
        r=[{'branch_id':'TENSILE_RT','condition_key':'fixture_condition_a','synthetic':True,'status':'accepted','custody_closed':True,'cleanup_closed':False,'prerequisite_closure':True}];self.bad(evaluate_campaign,self.plan(),r,self.d)
    def test_missing_material_condition(self):
        p=self.plan();p['conditions']['TENSILE_RT'].pop();self.bad(validate_plan,p,self.d)
    def test_reordered_scientific_phase(self):
        p=self.plan();p['phase_schedules']['TENSILE_RT']=list(reversed(p['phase_schedules']['TENSILE_RT']));self.bad(validate_plan,p,self.d)
    def test_b1_fixity_separate_branch(self):
        b=next(x for x in self.d['branches.json']['branches'] if x['id']=='B1_FIXITY_SERIES')
        self.assertEqual(b['sample_role'],'reserved_homogeneous_B1_fixity_coupon');self.assertFalse(b['conditions']['hinge_angle_n5_inherited'])
    def transfer(self):
        r={'synthetic':True,'sample_id':'S1','version':'v1','from_station':'WS_ELECTRIC','to_station':'WS_MECH','route_id':'T11','tethers_connected':False,'source_safe_release_receipt':'r1','retention_receipt':'r2','destination_ready_receipt':'r3','arrival_identity_receipt':'r4','arrival_version':'v1','arrival_sample_id':'S1'}
        c={'objects':{'S1':{'version':'v1','location':'WS_ELECTRIC','state':'accepted'}}};return r,c
    def test_transfer_positive(self):r,c=self.transfer();self.assertTrue(validate_transfer(r,c,self.d))
    def test_tethered_transfer(self):r,c=self.transfer();r['tethers_connected']=True;self.bad(validate_transfer,r,c,self.d)
    def test_transfer_wrong_origin(self):r,c=self.transfer();c['objects']['S1']['location']='WS_QC';self.bad(validate_transfer,r,c,self.d)
    def test_transfer_hot_payload(self):r,c=self.transfer();c['objects']['S1']['state']='loaded_or_hot';self.bad(validate_transfer,r,c,self.d)
    def test_transfer_wrong_arrival(self):r,c=self.transfer();r['arrival_sample_id']='S2';self.bad(validate_transfer,r,c,self.d)
    def bound_service(self):
        t=self.trace();x={'job_id':'J1','sample_id':'S1','version':'v1','station_id':'WS_MECH','port_id':'safe_fixture_exchange','condition_key':'cell0','fixture_id':'F1','calibration_id':'C1','setup_signature':'SET1','material_variant':'B1','target_registration_required':True,'target_registration_id':'hinge1'}
        for e in t:e.update(x)
        c={'objects':{'S1':{'version':'v1','location':'WS_MECH','state':'accepted','acceptance_receipt':'Q1','material_variant':'B1'}},'calibrations':{'C1':'SET1'}};return t,x,c
    def test_bound_service_positive(self):t,x,c=self.bound_service();self.assertTrue(validate_service_binding(t,x,c))
    def test_wrong_service_location(self):t,x,c=self.bound_service();c['objects']['S1']['location']='WS_QC';self.bad(validate_service_binding,t,x,c)
    def test_stale_service_version(self):t,x,c=self.bound_service();t[5]['version']='v0';self.bad(validate_service_binding,t,x,c)
    def test_missing_local_registration(self):t,x,c=self.bound_service();t[3].pop('target_registration_id');self.bad(validate_service_binding,t,x,c)
    def test_service_calibration_scope(self):t,x,c=self.bound_service();c['calibrations']['C1']='SET2';self.bad(validate_service_binding,t,x,c)
    def test_service_unaccepted_specimen(self):t,x,c=self.bound_service();c['objects']['S1']['state']='quarantined';self.bad(validate_service_binding,t,x,c)
    def test_card_payload_missing(self):p=self.plan();p['gate_cards']['U_CAD'].pop('payload');self.bad(validate_plan,p,self.d)
    def test_duplicate_card_omits_gate(self):self.d['episode_input_contract.json']['cards'][-1]=copy.deepcopy(self.d['episode_input_contract.json']['cards'][0]);self.bad(validate_package,self.d)
    def test_route_status_mismatch(self):self.d['transport_routes.json']['routes'].pop();self.bad(validate_package,self.d)
    def test_program_changes_after_verification(self):t=self.trace();t[5]['program_hash']='changed';self.bad(validate_service_trace,t,'J1','S1')
    def test_unloaded_explicitly_unsafe(self):t=self.trace();t[7]['safe_to_handle']=False;self.bad(validate_service_trace,t,'J1','S1')
    def test_impossible_date(self):r,c=self.fixture();r['timestamp_utc']='2026-99-99T99:99:99Z';self.bad(validate_record,r,c,True)
    def test_replayed_cycle_receipts(self):
        rs=[{'cycle_index':i,'sample_id':'S1','program_receipt':'p','release_receipt':'l','recovery_receipt':'r','integrity_receipt':'q'} for i in range(1,41)];self.bad(validate_cycle_history,rs,40,'S1')
    def test_replicate_deficit(self):p,r=self.campaign();p['replicate_counts']['TENSILE_RT']=7;self.bad(evaluate_campaign,p,r,self.d)
    def test_missing_campaign_phase(self):p,r=self.campaign();r[0]['replicates'][0]['phase_receipts'].pop();self.bad(evaluate_campaign,p,r,self.d)
    def test_missing_campaign_control(self):p,r=self.campaign();r[0]['replicates'][0]['control_receipts'].pop();self.bad(evaluate_campaign,p,r,self.d)
    def test_missing_campaign_service(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events']=[r[0]['replicates'][0]['physical_events'][0]];self.bad(evaluate_campaign,p,r,self.d)
    def test_missing_campaign_specimen(self):p,r=self.campaign();r[0]['replicates'][0]['sample_id']='';self.bad(evaluate_campaign,p,r,self.d)
    def test_boolean_ancestor_claim(self):p,r=self.campaign();r[0]['prerequisite_receipts']=True;self.bad(evaluate_campaign,p,r,self.d)
    def test_missing_campaign_operation(self):p,r=self.campaign();r[0]['replicates'][0]['operation_receipts'].pop();self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_service_location(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][1]['events'][5]['station_id']='WS_QC';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_service_version(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][1]['events'][5]['version']='v0';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_service_condition(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][1]['events'][5]['condition_key']='other';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_service_material(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][1]['events'][5]['material_variant']='other';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_service_calibration(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][1]['events'][5]['calibration_id']='unknown';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_tethered_transfer(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][0]['record']['tethers_connected']=True;self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_invented_route(self):p,r=self.campaign();r[0]['replicates'][0]['physical_events'][0]['record']['route_id']='invented';self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_missing_raw_records(self):p,r=self.campaign();r[0]['replicates'][0]['raw_records']=[];self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_wrong_raw_material(self):p,r=self.campaign();r[0]['replicates'][0]['raw_records'][0]['material_variant']='other';self.bad(evaluate_campaign,p,r,self.d)
    def test_context_material_contradiction(self):t,x,c=self.bound_service();c['objects']['S1']['material_variant']='B2';self.bad(validate_service_binding,t,x,c)
    def test_multistage_phase_requirements(self):
        for bid in ['THERMAL_HINGES','MICRO_PIPE','MEMORY_VISUAL','HYBRID_STRIPS']:
            req=next(x for x in self.d['condition_requirements.json']['branches'] if x['branch_id']==bid)
            self.assertGreaterEqual(len(req['observation_stage_requirements']),2)
    def test_campaign_rejected_raw_not_completion(self):
        p,r=self.campaign()
        for raw in r[0]['replicates'][0]['raw_records']:raw['quality']='rejected'
        self.bad(evaluate_campaign,p,r,self.d)
    def test_campaign_material_cell_substitution(self):
        p,r=self.campaign();p['evidence_context']['objects']['sample_cell_0']['material_variant']='B2';self.bad(evaluate_campaign,p,r,self.d)
if __name__=='__main__':unittest.main()
