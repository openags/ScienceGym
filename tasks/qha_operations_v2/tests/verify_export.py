"""Exact allowlist export checker; does not mutate, extract or execute an archive."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile,stat,re,sys
ALLOWED_SUFFIXES={'.json','.md','.py'}
ROOT='qha_operations_v2'
SECRET_PATTERNS=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{20,}'),re.compile(rb'sk-[A-Za-z0-9_-]{24,}'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'https?://[^\s\"<>]+[?&](?:sig|token|X-Amz-Signature)=',re.I)]
def require(ok,m):
 if not ok:raise ValueError(m)
def safe_path(p):
 require(isinstance(p,str) and p and '\\' not in p and '\x00' not in p,'unsafe path')
 pp=PurePosixPath(p);require(not pp.is_absolute() and '..' not in pp.parts and '.' not in pp.parts and str(pp)==p,'unsafe path')
 require(pp.suffix in ALLOWED_SUFFIXES and '__pycache__' not in pp.parts,'forbidden export type')
 return pp

def inspect_bytes(p,b):
 require(not b.startswith((b'%PDF',b'PK\x03\x04',b'\x89PNG',b'\xff\xd8\xff',b'glTF',b'BLENDER')),'source/binary/nested artifact prohibited')
 require(len(b)<2_000_000,'oversize member')
 require(not any(rx.search(b) for rx in SECRET_PATTERNS),'secret or signed URL')
 try:b.decode('utf-8')
 except UnicodeDecodeError:raise ValueError('nontext bytes prohibited')

def manifest_data(m):
 require(set(m)=={'schema_version','files','member_count_including_manifest','actor_visible_allowlist','all_other_files_are_evaluator_audit_only'},'manifest schema')
 require(m['schema_version']=='sciencegym.qha.export.v1','unsupported manifest schema')
 files=m['files'];require(isinstance(files,list) and files,'empty manifest')
 names=[f['path']for f in files];require(len(names)==len(set(names)),'duplicate allowlist')
 require('EXPORT_ALLOWLIST.json' not in names,'self hash not permitted')
 for f in files:
  safe_path(f['path']);require(set(f)=={'path','bytes','sha256'},'manifest entry schema')
  require(isinstance(f['bytes'],int) and 0<=f['bytes']<2_000_000,'invalid length')
  require(re.fullmatch('[0-9a-f]{64}',f['sha256']) is not None,'invalid hash')
 require(m['member_count_including_manifest']==len(files)+1,'count mismatch')
 require(m['actor_visible_allowlist']==['agent_visible.json'] and m['all_other_files_are_evaluator_audit_only'] is True,'actor scope widened')
 return {f['path']:f for f in files}

def validate_directory(root):
 root=Path(root);require(not (root/'EXPORT_ALLOWLIST.json').is_symlink(),'manifest symlink prohibited');raw=(root/'EXPORT_ALLOWLIST.json').read_bytes();inspect_bytes('EXPORT_ALLOWLIST.json',raw);m=json.loads(raw);entries=manifest_data(m)
 actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 require(actual==set(entries)|{'EXPORT_ALLOWLIST.json'},'unallowlisted/missing file')
 for p in root.rglob('*'):require(not p.is_symlink(),'symlink prohibited')
 for name,f in entries.items():
  b=(root/name).read_bytes();inspect_bytes(name,b);require(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'hash mismatch '+name)
 return {'status':'PASS','members':len(entries)+1,'scope':'exact authored export only'}

def validate_archive(path):
 with zipfile.ZipFile(path) as z:
  infos=z.infolist();require(len(infos)<=100,'archive member limit');names=[i.filename for i in infos];require(len(names)==len(set(names)),'duplicate zip member')
  require(sum(i.file_size for i in infos)<20_000_000,'archive size limit')
  for i in infos:
   require(i.filename.startswith(ROOT+'/'),'wrong archive root');safe_path(i.filename[len(ROOT)+1:]);require(not i.is_dir(),'directory entries not needed')
   mode=(i.external_attr>>16)&0o170000;require(mode in {0,stat.S_IFREG},'nonregular zip member')
   require(not (i.flag_bits&1),'encrypted archive');require(i.file_size<2_000_000,'member size limit')
  require(ROOT+'/EXPORT_ALLOWLIST.json' in names,'manifest absent')
  raw=z.read(ROOT+'/EXPORT_ALLOWLIST.json');inspect_bytes('EXPORT_ALLOWLIST.json',raw);m=json.loads(raw);entries=manifest_data(m)
  require(set(names)=={ROOT+'/'+n for n in entries}|{ROOT+'/EXPORT_ALLOWLIST.json'},'archive allowlist mismatch')
  for name,f in entries.items():
   b=z.read(ROOT+'/'+name);inspect_bytes(name,b);require(len(b)==f['bytes'] and hashlib.sha256(b).hexdigest()==f['sha256'],'archive hash mismatch '+name)
 return {'status':'PASS','members':len(entries)+1,'archive_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
if __name__=='__main__':
 p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
 print(json.dumps(validate_directory(p) if p.is_dir() else validate_archive(p),indent=2))
