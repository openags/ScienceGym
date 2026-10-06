"""Schema-aware native Blender fixed-buffer scanner and canonical privacy cleanup.

Only recognized C-string tails and inactive file-browser/sequencer directories are
rewritten. Opaque arrays are never guessed to be strings. Public reports contain
hashes and offsets, never recovered buffer contents. Supports little-endian 64-bit
BLEND with self-consistent SDNA layouts; unsupported layouts fail closed.
"""
from pathlib import Path
import argparse,gzip,hashlib,io,json,os,re,struct,tempfile,zstandard

STRING_FIELDS={
 'ID':{'name'},
 'FileGlobal':{'filename'},
 'FileSelectParams':{'title','dir','file','renamefile','filter_glob','filter_search'},
 'Editing':{'act_imagedir','act_sounddir','proxy_dir'},
 'View3DShading':{'studio_light','lookdev_light','matcap','aov_name'},
 'ColorManagedViewSettings':{'look','view_transform'},
 'RenderData':{'pic','stamp_udata','engine'},
 'SpaceOops':{'search_string'},'SpaceNode':{'tree_idname'},
}
UI_RESET={('FileSelectParams','dir'):b'//',('FileSelectParams','file'):b'',
 ('FileSelectParams','renamefile'):b'',('Editing','act_imagedir'):b'//',
 ('Editing','act_sounddir'):b'',('Editing','proxy_dir'):b''}
PATH_FIELDS={'filename','filepath','dir','file','renamefile','pic','act_imagedir','act_sounddir','proxy_dir'}
def sha(b):return hashlib.sha256(b).hexdigest()
def decoded(path):
 raw=Path(path).read_bytes()
 if raw.startswith(bytes.fromhex('28b52ffd')):data=zstandard.ZstdDecompressor().stream_reader(io.BytesIO(raw)).read()
 elif raw.startswith(b'\x1f\x8b'):data=gzip.decompress(raw)
 else:data=raw
 if not data.startswith(b'BLENDER-v'):raise ValueError('Only little-endian 64-bit BLEND is supported')
 return raw,data

def parse(data):
 pos=12;blocks=[]
 while pos+24<=len(data):
  code,n,old,sdna,count=struct.unpack_from('<4sIQII',data,pos)
  if pos+24+n>len(data):raise ValueError('Truncated Blender block')
  blocks.append({'start':pos,'data_start':pos+24,'code':code,'size':n,'sdna':sdna,'count':count});pos+=24+n
  if code==b'ENDB':break
 if pos!=len(data):raise ValueError('Unexpected bytes after final Blender block')
 dna=next(x for x in blocks if x['code']==b'DNA1');d=data[dna['data_start']:dna['data_start']+dna['size']]
 if d[:8]!=b'SDNANAME':raise ValueError('Missing SDNA schema')
 pos=8;n=struct.unpack_from('<I',d,pos)[0];pos+=4;names=[]
 for _ in range(n):j=d.index(0,pos);names.append(d[pos:j].decode());pos=j+1
 pos=(pos+3)&~3
 if d[pos:pos+4]!=b'TYPE':raise ValueError('Missing SDNA types')
 pos+=4;n=struct.unpack_from('<I',d,pos)[0];pos+=4;types=[]
 for _ in range(n):j=d.index(0,pos);types.append(d[pos:j].decode());pos=j+1
 pos=(pos+3)&~3
 if d[pos:pos+4]!=b'TLEN':raise ValueError('Missing SDNA sizes')
 pos+=4;sizes=list(struct.unpack_from('<'+'H'*len(types),d,pos));pos+=2*len(types);pos=(pos+3)&~3
 if d[pos:pos+4]!=b'STRC':raise ValueError('Missing SDNA structures')
 pos+=4;n=struct.unpack_from('<I',d,pos)[0];pos+=4;structs=[]
 for _ in range(n):
  typ,num=struct.unpack_from('<HH',d,pos);pos+=4;fields=[];off=0
  for _ in range(num):
   t,f=struct.unpack_from('<HH',d,pos);pos+=4;name=names[f];count=1
   for dim in re.findall(r'\[(\d+)\]',name):count*=int(dim)
   size=(8 if '*' in name else sizes[t])*count
   fields.append({'type':types[t],'name':name,'base_name':name.split('[')[0],'offset':off,'size':size});off+=size
  structs.append({'name':types[typ],'size':sizes[typ],'fields':fields,'computed_size':off})
 return blocks,structs,sha(d)

