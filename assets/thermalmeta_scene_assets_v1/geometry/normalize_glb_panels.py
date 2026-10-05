"""Use portable glTF alpha for original illustrative transparent safety panels."""
import pathlib,json,struct
p=pathlib.Path(__file__).resolve().parent/'thermalmeta_lab.glb';b=p.read_bytes();magic,version,total=struct.unpack_from('<III',b,0);assert magic==0x46546C67 and version==2 and total==len(b)
chunks=[];i=12
while i<len(b):
 n,t=struct.unpack_from('<II',b,i);i+=8;v=b[i:i+n];i+=n
 if t==0x4E4F534A:
  j=json.loads(v)
  for m in j['materials']:
   if m.get('name')=='glass':m['pbrMetallicRoughness']['baseColorFactor'][3]=.07;m['alphaMode']='BLEND';m.setdefault('extras',{})['rendering_boundary']='illustrative_alpha_approximation_not_optical_physics'
  v=json.dumps(j,separators=(',',':'),ensure_ascii=True).encode();v+=b' '*((-len(v))%4)
 chunks.append(struct.pack('<II',len(v),t)+v)
data=b''.join(chunks);p.write_bytes(struct.pack('<III',magic,version,12+len(data))+data);print('PORTABLE_ALPHA_NORMALIZED')
