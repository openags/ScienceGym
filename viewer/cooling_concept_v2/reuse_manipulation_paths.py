"""Adapt successful approach routes and recheck every candidate mesh edge.

Endpoint correction is a planning proposal only. It is accepted here only when
the receiving workstation's complete planning-region checks pass at the same
joint-space resolution as the original search. Independent film review remains
mandatory. Inputs are the explicitly frozen pre-integration endpoint capture.
"""
import hashlib
import json
import time
from pathlib import Path
import numpy as np
from plan_manipulation_approaches import HERE,Geometry,Space
from manipulation_inputs import load_inputs


def main():
    packet=load_inputs()
    geometry=Geometry();folder=HERE/'previews/reused_manipulation_paths';folder.mkdir(exist_ok=True)
    for name,source in packet['frames'].items():
        existing=HERE/'previews/manipulation_paths'/(name+'.json')
        current_input=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
        if existing.exists():
            saved=json.loads(existing.read_text())
            if saved['passed'] and saved.get('input_sha256')==current_input:continue
        previous=folder/(name+'.json')
        if previous.exists():
            saved=json.loads(previous.read_text())
            if saved.get('passed') and saved.get('source_sha256')==packet['source_sha256'] and saved.get('input_sha256')==current_input:continue
        candidates=[]
        for directory in ['manipulation_paths','reused_manipulation_paths']:
            for file in (HERE/'previews'/directory).glob('*.json'):
                data=json.loads(file.read_text())
                if data.get('passed') and data.get('source_sha256')==packet['source_sha256']:candidates.append((file,data))
        # Prefer same-dimension routes before trying projected arm trajectories.
        space=Space(source,packet['extraGeometry'],geometry);started=time.monotonic();attempts=[];selected=None
        if not space.free(space.start) or not space.free(space.goal):
            attempts.append(dict(rejected_endpoint=space.last_rejection))
        else:
            candidates.sort(key=lambda item:len(set(space.names)^set(item[1]['joints'])))
            for file,old in candidates:
                original=np.array(old['knots']);lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(original,axis=0),axis=1))]
                if lengths[-1]==0:continue
                route=[]
                for point,u in zip(original,lengths/lengths[-1]):
                    proposed=[]
                    for i,joint in enumerate(space.names):
                        if joint in old['joints']:
                            k=old['joints'].index(joint)
                            value=point[k]+(space.start[i]-original[0,k])*(1-u)+(space.goal[i]-original[-1,k])*u
                        else:value=space.start[i]+(space.goal[i]-space.start[i])*u
                        proposed.append(value)
                    route.append(np.array(proposed))
                passed=all(space.edge(a,b) for a,b in zip(route,route[1:]))
                attempts.append(dict(source=str(file.relative_to(HERE)),passed=passed))
                if passed:
                    selected=dict(joints=space.names,knots=[v.tolist() for v in route],
                                  generalized_finger_joint={'right_unused_finger_fold':['right_'+f+'_1_joint' for f in ['middle','ring','little']]} if space.kind=='lid' else {},
                                  candidate_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),
                                  maximum_edge_step=.045,roi=space.roi.tolist(),obstacle_count=len(space.obstacles._objs),
                                  path_length=sum(space.distance(a,b) for a,b in zip(route,route[1:])))
                    break
        result=dict(name=name,scope=__doc__,passed=selected is not None,attempts=attempts,
                    source_sha256=packet['source_sha256'],input_sha256=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest(),
                    planner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    geometry_checker_sha256=hashlib.sha256((HERE/'plan_manipulation_approaches.py').read_bytes()).hexdigest(),
                    collision_queries=space.calls,seconds=time.monotonic()-started,**(selected or {}))
        (folder/(name+'.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(name,result['passed'],'attempts',len(attempts),'checks',space.calls,'seconds',round(result['seconds'],1),flush=True)


if __name__=='__main__':main()
