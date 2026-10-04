"""Modified original ScienceGym exporter for the wetting contract allowlist.
Exact bounded text-only export; reject unknown members, aliases and symlinks.
"""
from pathlib import Path,PurePosixPath
import hashlib,json,stat,sys,zipfile,os,tempfile
from verify_package import read
ROOT=Path(__file__).resolve().parents[1]
CORE=['EXPORT_SCOPE.md', 'LICENSE', 'NOTICE.md', 'README.md', 'RELEASE_BOUNDARY.json', 'STATUS.json', 'TASK_DESIGN.md', 'VERIFICATION.json', 'adversarial_cases.json', 'agent_visible.json', 'analysis_contracts.json', 'asset_binding_plan.json', 'branches.json', 'controls_and_repeats.json', 'coverage_matrix.json', 'dependencies.json', 'design_assumptions.json', 'episode_input_contract.json', 'evaluator_reference.json', 'evidence_map.json', 'lifecycle_contract.json', 'lineage_contract.json', 'material_cards.json', 'mock_contract.json', 'nonmanual_scope.json', 'operations.json', 'preparation_routes.json', 'provenance.json', 'recovery_boundaries.json', 'review/INDEPENDENT_REVIEW.json', 'review/INDEPENDENT_REVIEW.md', 'review/test_independent_contract.py', 'review/test_independent_export.py', 'source_access_audit.json', 'source_conflicts.json', 'source_outcomes.json', 'source_parameters.json', 'station_contracts.json', 'tests/contract.py', 'tests/test_contract.py', 'tests/test_export.py', 'tests/verify_export.py', 'tests/verify_package.py', 'transport_routes.json', 'unknown_parameters.json']
ALLOWED=tuple(sorted(CORE));MANIFEST='EXPORT_ALLOWLIST.json';LIMIT=4*1024*1024
class ExportError(ValueError):pass
def require(ok,msg):
 if not ok:raise ExportError(msg)
def safe_path(path):
 require(type(path) is str and path and '\\' not in path and '\x00' not in path,'invalid path')
 p=PurePosixPath(path);require(not p.is_absolute() and str(p)==path and all(s not in ('','..','.') for s in path.split('/')),'unsafe/noncanonical path')
 require(path in ALLOWED or path==MANIFEST,'path outside exact hard-coded allowlist');return path
def load_bytes(data):
 def pairs(items):
  out={}
  for k,v in items:require(k not in out,'duplicate manifest key');out[k]=v
  return out
 try:return json.loads(data.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ExportError('nonfinite manifest')))
 except (UnicodeDecodeError,json.JSONDecodeError) as e:raise ExportError(str(e))
def manifest_check(m):
 require(type(m) is dict and set(m)=={'schema_version','files','member_count_including_manifest','actor_visible_allowlist','all_other_files_are_evaluator_audit_only'},'manifest fields')
 require(m['schema_version']=='wetting_export.v1','manifest schema');require(type(m['member_count_including_manifest']) is int and m['member_count_including_manifest']==len(ALLOWED)+1,'manifest count');require(m['actor_visible_allowlist']==['agent_visible.json'] and m['all_other_files_are_evaluator_audit_only'] is True,'visibility boundary')
 require(type(m['files']) is list and len(m['files'])==len(ALLOWED),'manifest entries');paths=[]
 for f in m['files']:
  require(type(f) is dict and set(f)=={'path','bytes','sha256'},'file entry fields');safe_path(f['path']);require(f['path']!=MANIFEST,'self listing');paths.append(f['path']);require(type(f['bytes']) is int and 0<f['bytes']<=LIMIT,'bounded positive bytes');require(type(f['sha256']) is str and len(f['sha256'])==64 and all(c in '0123456789abcdef' for c in f['sha256']),'sha256 format')
 require(paths==list(ALLOWED),'exact sorted allowlist');return m
def bytes_check(data,entry):
 require(len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],'file size/hash mismatch: '+entry['path'])
 try:s=data.decode('utf-8')
 except UnicodeDecodeError:raise ExportError('text-only release')
 require('\x00' not in s,'binary content');require(('/'+'workspace/') not in s and ('/'+'root/') not in s and ('sediment'+':/'+'/') not in s,'private path in export')
