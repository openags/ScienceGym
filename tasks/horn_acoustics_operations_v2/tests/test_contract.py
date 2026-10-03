"""All fixtures below are invented bookkeeping, never source or measured acoustics."""
import copy
import heapq
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
import json
import unittest
from contract import (ROOT, POINTS, EPOCHS, load, validate_cards, validate_panel,
                      validate_condition, validate_campaign, validate_export, occurrence_graph)

def rec(i, revision='1'):
    return {'id':i,'status':'accepted','revision':revision}

def fixture():
    cards = {u['id']:{'id':u['id'],'revision':'1','qualification_receipt':'synthetic-'+u['id'],
                     'parameter_payload':{'synthetic_parameter':1},'valid_scope':'synthetic fixture only'}
             for u in load('unknown_parameters.json')['unknowns']}
    panel={'id':'panel-1','revision':'1','design':'focusing','inspection':rec('panel-inspection'),
           'positions':[{'position':i,'row':min(i,31-i),'part_id':'part-1'} for i in range(1,31)],
           'parts':{'part-1':{'job_id':'job-1','stock_lot':'ABS-1','CAD_revision':'1','revision':'1',
                            'inspection':rec('part-inspection'),'quarantined':False}}}
    conditions=[]
    for name in ['without','with']:
        c={'data_class':'synthetic_bookkeeping','name':name,'id':'condition-'+name,'pair_id':'pair-1',
           'rig_revision':'rig-1','source_config':'source-1','frequency_hz':1000,
           'reference_microphone':'mic-ref','scan_microphone':'mic-scan','reference_pose_revision':'ref-pose-1',
           'channel_map':{'reference':'mic-ref','scan':'mic-scan'},'grid_revision':'grid-1',
           'DAQ_card':'daq-1','normalization_card':'norm-1','phase_card':'phase-1','source_off_before_configuration':True,
           'source_off_after_mapping':True,'reference_stable':True,'configuration_receipt':rec('cfg-'+name),
           'archive_receipt':rec('archive-'+name),'normalization_uses_paper_data':False,
           'panel_id':'panel-1' if name=='with' else None,'panel_revision':'1' if name=='with' else None,
           'calibrations':{mic:{**rec('cal-'+mic),'valid_from':0,'valid_until':10000} for mic in ['mic-ref','mic-scan']}}
        c['calibration_ids']={mic:r['id'] for mic,r in c['calibrations'].items()}
        c['points']=[]
        for x,y in sorted(POINTS):
            attempts=[{'id':f'{name}-{x}-{y}-{slot}','slot':slot,'condition_id':c['id'],
                       'point':[x,y],'data_class':'synthetic_bookkeeping',
                       'epochs':{k:c[k] for k in EPOCHS},'complex':[slot/10,-slot/20],
                       'timestamp':x*200+y*10+slot,'valid':True,'supersedes':None} for slot in range(1,11)]
            selected=[a['id'] for a in attempts]
            c['points'].append({'x':x,'y':y,'pose_receipt':rec(f'pose-{name}-{x}-{y}'),
                                'grid_revision':'grid-1','position_accepted':True,'settled':True,
                                'attempts':attempts,'selected_readouts':selected,'average_inputs':selected.copy(),
                                'average':[.55,-.275]})
        conditions.append(c)
    campaign = {'id':'campaign-1','data_class':'synthetic_bookkeeping','cards':cards,'panel':panel,'conditions':conditions,
            'operation_receipts':{o['id']:rec('op-'+o['id']) for o in load('operations.json')['operations']},
            'cleanup_complete':True,'independent_replicates':None,'source_Table2_used_as_acquisition':False}
    bind_occurrences(campaign)
    return campaign

