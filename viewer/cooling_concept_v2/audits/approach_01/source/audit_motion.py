"""Independently inspect joint limits, phase continuity and sole penetration.

Sampled geometry and finite differences only; neither contact dynamics nor a
continuous-time proof. Export samples must include both sides of phase changes.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
from source_geometry import KIN,robot_meshes

def audit(folder):
    folder=Path(folder);joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'}
    feet={n:m.vertices for n,m in robot_meshes().items() if n.endswith('ankle_roll_link')}
    limits=[];velocities=[];sole_errors=[];max_speeds={};minimum_sole=1;previous=None;count=0
    with gzip.open(folder/'frames.jsonl.gz','rt') as stream:
        for line in stream:
            frame=json.loads(line);count+=1;q=frame['joints'].copy()
            for j in KIN['joints']:
                if j['mimic']:
                    m=j['mimic'];q[j['name']]=float(m.get('offset',0))+float(m.get('multiplier',1))*q.get(m['joint'],0)
            for name,j in joints.items():
                value=q.get(name,0);lo,hi=j['limits']['lower'],j['limits']['upper']
                if not lo-1e-6<=value<=hi+1e-6:limits.append(dict(time_s=frame['time_s'],phase=frame['phase'],joint=name,value=value,lower=lo,upper=hi))
                if previous:
                    dt=frame['time_s']-previous[0]['time_s']
                    if 0<dt<.51:
                        speed=abs(value-previous[1].get(name,0))/dt;max_speeds[name]=max(max_speeds.get(name,0),speed)
                        if speed>j['limits']['velocity']+1e-3:velocities.append(dict(time_s=frame['time_s'],phase=frame['phase'],previous_phase=previous[0]['phase'],joint=name,speed_rad_s=speed,limit_rad_s=j['limits']['velocity'],dt_s=dt))
            for name,vertices in feet.items():
                matrix=np.asarray(frame['links'][name]).reshape(4,4).T
                minimum=float(np.min(vertices@matrix[2,:3]+matrix[2,3]));minimum_sole=min(minimum_sole,minimum)
                if minimum<-.002:sole_errors.append(dict(time_s=frame['time_s'],phase=frame['phase'],foot=name,minimum_z_m=minimum))
            previous=(frame,q)
    report=dict(passed=not(limits or velocities or sole_errors),scope=__doc__,frames=count,joint_limit_failures=limits,joint_velocity_failures=velocities,sole_penetration_failures=sole_errors,minimum_sole_z_m=minimum_sole,maximum_joint_speeds_rad_s=max_speeds,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (folder/'motion_review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=report['passed'],frames=count,limits=len(limits),speeds=len(velocities),soles=len(sole_errors),minimum_sole_z_m=minimum_sole)),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('folder');args=parser.parse_args();audit(args.folder)
