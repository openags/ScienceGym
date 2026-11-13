"""Check the spatula's containment at every recorded physics state."""
import argparse,hashlib,json
from pathlib import Path
import mujoco,numpy as np,trimesh

def verify(folder):
 p=Path(folder);m=mujoco.MjModel.from_xml_path(str(p/'world.xml'));d=mujoco.MjData(m);t=dict(np.load(p/'trace.npz'));v=trimesh.load(p/'buerkle_spatula.stl').vertices;bad=[];worst=np.zeros(2)
 for i,q in enumerate(t['qpos']):
  d.qpos[:]=q;mujoco.mj_kinematics(m,d);s=d.body('buerkle_spatula');b=d.body('carrier_tray');local=(v@s.xmat.reshape(3,3).T+s.xpos-b.xpos)@b.xmat.reshape(3,3);extent=abs(local[:,:2]).max(axis=0);worst=np.maximum(worst,extent)
  if not (extent[0]<.151 and extent[1]<.101 and -.005<local[:,2].min()<.06):bad.append(float(t['time'][i]))
 dt=np.diff(t['time']);frequency=int(round(1/np.median(dt[dt>0])))
 r=dict(passed=not bad,samples=len(t['time']),sample_frequency_hz=frequency,failed_times_s=bad,maximum_local_xy_extent_m=worst.tolist(),trace_sha256=hashlib.sha256((p/'trace.npz').read_bytes()).hexdigest(),verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Geometric containment at every recorded state; not a substitute for dynamics replay.')
 (p/f'payload_containment_{frequency}hz.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('folder');a=p.parse_args()
 if not verify(a.folder)['passed']:raise SystemExit(1)
