"""Final semantic selectors and byte pins. No physical geometry qualification."""
from pathlib import Path,PurePosixPath
import json,hashlib,sys,math,struct
ROOT=Path(__file__).resolve().parents[1]
REQUIRED_PINS={'affordances.json','asset_inventory.json','assembly_contract.json','operation_binding_contract.json','operation_bindings.json','semantic_controls.py','states.json','specimen_geometry.json','asset_metadata.json','geometry/conformal_lab.glb','geometry/conformal_lab.blend'}
class PairingError(ValueError):pass
def require(ok,msg):
 if not ok:raise PairingError(msg)
def glb_world(path):
 raw=Path(path).read_bytes();require(len(raw)>=20,'GLB header');magic,version,total=struct.unpack_from('<4sII',raw)
 require(magic==b'glTF' and version==2 and total==len(raw),'GLB identity/length');offset=12;chunks=[]
 while offset<len(raw):
  require(offset+8<=len(raw),'GLB chunk header');size,kind=struct.unpack_from('<II',raw,offset);offset+=8
  require(size%4==0 and offset+size<=len(raw),'bounded aligned GLB chunk');chunks.append((kind,raw[offset:offset+size]));offset+=size
 require(len(chunks)==2 and chunks[0][0]==0x4e4f534a and chunks[1][0]==0x004e4942,'JSON/BIN GLB chunks')
 def pairs(items):
  out={}
  for k,v in items:require(k not in out,'duplicate GLB JSON key');out[k]=v
  return out
 j=json.loads(chunks[0][1].decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(PairingError('nonfinite GLB JSON')))
 require(len(j.get('scenes',[]))==1 and j.get('scene',0)==0,'one default scene');require(all('uri' not in b for b in j.get('buffers',[])),'embedded geometry only')
 nodes=j['nodes'];names=[n.get('name') for n in nodes];require(all(type(n) is str and n for n in names) and len(names)==len(set(names)),'unique concrete GLB names')
 def finite(xs,n):require(type(xs) is list and len(xs)==n and all(type(x) in (int,float) and math.isfinite(x) for x in xs),'finite GLB transform')
 def mul(a,b):return [[sum(a[i][k]*b[k][z] for k in range(4)) for z in range(4)] for i in range(4)]
 def local(n):
  if 'matrix' in n:
   require(not any(k in n for k in ('translation','rotation','scale')),'matrix or TRS only');m=n['matrix'];finite(m,16);return [[m[c*4+r] for c in range(4)] for r in range(4)]
  t=n.get('translation',[0,0,0]);q=n.get('rotation',[0,0,0,1]);sc=n.get('scale',[1,1,1]);finite(t,3);finite(q,4);finite(sc,3)
  require(abs(sum(x*x for x in q)-1)<1e-4,'normalized GLB quaternion');x,y,z,w=q
  r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
  return [[r[i][k]*sc[k] for k in range(3)]+[t[i]] for i in range(3)]+[[0,0,0,1]]
 world={};owners={};objects={};visited=set();identity=[[1 if i==k else 0 for k in range(4)] for i in range(4)]
 def visit(idx,parent,owner):
  require(type(idx) is int and 0<=idx<len(nodes) and idx not in visited,'unique acyclic GLB hierarchy');visited.add(idx);n=nodes[idx];name=n['name'];m=mul(parent,local(n))
  if name.startswith('ASSET.'):
   require(owner is None,'nested asset roots');owner=name[6:]
  require(owner is not None,'every node owned by family root');owners[name]=owner;world[name]=[m[0][3],-m[2][3],m[1][3]];objects[name]=n
  for child in n.get('children',[]):visit(child,m,owner)
 for idx in j['scenes'][0]['nodes']:visit(idx,identity,None)
 require(len(visited)==len(nodes),'no orphan GLB nodes');return world,owners,objects