def root_path(root):
 root=Path(root).absolute()
 require(root.is_dir() and not root.is_symlink(),'regular package root')
 for parent in root.parents:require(not parent.is_symlink(),'symlinked package ancestor')
 return root
def inventory(root):
 root=root_path(root);found=[]
 for p in root.rglob('*'):
  require(not p.is_symlink(),'symlink rejected')
  if p.is_file():found.append(p.relative_to(root).as_posix())
  else:require(p.is_dir() and p.relative_to(root).as_posix() in ('tests','review'),'unknown directory or special file rejected')
 require(sorted(found)==sorted((*ALLOWED,MANIFEST)),'exact directory inventory');return root
def verify_directory(root=ROOT):
 root=inventory(root);m=manifest_check(load_bytes((root/MANIFEST).read_bytes()))
 for f in m['files']:bytes_check((root/f['path']).read_bytes(),f)
 return {'passed':True,'member_count':len(ALLOWED)+1,'text_only':True}
def freeze(root=ROOT):
 root=root_path(root);entries=[]
 destination=root/MANIFEST;require(not destination.is_symlink() and (not destination.exists() or destination.is_file()),'nonregular manifest destination')
 present=[]
 for p in root.rglob('*'):
  require(not p.is_symlink(),'linked package entry before freeze')
  if p.is_file():present.append(p.relative_to(root).as_posix())
  else:require(p.is_dir() and p.relative_to(root).as_posix() in ('tests','review'),'unknown directory or special package entry')
 require(set(present)-{MANIFEST}==set(ALLOWED),'exact prefreeze inventory')
 for name in ALLOWED:
  p=root/name;require(p.is_file() and not p.is_symlink(),'missing/linked export member '+name)
  for parent in p.parents:
   require(not parent.is_symlink(),'linked ancestor')
   if parent==root:break
  data=p.read_bytes();require(0<len(data)<=LIMIT,'bounded export member');entry={'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};bytes_check(data,entry);entries.append(entry)
 m={'schema_version':'wetting_export.v1','files':entries,'member_count_including_manifest':len(entries)+1,'actor_visible_allowlist':['agent_visible.json'],'all_other_files_are_evaluator_audit_only':True}
 with tempfile.NamedTemporaryFile(mode='w',dir=root,prefix='.manifest-',delete=False) as f:
  temp=Path(f.name);f.write(json.dumps(m,indent=2)+'\n')
 try:os.replace(temp,destination)
 finally:
  if temp.exists():temp.unlink()
 verify_directory(root);return m
def verify_zip(path):
 try:
  with zipfile.ZipFile(path) as z:
   infos=z.infolist();names=[i.filename for i in infos];require(len(names)==len(set(names)),'duplicate ZIP member');require(sorted(names)==sorted((*ALLOWED,MANIFEST)),'exact ZIP inventory')
   for i in infos:
    safe_path(i.filename);require(not i.is_dir(),'directory ZIP entry');mode=(i.external_attr>>16)&0o170000;require(mode in (0,stat.S_IFREG),'nonregular ZIP member');require(not i.flag_bits&1,'encrypted ZIP');require(0<i.file_size<=LIMIT,'ZIP member size')
   m=manifest_check(load_bytes(z.read(MANIFEST)))
   for f in m['files']:bytes_check(z.read(f['path']),f)
 except (OSError,zipfile.BadZipFile,RuntimeError) as e:raise ExportError(str(e))
 return {'passed':True,'member_count':len(ALLOWED)+1,'text_only':True}
def build_zip(root,dest):
 root=root_path(root);verify_directory(root);dest=Path(dest).absolute()
 require(not dest.is_symlink() and (not dest.exists() or dest.is_file()),'nonregular archive destination')
 for parent in dest.parents:require(not parent.is_symlink(),'linked archive ancestor')
 require(not dest.resolve().is_relative_to(root.resolve()),'archive destination must be outside package')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in sorted((*ALLOWED,MANIFEST)):
   info=zipfile.ZipInfo(name,date_time=(2026,10,4,0,0,0));info.external_attr=(stat.S_IFREG|0o644)<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,(root/name).read_bytes())
 return verify_zip(dest)
if __name__=='__main__':
 try:print(json.dumps(verify_directory(),indent=2))
 except (ExportError,OSError) as e:print(str(e));sys.exit(1)
