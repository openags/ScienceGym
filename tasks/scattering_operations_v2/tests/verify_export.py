"""Exact bounded text export with canonical ZIP envelope and privacy checks."""
from pathlib import Path, PurePosixPath
import hashlib, json, os, re, stat, struct, sys, tempfile, zipfile
ROOT=Path(__file__).resolve().parents[1]
CORE=['README.md','TASK_DESIGN.md','EXPORT_SCOPE.md','STATUS.json','VERIFICATION.json','agent_visible.json','branches.json','controls_and_repeats.json','coverage_map.json','evaluator_reference.json','failure_contract.json','lineage_contract.json','material_and_sample_dependencies.json','measurement_contract.json','operations.json','paired_asset_reference.json','provenance.json','read_coverage.json','release_boundary.json','safety_boundaries.json','shared_binding_contract.json','source_conflicts.json','source_evidence.json','source_table_inventory.json','source_update_status.json','station_contracts.json','unknowns.json','workflow.json','tests/contract.py','tests/test_contract.py','tests/test_export.py','tests/verify_export.py','tests/verify_package.py','review/test_independent_contract.py','review/test_independent_export.py','review/INDEPENDENT_REVIEW.json','review/INDEPENDENT_REVIEW.md']
ALLOWED=tuple(sorted(CORE));MANIFEST='EXPORT_ALLOWLIST.json';LIMIT=4*1024*1024
class ExportError(ValueError):pass
def require(ok,msg):
 if not ok:raise ExportError(msg)
def safe_path(path):
 require(type(path) is str and path and '\\' not in path and '\x00' not in path,'invalid path')
 p=PurePosixPath(path);require(not p.is_absolute() and str(p)==path and all(x not in ('','..','.') for x in path.split('/')),'unsafe/noncanonical path')
 require(path in ALLOWED or path==MANIFEST,'path outside exact hard-coded allowlist');return path
def load_bytes(data):
 def pairs(items):
  out={}
  for k,v in items:require(k not in out,'duplicate JSON key');out[k]=v
  return out
 try:return json.loads(data.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda x:(_ for _ in ()).throw(ExportError('nonfinite JSON')))
 except (UnicodeDecodeError,json.JSONDecodeError) as e:raise ExportError(str(e))
def root_path(root):
 root=Path(root).absolute()
 for p in (root,*root.parents):require(not p.is_symlink(),'symlink root or ancestor')
 require(root.is_dir(),'regular package directory');return root
def manifest_check(m):
 require(type(m) is dict and set(m)=={'schema_version','files','member_count_including_manifest','actor_visible_allowlist','all_other_files_are_evaluator_audit_only'},'manifest fields')
 require(m['schema_version']=='scattering_export.v1','manifest schema')
 require(type(m['member_count_including_manifest']) is int and m['member_count_including_manifest']==len(ALLOWED)+1,'manifest count')
 require(m['actor_visible_allowlist']==['agent_visible.json'] and m['all_other_files_are_evaluator_audit_only'] is True,'actor visibility boundary')
 require(type(m['files']) is list and len(m['files'])==len(ALLOWED),'manifest entries');paths=[]
 for f in m['files']:
  require(type(f) is dict and set(f)=={'path','bytes','sha256'},'file entry fields');safe_path(f['path']);require(f['path']!=MANIFEST,'manifest cannot list itself');paths.append(f['path'])
  require(type(f['bytes']) is int and 0<f['bytes']<=LIMIT,'bounded positive bytes')
  require(type(f['sha256']) is str and len(f['sha256'])==64 and all(c in '0123456789abcdef' for c in f['sha256']),'SHA-256 format')
 require(paths==list(ALLOWED),'exact sorted allowlist');return m