def bind_occurrences(campaign):
    graph=occurrence_graph(campaign);events={};sequence=0
    remaining={k:len(v) for k,v in graph.items()};following={k:[] for k in graph}
    for key,parents in graph.items():
        for parent in parents:following[parent].append(key)
    ready=[k for k,v in remaining.items() if not v];heapq.heapify(ready)
    while ready:
        key=heapq.heappop(ready);sequence+=1
        event={**rec('event-'+str(sequence)),'operation_id':key[0],'scope':key[1],'entity_id':key[2],
               'campaign_id':campaign['id'],'sequence':sequence,
               'prerequisite_events':[events[p]['id'] for p in sorted(graph[key])]}
        events[key]=event
        for child in following[key]:
            remaining[child]-=1
            if remaining[child]==0:heapq.heappush(ready,child)
    if len(events)!=len(graph):raise ValueError('Fixture graph cycle')
    campaign['panel']['inspection']['id']=events[('PANEL_INSPECT','shared','campaign')]['id']
    events[('PANEL_INSPECT','shared','campaign')]['revision']=campaign['panel']['revision']
    for pid,part in campaign['panel']['parts'].items():
        part['inspection']['id']=events[('METROLOGY','part',pid)]['id']
        events[('METROLOGY','part',pid)]['revision']=part['revision']
    for c in campaign['conditions']:
        for mic,cal in c['calibrations'].items():
            cal['id']=events[('CAL_RELEASE','microphone',mic)]['id']
            events[('CAL_RELEASE','microphone',mic)]['revision']=cal['revision']
        c['calibration_ids']={mic:cal['id'] for mic,cal in c['calibrations'].items()}
        presence='PANEL_INSTALL' if c['name']=='with' else 'PANEL_ABSENT'
        c['configuration_receipt']['id']=events[(presence,'condition',c['id'])]['id']
        c['archive_receipt']['id']=events[('CONDITION_CLOSE','condition',c['id'])]['id']
        for p in c['points']:
            point_id=f"{c['id']}:X{p['x']}Y{p['y']}"
            p['pose_receipt']['id']=events[('PROBE_MOVE','point',point_id)]['id']
            for a in p['attempts']:
                a['acquisition_event_id']=events[('POINT_READ','readout',a['id'])]['id']
    events[('PANEL_RETURN','shared','campaign')]['panel_action']='remove_installed' if campaign['conditions'][-1]['name']=='with' else 'verify_carrier'
    campaign['occurrences']=list(events.values())

class StaticTests(unittest.TestCase):
    def test_all_json_parse(self):
        for p in ROOT.rglob('*.json'): json.loads(p.read_text())
    def test_operations_are_grounded(self):
        d=load('operations.json'); self.assertEqual(d['operation_count'],44)
        ids=[o['id'] for o in d['operations']]; self.assertEqual(len(ids),len(set(ids)))
        fields=['actor','station_id','object_roles','tool_or_interface','actions','preconditions',
                'postconditions','observable_completion','authorship','failure_handling']
        for o in d['operations']:
            for field in fields:self.assertTrue(o[field],(o['id'],field))
    def test_references_resolve(self):
        evidence={e['id'] for e in load('provenance.json')['evidence']}
        gates={g['id'] for g in load('unknown_parameters.json')['unknowns']}
        stations={s['id'] for s in load('station_contracts.json')['stations']}
        operations={o['id'] for o in load('operations.json')['operations']}
        for o in load('operations.json')['operations']:
            self.assertTrue(set(o['evidence_ids'])<=evidence);self.assertTrue(set(o['unknown_parameter_ids'])<=gates)
            self.assertIn(o['station_id'],stations)
        for b in load('branches.json')['branches']:
            self.assertTrue(set(b['operation_ids'])<=operations);self.assertTrue(set(b['evidence_ids'])<=evidence)
    def test_every_operation_covered(self):
        covered={x for b in load('branches.json')['branches'] for x in b['operation_ids']}
        self.assertEqual(covered,{o['id'] for o in load('operations.json')['operations']})
    def test_dependency_graph_acyclic(self):
        d=load('dependencies.json'); graph={o['id']:set() for o in load('operations.json')['operations']}
        for e in d['edges']+d['condition_scoped_edges']:graph[e['after']].add(e['before'])
        while graph:
            ready={k for k,v in graph.items() if not v}
            self.assertTrue(ready,'Dependency cycle')
            graph={k:v-ready for k,v in graph.items() if k not in ready}
    def test_exclusive_conditions_are_scoped(self):
        d=load('dependencies.json')
        self.assertFalse(any(e['before'] in ('PANEL_ABSENT','PANEL_INSTALL') and e['after']=='CONDITION_START' for e in d['edges']))
        self.assertEqual({(e['condition'],e['before']) for e in d['condition_scoped_edges']},
                         {('with','PANEL_INSTALL'),('without','PANEL_ABSENT')})
    def test_numerical_branches_have_no_robot_operations(self):
        b=load('branches.json')['branches']; n=[x for x in b if x['kind']=='theory_or_numerical_only']
        self.assertEqual(len(n),9);self.assertTrue(all(not x['operation_ids'] for x in n))
    def test_counts_are_not_replicates(self):
        c=load('branches.json')['counts'];self.assertEqual(c['derived_minimum_valid_readouts_for_one_pair'],3800)
        self.assertIsNone(c['independent_specimen_replicates']);self.assertIsNone(c['independent_campaign_replicates'])
    def test_geometry_mirror_and_rows(self):
        g=load('geometry_reference.json');self.assertEqual(len(g['focusing']),15)
        self.assertEqual(len(g['beam_splitter_numerical_only']),15)
        self.assertEqual([x['design_row'] for x in g['mirror_map']],list(range(1,16))+list(range(15,0,-1)))
        self.assertEqual(g['focusing'][3],{'row':4,'N':13,'w':.004,'d1':.025,'CR':1.05})
    def test_actor_boundary(self):
        a=load('agent_visible.json')
        self.assertIn('source_outcomes',a['forbidden_fields']);self.assertIn('Table_2_values',a['forbidden_fields'])
        self.assertNotIn('reference_route',a['allowed_fields'])
    def test_table2_is_reference_only(self):
        t=load('source_outcomes.json')['SI_Table_2'];self.assertFalse(t['values_included']);self.assertFalse(t['raw_ten_readouts_available'])
    def test_full_source_scope(self):
        a=load('source_access_audit.json');self.assertTrue(a['source_ready_for_design']);self.assertFalse(a['robot_execution_ready'])
        self.assertEqual({s['id'] for s in a['sources']},{'MAIN_XML','MAIN_PDF','SI'})
    def test_export_exact(self):self.assertTrue(validate_export())

