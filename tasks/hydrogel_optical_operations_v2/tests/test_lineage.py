import unittest
from contract import fixture,validate
class LineageTests(unittest.TestCase):
 def test_lineage_mutations(self):
  cases={
  'missing_allocations':lambda c,e:c.pop('condition_allocations'),
  'missing_lineage':lambda c,e:c.pop('lineage'),
  'missing_batch_registry':lambda c,e:c.pop('batches'),
  'batch_material_swap':lambda c,e:next(iter(c['batches'].values())).update(material='other'),
  'batch_unqualified':lambda c,e:next(iter(c['batches'].values())).update(qualified=False),
  'missing_parent_batches':lambda c,e:next(iter(c['lineage'].values())).update(parent_batch_ids=[]),
  'collapsed_cover':lambda c,e:next(iter(c['lineage'].values())).update(cover_id=next(iter(c['lineage'].values()))['substrate_id']),
  'missing_map':lambda c,e:next(iter(c['lineage'].values())).update(geometry_hash=None),
  'missing_job_lineage':lambda c,e:next(iter(c['lineage'].values())).update(service_job_ids=[]),
  'wrong_hydrogel':lambda c,e:next(iter(c['lineage'].values())).update(hydrogel_material='other'),
  'wrong_resist':lambda c,e:next(iter(c['lineage'].values())).update(resist_material='other'),
  'destroyed_lineage':lambda c,e:next(iter(c['lineage'].values())).update(damage_state='destroyed'),
  'allocation_rewrite':lambda c,e:next(iter(c['condition_allocations'].values())).update(condition_id='{}'),
  'allocation_material_swap':lambda c,e:next(iter(c['condition_allocations'].values())).update(material_class='other'),
  'extra_event':lambda c,e:e.append(dict(e[0])),
  'malformed_selected':lambda c,e:c.update(selected_branches=1),
  'malformed_event_id':lambda c,e:e[0].update(event_id=[]),
  'malformed_jobs':lambda c,e:c.update(jobs=[]),
  }
  for name,fn in cases.items():
   with self.subTest(case=name):
    c,e=fixture();fn(c,e);self.assertTrue(validate(c,e))
 def test_image_count_merge(self):
  c,e=fixture(['ANGLE_IMAGE_VIDEO']);a=next(a for a in c['condition_allocations'].values() if a['branch_id']=='ANGLE_IMAGE_VIDEO');a['source_unit_count']=10000;self.assertTrue(validate(c,e))
 def test_sem_reuse(self):
  c,e=fixture(['THREE_D']);a=next(a for a in c['condition_allocations'].values() if a['branch_id']=='THREE_D');a['service_specimens']['CONFOCAL']=a['service_specimens']['SEM'];self.assertTrue(validate(c,e))
 def test_ip_s_required(self):
  c,e=fixture(['THREE_D']);j=next(j for j in c['jobs'].values() if j['branch_id']=='THREE_D');c['lineage'][j['specimen_id']]['resist_material']='DEGRAD_INX_N100';self.assertTrue(validate(c,e))
 def test_incompatible_control_dependency(self):
  c,e=fixture(['SQUARE_LATTICES']);self.assertIn('INCOMPATIBLE_CONTROL',c['plans']);c['plans'].pop('INCOMPATIBLE_CONTROL');self.assertTrue(validate(c,e))
 def test_parent_condition_swap(self):
  c,e=fixture(['HYDROGEL_CONTROLS']);j=next(j for j in c['jobs'].values() if j['branch_id']=='HYDROGEL_CONTROLS');j['parents']=[jid for jid,v in c['jobs'].items() if v['branch_id']=='PREP_COUPON' and v['condition_id']!=j['condition_id']];self.assertTrue(validate(c,e))
if __name__=='__main__':unittest.main()