def verify(asset_root,task_root=ROOT):
 a=Path(asset_root);require(a.is_dir() and not a.is_symlink(),'regular asset directory')
 for parent in a.absolute().parents:require(not parent.is_symlink(),'regular asset ancestor')
 task=json.loads((Path(task_root)/'asset_binding_plan.json').read_text());require(task['status']=='frozen_nominal_pairing','final asset freeze required');pins=task['final_asset_hashes']
 require(len(pins)==len({x['path'] for x in pins}) and {x['path'] for x in pins}==REQUIRED_PINS,'exact required pins')
 for pin in pins:
  name=pin['path'];p=PurePosixPath(name);require(not p.is_absolute() and str(p)==name and '..' not in p.parts,'canonical pin path');f=a/name;require(f.is_file() and not f.is_symlink(),'regular asset pin file')
  for parent in f.parents:
   require(not parent.is_symlink(),'regular asset pin ancestor')
   if parent==a:break
  data=f.read_bytes();require(len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],'final asset byte hash: '+name)
 def read(n):return json.loads((a/n).read_text())
 glb_positions,glb_owners,glb_objects=glb_world(a/'geometry/conformal_lab.glb')
 contract=read('operation_binding_contract.json');second=read('operation_bindings.json');aff=read('affordances.json');inv=read('asset_inventory.json');meta=read('asset_metadata.json')
 require(contract['operations']==second['bindings'],'duplicate binding views agree')
 require(contract['asset_pack_id']==task['asset_pack_id'] and contract['task_id']=='conformal_operations_v3_compressed','package identity');require(meta['physical_execution_enabled'] is False and meta['scientific_result_reproduced'] is False,'qualification boundary')
 roots={x['id']:x['root'] for x in inv['assets']};objects={p['name']:p for x in inv['assets'] for p in x['objects']};owners={p['name']:x['id'] for x in inv['assets'] for p in x['objects']};anchors={x['name']:x for x in aff['anchors']};scene_ops={x['operation_id']:x for x in contract['operations']}
 require(len(roots)==12 and len(scene_ops)==16,'pair counts');require(len(objects)==sum(len(x['objects']) for x in inv['assets']),'unique scene object names');require(len(anchors)==len(aff['anchors']),'unique anchor names')
 require(len(task['operation_bindings'])==16 and len({b['operation_id'] for b in task['operation_bindings']})==16,'complete unique task binding IDs');count=0
 for b in task['operation_bindings']:
  o=scene_ops[b['operation_id']]
  for k in ['asset_ids','primary_asset_id','primary_target','control_target']:require(b[k]==o[k],'exact scene/task '+k+' '+b['operation_id'])
  require(b['root_node_ids']==[roots[x] for x in b['asset_ids']],'root ownership');require(o['primary_asset_id'] in o['asset_ids'],'primary family membership')
  for kind in ('primary','control'):
   name=o[kind+'_anchor'];require(name in b['anchor_ids'] and name in anchors,'anchor identity');r=anchors[name];target=o[kind+'_target'];require(target in objects and objects[target]['type']=='MESH','concrete target mesh')
   require(r['target_mesh']==target and r['owner']==owners[target]==o['primary_asset_id'],'concrete target ownership');pos=r['position_m'];require(len(pos)==3 and all(type(x) in (float,int) and math.isfinite(x) for x in pos),'finite nominal anchor')
   require(all(abs(x-y)<1e-6 for x,y in zip(pos,objects[target]['position_m'])),'world target correspondence');require(b['anchor_positions_m'][name]==pos,'pinned nominal anchor coordinates');require(name in glb_objects and target in glb_objects and 'mesh' in glb_objects[target],'concrete GLB anchor/mesh')
   require(glb_owners[name]==glb_owners[target]==o['primary_asset_id'],'actual GLB family ownership')
   require(glb_objects[name].get('extras',{}).get('target_mesh')==target and glb_objects[name].get('extras',{}).get('qualified_pose') is False,'GLB anchor target metadata')
   for actual in (glb_positions[name],glb_positions[target]):require(all(abs(x-y)<1e-6 for x,y in zip(pos,actual)),'actual GLB world-space binding')
   require(r['qualified_pose'] is False and r['physical_execution_enabled'] is False,'unqualified anchors');count+=1
  require(b['physical_qualified'] is False,'task unqualified pose')
 return {'passed':True,'operation_bindings':16,'anchor_bindings':count,'pinned_asset_files':len(pins),'physical_execution':False,'geometry_qualification':False}
if __name__=='__main__':
 try:
  require(len(sys.argv)==2,'Supply separate asset package directory');print(json.dumps(verify(sys.argv[1]),indent=2))
 except (PairingError,OSError,KeyError,ValueError) as e:print(str(e));sys.exit(1)
