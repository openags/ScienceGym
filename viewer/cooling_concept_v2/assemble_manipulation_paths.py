"""Package planned paths with speed-bounded smooth interpolation timings."""
import hashlib
import json
from pathlib import Path
import numpy as np
from source_geometry import KIN
from manipulation_inputs import load_inputs

HERE=Path(__file__).resolve().parent


def main():
    packet=load_inputs()
    joints={j['name']:j for j in KIN['joints'] if j['type']=='revolute'}
    effective={n:j['limits']['velocity'] for n,j in joints.items()}
    for name,joint in joints.items():
        root=name;multiplier=1.
        while joints[root].get('mimic'):
            m=joints[root]['mimic'];multiplier*=float(m.get('multiplier',1));root=m['joint']
        if multiplier:effective[root]=min(effective[root],joint['limits']['velocity']/abs(multiplier))
    paths={};pending=[]
    for name,source in packet['frames'].items():
        candidates=[HERE/'previews/verified_manipulation_paths'/(name+'.json')]
        accepted=[(f,json.loads(f.read_text())) for f in candidates if f.exists()]
        current_input=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
        accepted=[(f,r) for f,r in accepted if r.get('passed') and r.get('input_sha256')==current_input]
        if not accepted:pending.append(name);continue
        file,result=accepted[0]
        assert result['source_sha256']==packet['source_sha256'],name+' stale source pins'
        assert result['input_sha256']==hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),name+' stale endpoints'
        limits=[]
        for joint in result['joints']:
            aliases=result['generalized_finger_joint'].get(joint,[joint])
            selected=.65 if any(f in joint for f in ['fold','index','middle','ring','little']) else .9 if 'thumb' in joint else .8 if joint=='waist_pitch_joint' else 2.
            limits.append(min(selected,*(effective[n] for n in aliases)))
        knots=np.array(result['knots']);assert len(knots)>=2
        # Smoothstep has maximum derivative 1.5. The factor 1.6 leaves margin.
        segments=np.maximum(.20,1.6*np.max(np.abs(np.diff(knots,axis=0))/limits,axis=1))
        times=np.r_[0,np.cumsum(segments)]
        paths[name]=dict(joints=result['joints'],knots=result['knots'],
                         generalized_finger_joint=result['generalized_finger_joint'],base_q=source['start']['joints'],
                         knot_times_s=times.tolist(),duration_s=float(times[-1]),selected_speed_caps_rad_s=limits,
                         source_plan_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                         independently_reviewed=False)
    out=dict(scope='Development choreography paths; whole-scene and phase-transition validation remain required',
             complete=not pending,pending_paths=pending,source_sha256=packet['source_sha256'],
             generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),paths=paths)
    (HERE/'manipulation_approach_paths.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(paths=len(paths),pending=pending,durations={n:round(p['duration_s'],3) for n,p in paths.items()})),flush=True)


if __name__=='__main__':main()
