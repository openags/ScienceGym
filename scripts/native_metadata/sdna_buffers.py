"""Read-only SDNA decoder and fixed-array traversal from the accepted QHA parser.

This library has no writer or command-line interface. Only maintain_native_paths
owns the narrower, explicitly allowlisted metadata cleanup policy.
"""
from pathlib import Path
import gzip,hashlib,io,re,struct,zstandard

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