def arrays(data):
 blocks,structs,dna_sha=parse(data);by_name={x['name']:x for x in structs};out=[];bad=set()
 def walk(s,start,prefix,depth=0):
  if depth>16:raise ValueError('Unexpected embedded struct recursion')
  if s['computed_size']!=s['size']:bad.add(s['name']);return
  for f in s['fields']:
   if '*' in f['name']:continue
   loc=start+f['offset'];label=prefix+'.'+f['name']
   if f['type']=='char' and '[' in f['name'] and f['size']>=32:
    if loc+f['size']>len(data):raise ValueError('Field outside file')
    out.append(dict(f,declaring_struct=s['name'],field=label,start=loc,end=loc+f['size']))
   elif f['type'] in by_name:
    sub=by_name[f['type']]
    if not sub['size']:continue
    for k in range(f['size']//sub['size']):walk(sub,loc+k*sub['size'],label+'['+str(k)+']',depth+1)
 for block in blocks:
  if block['code'] in {b'DNA1',b'ENDB',b'REND',b'TEST'}:continue
  if block['sdna']>=len(structs):raise ValueError('Unknown block schema')
  s=structs[block['sdna']]
  if not s['size'] or s['size']*block['count']>block['size']:continue
  for k in range(block['count']):walk(s,block['data_start']+k*s['size'],s['name']+'@'+str(block['start'])+'['+str(k)+']')
 if bad:raise ValueError('Unsupported SDNA layouts: '+','.join(sorted(bad)))
 return out,dna_sha

def path_state(active,path,root):
 if not active:return 'empty'
 if b'\x00' in active:return 'invalid'
 try:s=active.decode('utf-8')
 except UnicodeDecodeError:return 'undecodable'
 if s.startswith('//'):
  candidate=(Path(path).parent/s[2:]).resolve()
  return 'package_relative' if candidate.is_relative_to(root.resolve()) else 'outside_package'
 if s.startswith('/') or re.match(r'^[A-Za-z]:[\\/]',s):return 'absolute'
 if '/' in s or '\\' in s:return 'unqualified_relative'
 return 'basename'

def inspect(path,package_root=None):
 path=Path(path);root=Path(package_root) if package_root else path.parent.parent;raw,data=decoded(path);fields,dna_sha=arrays(data);results=[]
 for f in fields:
  v=data[f['start']:f['end']];nul=v.find(b'\x00');active=v if nul<0 else v[:nul];tail=v[nul+1:] if nul>=0 else b''
  known=f['base_name'] in STRING_FIELDS.get(f['declaring_struct'],set());is_path=f['base_name'] in PATH_FIELDS
  results.append({'field':f['field'],'declaring_struct':f['declaring_struct'],'base_name':f['base_name'],'start':f['start'],'end':f['end'],'size':f['size'],'first_nul':nul,'nonzero_tail_count':sum(x!=0 for x in tail),'known_c_string':known,'path_field':is_path,'path_classification':path_state(active,path,root) if is_path else 'not_path','active_sha256':sha(active),'buffer_sha256':sha(v)})
 path_issues=[x['field'] for x in results if x['path_field'] and (x['nonzero_tail_count'] or x['path_classification'] not in {'empty','package_relative','basename'})]
 unknown_tails=[x['field'] for x in results if x['nonzero_tail_count'] and not x['known_c_string']]
 return {'schema':'sciencegym3d.deep_native_buffers.v1','file':path.name,'compressed_sha256':sha(raw),'decompressed_sha256':sha(data),'decompressed_bytes':len(data),'sdna_sha256':dna_sha,'fixed_char_arrays_checked':len(results),'fields_with_nonzero_tail':sum(bool(x['nonzero_tail_count']) for x in results),'unsupported_layouts':[],'path_issues':path_issues,'unclassified_nonzero_tails':unknown_tails,'strict_path_privacy_pass':not path_issues and not unknown_tails,'fields':results,'contents_redacted':True}

def clean(source,destination,package_root=None):
 source=Path(source);destination=Path(destination)
 if source.resolve()==destination.resolve():raise ValueError('Source and output must be separate; retain input for audit')
 raw,data=decoded(source);fields,dna_sha=arrays(data);mutable=bytearray(data);changes=[]
 for f in fields:
  v=data[f['start']:f['end']];nul=v.find(b'\x00');active=v if nul<0 else v[:nul];tail=v[nul+1:] if nul>=0 else b''
  known=f['base_name'] in STRING_FIELDS.get(f['declaring_struct'],set());key=(f['declaring_struct'],f['base_name'])
  if any(tail) and not known:raise ValueError('Unclassified fixed-buffer tail requires review: '+f['field'])
  if not known:continue
  if nul<0:raise ValueError('Recognized C string has no terminator: '+f['field'])
  replacement=UI_RESET.get(key,active)
  if len(replacement)>=f['size']:raise ValueError('Replacement exceeds field')
  canonical=replacement+bytes(f['size']-len(replacement))
  if canonical!=v:
   mutable[f['start']:f['end']]=canonical
   changes.append({'field':f['field'],'declaring_struct':f['declaring_struct'],'base_name':f['base_name'],'start':f['start'],'end':f['end'],'size':f['size'],'mode':'reset_inactive_ui_directory' if replacement!=active else 'canonicalize_post_nul_tail','active_value_unchanged':replacement==active,'before_buffer_sha256':sha(v),'after_buffer_sha256':sha(canonical),'complete_fixed_width_buffer_written':True})
 output=bytes(mutable);masked_before=bytearray(data);masked_after=bytearray(output)
 for f in changes:masked_before[f['start']:f['end']]=bytes(f['size']);masked_after[f['start']:f['end']]=bytes(f['size'])
 if masked_before!=masked_after:raise AssertionError('Unexpected byte modification')
 encoded=zstandard.ZstdCompressor(level=19,write_checksum=True).compress(output)
 destination.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.NamedTemporaryFile(dir=destination.parent,prefix='.native-buffer-',suffix='.blend',delete=False) as stream:
  temporary=Path(stream.name);stream.write(encoded)
 try:
  post=inspect(temporary,package_root)
  if not post['strict_path_privacy_pass'] or post['fields_with_nonzero_tail']:raise ValueError('Post-clean fixed buffer scan failed')
  os.replace(temporary,destination);post['file']=destination.name
 finally:
  if temporary.exists():temporary.unlink()
 return {'schema':'sciencegym3d.native_buffer_cleanup.v1','source_file':source.name,'destination_file':destination.name,'source_sha256':sha(raw),'destination_sha256':sha(encoded),'source_decompressed_sha256':sha(data),'destination_decompressed_sha256':sha(output),'decompressed_bytes_preserved':len(data)==len(output),'sdna_sha256_unchanged':parse(output)[2]==dna_sha,'bytes_outside_declared_buffers_identical':True,'masked_bytes_sha256':sha(masked_after),'changed_fixed_buffers':changes,'changed_buffer_count':len(changes),'all_active_values_preserved_except_inactive_ui_directories':all(x['active_value_unchanged'] or x['declaring_struct'] in {'FileSelectParams','Editing'} for x in changes),'post_scan_summary':{k:v for k,v in post.items() if k!='fields'},'raw_buffer_contents_disclosed':False}

def main():
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['scan','clean']);p.add_argument('source');p.add_argument('destination',nargs='?');p.add_argument('--package-root');p.add_argument('--report',required=True);a=p.parse_args()
 r=inspect(a.source,a.package_root) if a.mode=='scan' else clean(a.source,a.destination,a.package_root)
 Path(a.report).write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps({k:v for k,v in r.items() if k not in {'fields','changed_fixed_buffers'}},indent=2))
if __name__=='__main__':main()
