"""Lossless, byte-shuffled depth chunks with bit-for-bit round-trip checks."""
from pathlib import Path
import json,hashlib
import numpy as np

def save(folder,frames,chunk_frames=100):
 folder=Path(folder);out=folder/'head_depth_chunks';out.mkdir(exist_ok=False);parts=[]
 for start in range(0,len(frames),chunk_frames):
  chunk=frames[start:start+chunk_frames];time=np.array([x[0] for x in chunk]);depth=np.stack([x[1] for x in chunk]).astype('<f4',copy=False)
  shuffled=depth.view('u1').reshape(depth.shape+(4,)).transpose(3,0,1,2).copy();path=out/f'{start:06d}.npz'
  np.savez_compressed(path,time=time,bytes=shuffled)
  loaded=np.load(path);restored=loaded['bytes'].transpose(1,2,3,0).copy().view('<f4').reshape(depth.shape)
  if not np.array_equal(restored.view('u4'),depth.view('u4')):raise AssertionError('Depth bits changed during packing')
  parts.append(dict(path=str(path.relative_to(folder)),frames=len(chunk),first_time_s=float(time[0]),last_time_s=float(time[-1]),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 (folder/'head_depth_index.json').write_text(json.dumps(dict(format='lossless_float32_byteplanes_v1',frames=len(frames),parts=parts),indent=2)+'\n')

def load(folder):
 folder=Path(folder)
 if (folder/'head_depth_index.json').exists():
  index=json.loads((folder/'head_depth_index.json').read_text())
  for row in index['parts']:
   data=np.load(folder/row['path']);shuffled=data['bytes'];depth=shuffled.transpose(1,2,3,0).copy().view('<f4').reshape(shuffled.shape[1:]);yield from zip(data['time'],depth)
 else:
  data=np.load(folder/'head_depth.npz');yield from zip(data['time'],data['depth'])