def privacy_text(s):
 require(not any((ord(c)<32 or 127<=ord(c)<=159) and c not in '\n\r\t' for c in s),'control character in text')
 # Split literals ensure these guard patterns are not themselves private locators.
 roots=('workspace','workspaces','root','home','tmp','Users','Volumes','private')
 require(not any('/'+r.lower()+'/' in s.lower() for r in roots),'private local path')
 require(not re.search(r'[A-Za-z]:'+re.escape(chr(92))+r'(?:Users|Windows|Temp|Documents and Settings)'+re.escape(chr(92)),s,re.IGNORECASE),'private Windows path')
 require(not re.search('(?:'+'file'+'|'+'sediment'+'):'+r'/+',s,re.IGNORECASE),'private file locator')
 require(not re.search(r'(?:sk|ghp|github_pat)[_-][A-Za-z0-9]{20,}',s),'credential-like secret')

def content_check(data,name):
 require(type(data) is bytes and 0<len(data)<=LIMIT,'bounded text bytes')
 try:s=data.decode('utf-8')
 except UnicodeDecodeError:raise ExportError('text-only release')
 privacy_text(s)
 lead=s.lstrip('\ufeff \r\n\t').lower()
 require(not any(lead.startswith(x) for x in ('%pdf','gif87a','gif89a','riff','<svg','<?xml')),'media signature in text export')
 require(data[4:8]!=b'ftyp','movie signature in text export')
 if name.endswith('.json'):
  obj=load_bytes(data)
  def walk(v):
   if isinstance(v,str):privacy_text(v)
   elif isinstance(v,dict):
    for k,x in v.items():privacy_text(k);walk(x)
   elif isinstance(v,list):
    for x in v:walk(x)
  walk(obj)

