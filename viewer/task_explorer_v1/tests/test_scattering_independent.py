"""Independent audit: frozen ZIP bytes are oracle; never import an adapter.

Read-only against the checkout; mutations are in-memory hostile copies.
Expected per-file SHA-256 values were independently extracted from the two frozen
release ZIPs named in PACKAGES. No adapter module or projection helper is imported.
Not paper rereading, physics testing, or scientific validation.
"""
import copy, hashlib, json, os, pathlib, re, unittest, zipfile
HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path(os.environ['SCIENCEGYM_ROOT']).resolve() if 'SCIENCEGYM_ROOT' in os.environ else pathlib.Path(__file__).resolve().parents[3]
VIEW = ROOT/'viewer/task_explorer_v1'
PACKAGES = {'task': ('tasks/scattering_operations_v2', 'scattering_operations_v2.metadata_20261005.zip', '02cf39abb287bed41d282a4996a50d51630713c98d4b9adf244452c8fd06f74b'), 'asset': ('assets/scattering_scene_assets_v1', 'scattering_scene_assets_v1.metadata_20261005.zip', '241e32c2812a2ed534044a99ecc380c67c5e2e26f9d7a12255b599233d1acb78')}
FROZEN_FILES = {'task': {'EXPORT_ALLOWLIST.json': 'e10a331aef4ed77c9bdeb1840ae4a0249a88898c832152e10ca278e377fc86fc', 'EXPORT_SCOPE.md': 'e94e5b0914992d4832cc05064fd4c71f45e160accbf11210a9f2b58110159719', 'README.md': 'f0885a9d9fdd5e34da373e8e2a26d52db342ad5d09df07fb30868d06673cf031', 'STATUS.json': '40c0967d01594a94da20ba03d64e9c3f59fbfec2c0771e8701ccbc96e82ba635', 'TASK_DESIGN.md': '98de304e4d9869323b0f60abf1c05ae5e8e85363552b17ae29fea5b8afbf97cd', 'VERIFICATION.json': 'a0be19d05dd7b089842ddd1629ef1b9603f5197506ca81094024960903c8c267', 'agent_visible.json': '3ff1498ae11a67a447e875857a0dfbd8b0d59e10cb4e72f9ade3c3d069e2d9fc', 'branches.json': '81743ba5de1a25dc0b49fb69255f854e2dd007ffb1494f90e22df944ed0421ee', 'controls_and_repeats.json': 'f74276bb485b34f3932fd91998b3a9f62ea19003a9966f419f29761693baa834', 'coverage_map.json': 'c44ea8cfa7f4728f45c555d7a2578d95061c19baa7056501ba18f18a6f3be02f', 'evaluator_reference.json': '2ab0d86857574e8479c5241ffd2e619723ca0ec5b221c2975e925d2a4344844b', 'failure_contract.json': '385598678c2a1c32b5e8b3639c3e12e0a469780def02744db9771d36ced88349', 'lineage_contract.json': '73527a25963bfe9d53cfdd72e6b60e8a2020b166ba12202668589f5e231ff553', 'material_and_sample_dependencies.json': '486930fd439cfdfa43c8646abf6663f65d145b898ae2b754b8798aba8c5c32dd', 'measurement_contract.json': '27abc21f7beadd3602a58e73245dafaa5d8fa9ee88fd3a247a4e28301f8c0c50', 'operations.json': 'dd8aa103ca0be0c459e953b6f20ab6076f36f4b00ed16f7f2a9b4fc7f13b21b0', 'paired_asset_reference.json': '65fdbeb530af734bb4057184621548d804acbcda556c2432bff9033aa3c1237a', 'provenance.json': 'd160df2afab19fc470425aed9901757ba646ee43340d898a6c8a5e14875c8fb1', 'read_coverage.json': '426ba8219dc94c7079016176f5384dd40f80697c83069e041bc0a4dd3f41888e', 'release_boundary.json': '650d92a1840d451ff4d7b9d2ad96909a1d7a6621379ef51c4f616528c4830cd7', 'review/INDEPENDENT_REVIEW.json': '9219890d920f31503820ffe33dfa8e29176f86804b6188235620373a3eb72675', 'review/INDEPENDENT_REVIEW.md': '9e6abc8386b4047f93e81343adef45d2842c1b38a9a8fb085b36eeb105296fe0', 'review/test_independent_contract.py': 'c6d847344bd7c42fe51f336aa46122ed45277a1cb4101f4be919916b8c67ce83', 'review/test_independent_export.py': '3eb0cacc29d81e8b3116ec543864341291edb0d65a19f56bf581c95c2206f4d8', 'safety_boundaries.json': 'fa37d3c3ccc293b84c9265de456284561ec931b987ea2352f5999b8d910174a7', 'shared_binding_contract.json': 'c601bb0f9c856273da02570e4991022019cdce4e03a614db0fbf031a7d2bae93', 'source_conflicts.json': '46506e79eb5831da7ce279f446eb614b741be1ead8a9211f8676bb58190a9d5d', 'source_evidence.json': 'ded5ea261b048e4499f78b299b1374fcd9860f9d6b3897582f5165cf2da3a32e', 'source_table_inventory.json': '113c5b589457444692f9996f62d91faad2416dc1e2a08be113db8e7451c36599', 'source_update_status.json': '588fe9da1af17377057dba9d6ff601835d257a63421315bfb2dc765d37ac051a', 'station_contracts.json': '31b3c7399e14c59c2e35661e0e84dd80c0a4f6ed2f2afad7f384c46aba006e4c', 'tests/contract.py': 'e896edc7328ae4707aa06856f08751dd11d3e471035bfea2559422a1126d7a6b', 'tests/test_contract.py': 'cc2fa8219e8e689b2e137fd22026bf208497e6b655f11eff6eca3969bf8a6bdd', 'tests/test_export.py': '401075e84f8f49f1d75eefdd6a115fafd73cb014f6860b0beb222f4edd766b2d', 'tests/verify_export.py': '88292fa5bc4e77a27ca2732c764b263508eeca5140dba92e84b68db32df703b3', 'tests/verify_package.py': '02ce2a9d04c568d6dc11999f8d3fdefa9619b5447c978b778abcf2b5a15f1a07', 'unknowns.json': '10244a22deb0672b706fd4cf2993ee90b958f24b4e92ec208df4eff9c33bb73f', 'workflow.json': '304492b234c60f8104a1bbb429edf6cba6dbfe544189bcdee52a2d034265809c'}, 'asset': {'DELIVERABLE_MANIFEST.json': '8154b0c165f8cc79dc87ba265ef012b69c23c94975fb1a104cf19d84b359f2c8', 'EXPORT_ALLOWLIST.json': '98b4c7cc6f6534f307c121446cf9d8be13140dcadb600cd83f68ed20d6318394', 'MANIFEST.sha256': 'de3de9c6d2ec1866e4655de0721bfc67eca458a1eb20757a88ff62d0d678f914', 'README.md': 'd9f7cef1b45a10b98507b7c89a63706a89bfabc90a8241230f6ea1408bc3fcfa', 'asset_binding_contract.json': 'c601bb0f9c856273da02570e4991022019cdce4e03a614db0fbf031a7d2bae93', 'blender_validation.json': '0f0d914dd18b9f2384b4c6a57f9c7270092a6e6e8ae9f18f8b0c30c77e6bd613', 'build_scene.py': '0fe93c806ea30f7f0bb394bc27aeb84221890043009008ed0137104c86c3f5b8', 'export_package.py': '92bac9eec201a95911df2d182af052b1c50c65e5a56667cb97ce1aba5deb1559', 'guard_test_results.json': '221cb18d18328ddf1b5af5ce82a8123c5108045ea373ea8622a29e93af9e128c', 'independent_guard_probe_results.json': '938c34237ecba26826b725625a1130540f51551275ae762254fe9cfb1e35080e', 'independent_guard_probes.py': '60076bc722411fc939e071d454a977fb42fd6beb69c896dab9d0f30ba286e5fe', 'independent_review.json': '4d2eb00b822f5ab017bdb303f237d0786f3c910bcef1746e8b9a18acdfa1c650', 'independent_review.md': '91663fc4b393427734201580fb7faf4153e6afd6ffc23dc7e61c89f14b2a678d', 'metadata_sanitization.json': '37b7e25f1b46d8af5befad80b3c10d83dcacb6a8b856d0f5a530f91f316df8a6', 'paired_task_core_reference.json': '23f90891d3b2933002dabebfeb11af8d77362fa06cb4bc9d9005bc5d609577a4', 'preview_01_overview.png': '418ae6e6967b3563fb08c35a5bdc513c1766ab19d9de73c036a50343ae9cf347', 'preview_02_preparation.png': '6cd61e63232438dfccfc5a1ff16f9613224009a8ab79b4a16e3a1370bfa9508d', 'preview_03_metrology.png': '4a8d25ee85383ab75abb3d05e60895269867bd00104851bd663c27632b6e957c', 'provenance.json': '6c58e3416d94da89b16f14bb03b4d3dbb71c2c5c7fc71f96b7ff1fdd84c45307', 'render_receipt.json': '1e4a62747e504eb185421512ca01c819c4b79096d0c7a5fa3c3154407b0ca391', 'sanitize_metadata.py': '12e46bd23b944e479f6066b6f0504b750542795f9b77a37233f2a039a4e65ac7', 'scattering_review_scene.blend': 'bc1f0b984f17df960e8be967b18bde431b6f77ab11b316a0a87fb5a8e72dc7c0', 'scattering_review_scene.glb': '9785a801b1f56ace3bcdfdaaebf07c40436c1739b710d45febee7c865a36e7c4', 'scene_core_manifest.json': '6796beafda712e604e01a04a1f38ea107c73223898945ac6f4d379b1164a8663', 'scene_guards.py': '9817088523ff978b99d5cdca1ca1bd52a42556a32c15f44af681c6942e3809df', 'scene_manifest.json': '2e6319afd92729041375ebcae647c841108f246ee555a461fb274d232edef240', 'test_scene_guards.py': '6dc322f38524e80f326d7bda2b309b96f5b869ee5a4898fbb4698ed0c7b2c51c', 'verify_pair.py': '65dd966f16193aa8269f421ffac495bdfb6726def3cdd515d8d656ff7e9ec78e', 'verify_scene.py': '58e65535f855e324314188eae81514d91e6e66dd99aac72abc234b7aceb596ca'}}
ALIASES={'evaluator_reference.json':'acceptance','lineage_contract.json':'lineage'}
BRANCH_KINDS={'P01':'preparation_support','P02':'preparation_support','P03':'calibration_support', **{f'B{i:02}':'reported_experimental_branch' for i in range(1,6)}, **{f'A{i:02}':'numerical_review_only' for i in range(1,5)}, 'CLOSE':'authored_closeout'}
def load(p):return json.loads(p.read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
def unpool(f,v):
 if isinstance(v,dict):
  if set(v)=={'$shared'}:return unpool(f,f['shared'][v['$shared']])
  return {k:unpool(f,x) for k,x in v.items()}
 if isinstance(v,list):return [unpool(f,x) for x in v]
 return v
def walk(nodes):
 for n in nodes:
  yield n
  yield from walk(n.get('children',[]))
def pointer(doc,p):
 if p:
  assert p.startswith('/')
  for tok in p[1:].split('/'):
   tok=tok.replace('~1','/').replace('~0','~')
   doc=doc[int(tok)] if isinstance(doc,list) else doc[tok]
 return doc

def audit(f,docs,raw,assetdocs=None,assetraw=None):
 """Independent semantic oracle used also for hostile mutation sensitivity."""
 expected={ALIASES.get(n,n.removesuffix('.json')):v for n,v in docs.items()}
 assert len(expected)==27
 expected['static_assets']=assetdocs
 assert f['context']==expected,'All task and asset source JSON, including review, must remain lossless'
 assert set(f['source_files'])==set(docs)|{'static_assets/'+n for n in assetdocs}
 for name,v in f['source_files'].items():
  if name.startswith('static_assets/'):
   aname=name[len('static_assets/'):]; assert v['sha256']==digest(assetraw[aname])
   assert v['url']=='../../assets/scattering_scene_assets_v1/'+aname
   assert v['repository_path']=='assets/scattering_scene_assets_v1/'+aname
   continue
  assert v['sha256']==digest(raw[name]),name
  assert v['url']=='../../tasks/scattering_operations_v2/'+name,name
  assert v['repository_path']=='tasks/scattering_operations_v2/'+name,name
 assert f['source_commit'] is None
 assert f['source_archive_sha256']==PACKAGES['task'][2]
 assert f['asset_archive_sha256']==PACKAGES['asset'][2]
 assert f['id']=='scattering'
 assert f['family_scope']=='paper_level_design'
 assert f['visibility']=='author_evaluator_reference_only'
 assert f['actor_projection_implemented'] is False
 assert f['default_route']=='HOLD_QUALIFICATION'
 rawops=docs['operations.json']['operations']
 assert [o['id'] for o in f['operations']]==[f'R{i:02}' for i in range(1,15)]
 for i,(o,m) in enumerate(zip(rawops,f['operations'])):
  assert m['detail']==o,o['id']+' full detail'
  assert m['source_file']=='operations.json'
  assert m['source_pointer']==f'/operations/{i}'
  assert pointer(docs[m['source_file']],m['source_pointer'])==o
  assert m['title']==o['name']
  assert m['stage']==o['station_id']
  assert m['actions'] in (o['action'],[o['action']])
  assert m['pre'] in (o['precondition'],[o['precondition']])
  assert 'No ' in m['post'] and 'field supplied' in m['post'],'Absent post-state must be explicit'
  assert 'original_authored_robot_task_design' in json.dumps(m['provenance'])
  assert o['physical_execution_enabled'] is False
  assert o['action_interface']['numeric_or_hardware_arguments_allowed'] is False
  assert m['objects']=={k:o[k] for k in ('asset_ids','anchor_ids')}
  assert m['acceptance']=={k:o[k] for k in ('required_receipt_types','required_outputs','completion_evidence','guard')}
  assert m['recovery']==o['on_failure']
  assert m['sources']==[], 'No per-operation source-fact mapping should be invented'
  assert m['loop'] is None,'Unknown repeated attempts must not become expanded/default loops'
 branches=docs['branches.json']['branches']; rs={r['id']:r for r in f['routes']}
 assert len(rs)==len(f['routes'])==18,'13 source branches + 4 reference views + 1 hold'
 assert set(rs)==set(BRANCH_KINDS)|{'OPERATIONS_REFERENCE','CONTROLS_REFERENCE','FAILURE_REFERENCE','BINDINGS_REFERENCE','HOLD_QUALIFICATION'}
 assert {b['id']:b['source_reported_kind'] for b in branches}==BRANCH_KINDS
 for i,b in enumerate(branches):
  r=rs[b['id']]
  assert r['detail']==b,b['id']+' detail'
  assert r['route_kind']==b['source_reported_kind'],b['id']+' kind'
  assert r['source_file']=='branches.json' and r['source_pointer']==f'/branches/{i}'
  ns=list(walk(r['nodes'])); ops=[n for n in ns if n['type']=='op']
  assert [n['id'] for n in ops]==b['operation_ids'],b['id']+' exact memberships'
  for n in ns:
   if n['type']=='op':
    m=n['meta']; assert pointer(docs[m['source_file']],m['source_pointer'])==n['id']
   elif n.get('children'):assert n.get('ordered') is False,'Membership must not invent chronological arrows'
  assert b['default_repeat_count'] is None
  assert b['required_source_outcome_for_success'] is None
  assert b['physical_executed'] is False and b['numerical_executed'] is False
 assert len([r for r in f['routes'] if r['route_kind']=='reported_experimental_branch'])==5
 assert len([r for r in f['routes'] if r['route_kind']=='numerical_review_only'])==4
 for r in f['routes']:
  assert pointer(docs[r['source_file']],r['source_pointer'])==r['detail'],r['id']+' source pointer'
  for n in walk(r['nodes']):
   m=n.get('meta',{})
   if 'source_contract' in m:assert pointer(docs[m['source_file']],m['source_pointer'])==m['source_contract']
 h=rs['HOLD_QUALIFICATION'];assert h['metadata_only'] is True
 assert not [n for n in walk(h['nodes']) if n['type']=='op']
 assert 'HOLD_QUALIFICATION' not in [o['id'] for o in f['operations']]
 assert f['evidence']=={e['id']:e for e in docs['source_evidence.json']['facts']}
 dep=f['dependencies']
 for name in ['workflow','material_and_sample_dependencies','lineage_contract','measurement_contract','station_contracts','failure_contract']:
  assert dep.get(name)==docs[name+'.json'],name+' dependencies must be exact'
 assert not dep.get('edges'), 'No invented universal cross-branch edges'
 status=(f['status']+' '+f['source_warnings']+' '+f['asset_boundary']).lower()
 for token in ['whole-paper','design','no','qualification','unqualified','numerical','physical','source','authored']:
  assert token in status,token+' boundary'
 assert len(f['asset_links'])==4
 for item in f['asset_links']:
  assert item['url'].startswith('../../assets/scattering_scene_assets_v1/')
  assert item['path']=='assets/scattering_scene_assets_v1/'+item['url'].split('scattering_scene_assets_v1/')[1]
 return True

class FrozenOracle(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw={k:{n:(ROOT/v[0]/n).read_bytes() for n in FROZEN_FILES[k]} for k,v in PACKAGES.items()}
  cls.docs={n:json.loads(b) for n,b in cls.raw['task'].items() if n.endswith('.json')}
  cls.assetdocs={n:json.loads(b) for n,b in cls.raw['asset'].items() if n.endswith('.json')}
  p=load(VIEW/'data/scattering.json');cls.pooled=p;cls.f=unpool(p,p)
 def test_01_exact_archives_and_extracted_packages(self):
  for key,(folder,zfile,sha) in PACKAGES.items():
   files={p.relative_to(ROOT/folder).as_posix() for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}
   self.assertEqual(files,set(self.raw[key]))
   for name,b in self.raw[key].items():self.assertEqual(digest(b),FROZEN_FILES[key][name],name)
 def test_02_frozen_source_oracle(self):audit(self.f,self.docs,self.raw['task'],self.assetdocs,self.raw['asset'])
 def test_04_binding_bijections_and_exact_reciprocal_pins(self):
  t=self.docs['shared_binding_contract.json'];a=self.assetdocs['asset_binding_contract.json']
  self.assertEqual(self.raw['task']['shared_binding_contract.json'],self.raw['asset']['asset_binding_contract.json'])
  self.assertEqual(len(t['asset_groups']),11);self.assertEqual(len(t['operation_bindings']),14)
  sm=self.assetdocs['scene_manifest.json'];self.assertEqual(len(sm['anchors']),32)
  self.assertEqual(sm['operation_ids'],[f'R{i:02}' for i in range(1,15)])
  for p in self.assetdocs['paired_task_core_reference.json']['files']:
   self.assertEqual(digest(self.raw['task'][p['path']]),p['sha256']);self.assertEqual(len(self.raw['task'][p['path']]),p['bytes'])
  for name,p in self.docs['paired_asset_reference.json']['stable_scene_files'].items():
   self.assertEqual(digest(self.raw['asset'][name]),p['sha256']);self.assertEqual(len(self.raw['asset'][name]),p['bytes'])
  for item in self.f['asset_links']:
   name=item['url'].split('scattering_scene_assets_v1/')[1];self.assertEqual(item['sha256'],digest(self.raw['asset'][name]))
 def test_05_source_counts_and_repeat_prohibitions(self):
  self.assertEqual(len(self.docs['unknowns.json']['unknowns']),16)
  self.assertEqual(len(self.docs['source_conflicts.json']['records']),8)
  self.assertEqual(len(self.docs['controls_and_repeats.json']['controls']),12)
  for key in ['source_independent_specimen_count','source_independent_repeat_count','prospective_default_repeat_count']:
   self.assertIsNone(self.f['context']['controls_and_repeats'][key])
  self.assertEqual(self.f['context']['read_coverage']['MOVIES']['sampled_visual_frames'],{'1':6,'2':6,'3':5})
  self.assertIs(self.f['context']['read_coverage']['MOVIES']['continuous_visual_review'],False)
  self.assertEqual(self.f['context']['release_boundary']['paper_design_count'],1)
  self.assertEqual(self.f['context']['release_boundary']['actual_hardware_actions'],0)
  self.assertEqual(self.f['context']['release_boundary']['physical_simulations'],0)
  self.assertEqual(self.f['context']['release_boundary']['scientific_reproductions'],0)
 def test_06_data_js_exactly_matches_json(self):
  js=(VIEW/'data/scattering.js').read_text();prefix='window.SCIENCEGYM_DATA=window.SCIENCEGYM_DATA||{};window.SCIENCEGYM_DATA["scattering"]='
  self.assertTrue(js.startswith(prefix));self.assertEqual(json.loads(js[len(prefix):].strip().removesuffix(';')),self.pooled)
  self.assertIn('data/scattering.js',(VIEW/'index.html').read_text())
 def test_07_independent_oracle_detects_hostile_semantic_mutations(self):
  def route(f,id):return next(r for r in f['routes'] if r['id']==id)
  mutations={
   'drop_nested_review':lambda f:f['context'].pop('review/INDEPENDENT_REVIEW'),
   'physical_numerical_conflation':lambda f:route(f,'A01').update(route_kind='reported_experimental_branch'),
   'invent_replication':lambda f:f['context']['controls_and_repeats'].update(prospective_default_repeat_count=3),
   'source_outcome_as_success':lambda f:route(f,'B01')['detail'].update(required_source_outcome_for_success='match paper'),
   'action_as_observation':lambda f:f['operations'][0].update(post=f['operations'][0]['detail']['required_outputs']),
   'erase_failure_history':lambda f:f['context']['failure_contract'].update(on_fault=[]),
   'erase_required_receipt':lambda f:f['operations'][1]['detail'].update(required_receipt_types=[]),
   'wrong_pointer':lambda f:f['operations'][5].update(source_pointer='/operations/7'),
   'invent_dependency':lambda f:f['dependencies'].update(edges=[['B01','B02']]),
   'activate_hold':lambda f:route(f,'HOLD_QUALIFICATION').update(metadata_only=False),
   'drop_source_hash':lambda f:f['source_files']['unknowns.json'].update(sha256='0'*64),
   'resolve_unknown':lambda f:f['context']['unknowns'].update(default_resolution='all_clear'),
   'review_scope_inflation':lambda f:f['context']['read_coverage']['MOVIES'].update(continuous_visual_review=True),
   'science_count_inflation':lambda f:f['context']['release_boundary'].update(paper_design_count=5),
   'actor_projection':lambda f:f.update(actor_projection_implemented=True),
  }
  rejected=[]
  for name,mut in mutations.items():
   f=copy.deepcopy(self.f);mut(f)
   with self.subTest(mutation=name):
    try:audit(f,self.docs,self.raw['task'],self.assetdocs,self.raw['asset'])
    except (AssertionError,KeyError,TypeError):rejected.append(name)
    else:self.fail('Undetected mutation: '+name)
  self.assertEqual(len(rejected),15)

if __name__=='__main__':unittest.main(verbosity=2)