class ExportAdversarialTests(unittest.TestCase):
    def check_rejected(self, mutation):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'candidate';shutil.copytree(ROOT,root)
            mutation(root)
            with patch('contract.ROOT',root):
                with self.assertRaises(ValueError):validate_export()
    def test_extra_export_file(self):self.check_rejected(lambda root:(root/'unexpected.bin').write_text('synthetic'))
    def test_missing_export_file(self):self.check_rejected(lambda root:(root/'README.md').unlink())
    def test_changed_export_hash(self):self.check_rejected(lambda root:(root/'README.md').write_text('changed'))
    def test_symlink_export(self):self.check_rejected(lambda root:(root/'alias.md').symlink_to(root/'README.md'))
    def test_duplicate_allowlist(self):
        def mutate(root):
            p=root/'EXPORT_ALLOWLIST.json';d=json.loads(p.read_text());d['allowlist'].append('README.md');p.write_text(json.dumps(d))
        self.check_rejected(mutate)
    def test_incomplete_hash_inventory(self):
        def mutate(root):
            p=root/'EXPORT_ALLOWLIST.json';d=json.loads(p.read_text());d['files'].pop();p.write_text(json.dumps(d))
        self.check_rejected(mutate)

class RecordTests(unittest.TestCase):
    def setUp(self):self.c=fixture()
    def rejects(self,mutate):
        mutate(self.c)
        with self.assertRaises(ValueError):validate_campaign(self.c)
    def test_complete_pair(self):self.assertTrue(validate_campaign(self.c))
    def test_reverse_condition_order(self):
        self.c['conditions'].reverse();bind_occurrences(self.c);self.assertTrue(validate_campaign(self.c))
    def test_missing_card(self):self.rejects(lambda c:c['cards'].pop('U_CAD'))
    def test_empty_payload(self):self.rejects(lambda c:c['cards']['U_CAL'].update(parameter_payload={}))
    def test_bare_qualification(self):self.rejects(lambda c:c['cards'].update(U_FAB=True))
    def test_empty_qualification_receipt(self):self.rejects(lambda c:c['cards']['U_DAQ'].update(qualification_receipt=''))
    def test_wrong_design(self):self.rejects(lambda c:c['panel'].update(design='beam_splitter'))
    def test_wrong_mirror(self):self.rejects(lambda c:c['panel']['positions'][29].update(row=15))
    def test_fifteen_cells_not_thirty(self):self.rejects(lambda c:c['panel'].update(positions=c['panel']['positions'][:15]))
    def test_stale_panel_inspection(self):self.rejects(lambda c:c['panel'].update(revision='2'))
    def test_quarantined_part(self):self.rejects(lambda c:c['panel']['parts']['part-1'].update(quarantined=True))
    def test_missing_fabrication_ancestry(self):self.rejects(lambda c:c['panel']['parts']['part-1'].pop('job_id'))
    def test_without_contains_panel(self):self.rejects(lambda c:c['conditions'][0].update(panel_id='panel-1'))
    def test_with_stale_panel(self):self.rejects(lambda c:c['conditions'][1].update(panel_revision='2'))
    def test_duplicate_conditions(self):self.rejects(lambda c:c['conditions'][0].update(name='with'))
    def test_different_pair(self):self.rejects(lambda c:c['conditions'][1].update(pair_id='pair-2'))
    def test_source_changed(self):self.rejects(lambda c:c['conditions'][1].update(source_config='other'))
    def test_missing_condition(self):self.rejects(lambda c:c['conditions'].pop())
    def test_missing_point(self):self.rejects(lambda c:c['conditions'][0]['points'].pop())
    def test_duplicate_grid_point(self):self.rejects(lambda c:c['conditions'][0]['points'].__setitem__(1,copy.deepcopy(c['conditions'][0]['points'][0])))
    def test_missing_readout(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'].pop())
    def test_duplicate_readout_identity(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'][1].update(id=c['conditions'][0]['points'][0]['attempts'][0]['id']))
    def test_unsettled_probe(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(settled=False))
    def test_bad_position(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(position_accepted=False))
    def test_stale_pose(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(grid_revision='old'))
    def test_missing_pose_receipt(self):self.rejects(lambda c:c['conditions'][0]['points'][0].pop('pose_receipt'))
    def test_same_microphone(self):self.rejects(lambda c:c['conditions'][0].update(scan_microphone='mic-ref'))
    def test_missing_calibration(self):self.rejects(lambda c:c['conditions'][0]['calibrations'].pop('mic-ref'))
    def test_expired_calibration(self):self.rejects(lambda c:c['conditions'][0]['calibrations']['mic-ref'].update(valid_until=1))
    def test_reference_drift(self):self.rejects(lambda c:c['conditions'][0].update(reference_stable=False))
    def test_energized_reconfiguration(self):self.rejects(lambda c:c['conditions'][0].update(source_off_before_configuration=False))
    def test_source_left_running(self):self.rejects(lambda c:c['conditions'][0].update(source_off_after_mapping=False))
    def test_published_data_substitution(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'][0].update(data_class='published_reference'))
    def test_nan(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'][0].update(complex=[float('nan'),0]))
    def test_wrong_average(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(average=[42,42]))
    def test_wrong_average_ancestry(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(average_inputs=['fake']*10))
    def test_missing_cleanup(self):self.rejects(lambda c:c.update(cleanup_complete=False))
    def test_missing_fabrication_operation(self):self.rejects(lambda c:c['operation_receipts'].pop('PRINT_PROCESS'))
    def test_missing_transport(self):self.rejects(lambda c:c['operation_receipts'].pop('MOVE'))
    def test_invented_replication(self):self.rejects(lambda c:c.update(independent_replicates=10))
    def test_paper_table_as_data(self):self.rejects(lambda c:c.update(source_Table2_used_as_acquisition=True))
    def test_retry_retains_failed_attempt(self):
        p=self.c['conditions'][0]['points'][0];failed=p['attempts'][0]
        failed['valid']=False;failed['failure_reason']='synthetic overload'
        replacement=copy.deepcopy(failed);replacement.update(id='replacement-1',valid=True,supersedes=failed['id'])
        replacement.pop('failure_reason');p['attempts'].append(replacement)
        p['selected_readouts'][0]='replacement-1';p['average_inputs']=p['selected_readouts'].copy()
        bind_occurrences(self.c);self.assertTrue(validate_campaign(self.c))
    def test_retry_without_ancestry(self):
        p=self.c['conditions'][0]['points'][0];replacement=copy.deepcopy(p['attempts'][0]);replacement['id']='unbound-retry'
        p['attempts'].append(replacement)
        with self.assertRaises(ValueError):validate_campaign(self.c)
    def test_failed_selected_readout(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'][0].update(valid=False,failure_reason='synthetic fault'))

    def test_boolean_panel_position(self):self.rejects(lambda c:c['panel']['positions'][0].update(position=True))
    def test_boolean_panel_row(self):self.rejects(lambda c:c['panel']['positions'][0].update(row=True))
    def test_boolean_grid_index(self):self.rejects(lambda c:c['conditions'][0]['points'][0].update(x=True))
    def test_phase_card_changed(self):self.rejects(lambda c:c['conditions'][1].update(phase_card='other-phase'))
    def test_generic_receipts_cannot_replace_occurrences(self):self.rejects(lambda c:c.pop('occurrences'))
    def test_missing_mic_calibration_occurrence(self):
        self.rejects(lambda c:c.update(occurrences=[e for e in c['occurrences'] if not(e['operation_id']=='CAL_ACQUIRE' and e['entity_id']=='mic-ref')]))
    def test_missing_second_condition_start(self):
        self.rejects(lambda c:c.update(occurrences=[e for e in c['occurrences'] if not(e['operation_id']=='CONDITION_START' and e['entity_id']=='condition-with')]))
    def test_dependency_receipt_mismatch(self):self.rejects(lambda c:c['occurrences'][-1].update(prerequisite_events=[]))
    def test_out_of_order_occurrences(self):
        self.rejects(lambda c:c['occurrences'][-1].update(sequence=0))
    def test_raw_event_binding(self):self.rejects(lambda c:c['conditions'][0]['points'][0]['attempts'][0].update(acquisition_event_id='other'))
    def test_cleanup_location_binding(self):
        self.rejects(lambda c:next(e for e in c['occurrences'] if e['operation_id']=='PANEL_RETURN').update(panel_action='verify_carrier'))

    def test_alternative_point_order(self):
        self.c['conditions'][0]['points'].reverse();bind_occurrences(self.c);self.assertTrue(validate_campaign(self.c))
    def test_single_probe_cannot_move_before_point_reads(self):
        def mutate(c):
            first_read=next(e for e in c['occurrences'] if e['operation_id']=='POINT_READ' and e['entity_id']=='without-1-1-1')
            next_move=next(e for e in c['occurrences'] if e['operation_id']=='PROBE_MOVE' and e['entity_id']=='condition-without:X1Y2')
            first_read['sequence'],next_move['sequence']=next_move['sequence'],first_read['sequence']
        self.rejects(mutate)
    def test_detached_calibration_receipt(self):
        self.rejects(lambda c:c['conditions'][0]['calibrations']['mic-ref'].update(id='unbound'))
    def test_detached_panel_inspection(self):self.rejects(lambda c:c['panel']['inspection'].update(id='unbound'))
    def test_detached_part_inspection(self):self.rejects(lambda c:c['panel']['parts']['part-1']['inspection'].update(id='unbound'))

    def test_stale_calibration_event_revision(self):
        self.rejects(lambda c:next(e for e in c['occurrences'] if e['operation_id']=='CAL_RELEASE').update(revision='stale'))
    def test_stale_panel_event_revision(self):
        self.rejects(lambda c:next(e for e in c['occurrences'] if e['operation_id']=='PANEL_INSPECT').update(revision='stale'))
    def test_stale_metrology_event_revision(self):
        self.rejects(lambda c:next(e for e in c['occurrences'] if e['operation_id']=='METROLOGY').update(revision='stale'))
    def test_detached_condition_configuration(self):self.rejects(lambda c:c['conditions'][0]['configuration_receipt'].update(id='unbound'))
    def test_detached_condition_archive(self):self.rejects(lambda c:c['conditions'][0]['archive_receipt'].update(id='unbound'))

if __name__=='__main__':unittest.main()