def bytes_check(data,entry):
 require(len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256'],'file size/hash mismatch: '+entry['path'])
 content_check(data,entry['path'])
def inventory(root,allow_missing_manifest=False):
 root=root_path(root);found=[]
 for p in root.rglob('*'):
  require(not p.is_symlink(),'linked package entry')
  if p.is_file():require(stat.S_ISREG(p.stat().st_mode),'nonregular file');found.append(p.relative_to(root).as_posix())
  else:require(p.is_dir() and p.relative_to(root).as_posix() in ('tests','review'),'unknown directory or special entry')
 expected=set(ALLOWED)|({MANIFEST} if not allow_missing_manifest or MANIFEST in found else set())
 require(set(found)==expected and len(found)==len(expected),'exact directory inventory');return root
def verify_directory(root=ROOT):
 root=inventory(root);m=manifest_check(load_bytes((root/MANIFEST).read_bytes()))
 content_check((root/MANIFEST).read_bytes(),MANIFEST)
 for f in m['files']:bytes_check((root/f['path']).read_bytes(),f)
 return {'passed':True,'member_count':len(ALLOWED)+1,'text_only':True}
def freeze(root=ROOT):
 root=inventory(root,True);entries=[]
 for name in ALLOWED:
  data=(root/name).read_bytes();content_check(data,name);entries.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 m={'schema_version':'scattering_export.v1','files':entries,'member_count_including_manifest':len(entries)+1,'actor_visible_allowlist':['agent_visible.json'],'all_other_files_are_evaluator_audit_only':True}
 manifest_check(m)
 with tempfile.NamedTemporaryFile(mode='w',dir=root,prefix='.manifest-',delete=False) as f:
  temp=Path(f.name);f.write(json.dumps(m,indent=2)+'\n')
 try:os.replace(temp,root/MANIFEST)
 finally:
  if temp.exists():temp.unlink()
 verify_directory(root);return m

def zip_envelope(raw,infos):
 require(len(raw)>=22 and raw[-22:-18]==b'PK\x05\x06','canonical final EOCD; no trailing data or comments')
 eocd=struct.unpack_from('<4s4H2LH',raw,len(raw)-22)
 _,disk,startdisk,on_disk,total,cd_size,cd_offset,comment=eocd
 require(disk==startdisk==comment==0 and on_disk==total==len(infos),'single-disk standard ZIP only')
 require(cd_offset+cd_size==len(raw)-22,'no hidden central-directory gap')
 offset=0
 for info in infos:
  require(info.header_offset==offset and raw[offset:offset+4]==b'PK\x03\x04','no prepended/intermember payload')
  require(len(raw)>=offset+30,'local header length')
  fields=struct.unpack_from('<4s5H3L2H',raw,offset)
  _,version,flags,method,tm,dt,crc,compressed,uncompressed,nlen,xlen=fields
  require(xlen==0 and flags==info.flag_bits and method==info.compress_type and crc==info.CRC and compressed==info.compress_size and uncompressed==info.file_size,'local/central metadata mismatch')
  require(not flags&9 and version<=20,'encryption/data descriptors/advanced ZIP unsupported')
  name=raw[offset+30:offset+30+nlen]
  require(name.decode('utf-8' if flags&0x800 else 'cp437')==info.filename,'local/central filename mismatch')
  offset+=30+nlen+compressed
 require(offset==cd_offset,'no local payload gap')
 pos=cd_offset
 for info in infos:
  require(raw[pos:pos+4]==b'PK\x01\x02','central header sequence')
  vals=struct.unpack_from('<4s6H3L5H2L',raw,pos)
  nlen,xlen,clen=vals[10:13]
  require(xlen==clen==0,'central hidden extra/comment')
  pos+=46+nlen+xlen+clen
 require(pos==cd_offset+cd_size,'exact central-directory size')

def verify_zip(path):
 try:
  path=Path(path);require(path.is_file() and not path.is_symlink(),'regular archive required')
  for parent in path.absolute().parents:require(not parent.is_symlink(),'linked archive ancestor')
  require(path.stat().st_size<=(len(ALLOWED)+1)*(LIMIT+1024),'bounded archive')
  raw=path.read_bytes()
  with zipfile.ZipFile(path) as z:
   infos=z.infolist();names=[i.filename for i in infos]
   require(len(names)==len(set(names)) and sorted(names)==sorted((*ALLOWED,MANIFEST)),'exact unique ZIP inventory')
   require(z.comment==b'','ZIP comment prohibited')
   for i in infos:
    safe_path(i.filename);require(not i.is_dir(),'directory ZIP entry');require(((i.external_attr>>16)&0o170000) in (0,stat.S_IFREG),'nonregular ZIP member')
    require(i.extra==i.comment==b'','ZIP metadata payload prohibited')
    require(not i.flag_bits&9 and i.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'unsupported ZIP format')
    require(0<i.file_size<=LIMIT,'bounded ZIP member size')
   zip_envelope(raw,infos)
   manifest_data=z.read(MANIFEST);content_check(manifest_data,MANIFEST);m=manifest_check(load_bytes(manifest_data))
   for f in m['files']:bytes_check(z.read(f['path']),f)
 except ExportError:raise
 except (OSError,zipfile.BadZipFile,RuntimeError,ValueError,UnicodeError,struct.error,NotImplementedError) as e:raise ExportError(str(e))
 return {'passed':True,'member_count':len(ALLOWED)+1,'text_only':True,'canonical_envelope':True}
def build_zip(root,dest):
 root=root_path(root);verify_directory(root);dest=Path(dest).absolute()
 require(not dest.is_symlink() and (not dest.exists() or dest.is_file()),'regular archive destination')
 for p in dest.parents:require(not p.is_symlink(),'linked archive ancestor')
 require(not dest.is_relative_to(root),'archive outside package required')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name in sorted((*ALLOWED,MANIFEST)):
   i=zipfile.ZipInfo(name,date_time=(2026,10,4,0,0,0));i.create_system=3;i.external_attr=(stat.S_IFREG|0o644)<<16;i.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(i,(root/name).read_bytes())
 return verify_zip(dest)
if __name__=='__main__':
 try:print(json.dumps(verify_directory(),indent=2))
 except (ExportError,OSError) as e:print(str(e));sys.exit(1)
