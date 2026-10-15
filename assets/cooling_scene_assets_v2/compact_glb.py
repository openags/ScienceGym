"""Lossless glTF buffer/accessor/mesh deduplication; no geometry quantization."""
import hashlib
import json
import struct
from pathlib import Path

def compact(path):
    path=Path(path);raw=path.read_bytes()
    magic,version,length=struct.unpack('<4sII',raw[:12])
    if (magic,version,length)!=(b'glTF',2,len(raw)):raise ValueError('Invalid GLB')
    jlen,jtype=struct.unpack('<II',raw[12:20]);doc=json.loads(raw[20:20+jlen])
    offset=20+jlen;blen,btype=struct.unpack('<II',raw[offset:offset+8]);binary=raw[offset+8:offset+8+blen]
    if len(doc['buffers'])!=1:raise ValueError('Only single-buffer self-contained GLB supported')
    newbin=bytearray();views=[];viewmap={};seen={}
    for i,view in enumerate(doc['bufferViews']):
        start=view.get('byteOffset',0);payload=binary[start:start+view['byteLength']]
        metadata={k:v for k,v in view.items() if k not in ('buffer','byteOffset','byteLength','name')}
        key=(hashlib.sha256(payload).digest(),json.dumps(metadata,sort_keys=True))
        if key not in seen:
            newbin.extend(b'\0'*((-len(newbin))%4))
            newview={**metadata,'buffer':0,'byteOffset':len(newbin),'byteLength':len(payload)}
            seen[key]=len(views);views.append(newview);newbin.extend(payload)
        viewmap[i]=seen[key]
    accessors=[];amap={};seen={}
    for i,a in enumerate(doc['accessors']):
        a=dict(a)
        if 'sparse' in a:raise ValueError('Sparse accessors need explicit handling')
        if 'bufferView' in a:a['bufferView']=viewmap[a['bufferView']]
        a.pop('name',None);key=json.dumps(a,sort_keys=True)
        if key not in seen:seen[key]=len(accessors);accessors.append(a)
        amap[i]=seen[key]
    meshes=[];mmap={};seen={}
    for i,m in enumerate(doc['meshes']):
        m=dict(m);m.pop('name',None)
        for p in m['primitives']:
            p['attributes']={k:amap[v] for k,v in p['attributes'].items()}
            if 'indices' in p:p['indices']=amap[p['indices']]
            for target in p.get('targets',[]):
                for k in list(target):target[k]=amap[target[k]]
        key=json.dumps(m,sort_keys=True)
        if key not in seen:seen[key]=len(meshes);meshes.append(m)
        mmap[i]=seen[key]
    for n in doc['nodes']:
        if 'mesh' in n:n['mesh']=mmap[n['mesh']]
    for image in doc.get('images',[]):
        if 'bufferView' in image:image['bufferView']=viewmap[image['bufferView']]
    for skin in doc.get('skins',[]):
        if 'inverseBindMatrices' in skin:skin['inverseBindMatrices']=amap[skin['inverseBindMatrices']]
    for animation in doc.get('animations',[]):
        for sampler in animation['samplers']:
            for k in ('input','output'):sampler[k]=amap[sampler[k]]
    doc.update(bufferViews=views,accessors=accessors,meshes=meshes,buffers=[{'byteLength':len(newbin)}])
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    newbin.extend(b'\0'*((-len(newbin))%4))
    result=struct.pack('<4sII',b'glTF',2,28+len(js)+len(newbin))+struct.pack('<II',len(js),jtype)+js+struct.pack('<II',len(newbin),btype)+newbin
    path.write_bytes(result)
    return {'bytes_before':len(raw),'bytes_after':len(result),'meshes':len(meshes),'nodes':len(doc['nodes']),'method':'lossless_buffer_accessor_mesh_deduplication'}

if __name__=='__main__':print(json.dumps(compact(Path(__file__).resolve().parent/'geometry/cooling_pilot.glb')))
