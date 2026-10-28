"""Constrain interpolation between lid-contact IK knots to the sliding pull.

Exact endpoint IK alone can bow away from a handle between knots. Subdivide
and project intermediate postures onto the source contact transform, while
checking the actual whole-body scene. The exported path still needs review.
"""
import argparse,hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE,load_json,solve_palm
from source_geometry import fk


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',default='previews/cary_lid_operation_07.json');parser.add_argument('--output',default='previews/cary_lid_operation_08.json');parser.add_argument('--snapshot',default='previews/cary_lid_interpolation_source_08');args=parser.parse_args()
    names=['refine_cary_lid_path.py','cary_access_scene.py','optical_choreography.py',args.input];sources={n:(HERE/n).read_bytes() for n in names}
    snapshot=HERE/args.snapshot;snapshot.mkdir(exist_ok=False)
    for n,data in sources.items():
        dest=snapshot/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    original=load_json(names[-1]);scene=CaryAccessScene(cover_candidate=True);base=np.array(original['root']);grasp=np.array(original['grasp']['target']);count=0;maximum_error=0.;accepted=[]
    initial_lid=original.get('initial_lid_m',0.);cover=np.array(original.get('cover_matrix',np.eye(4)))
    def target(lid):
        value=grasp.copy();value[1,3]+=lid-initial_lid;return value
    def edge(a,b,depth=0):
        nonlocal count,maximum_error
        valid=True;largest=0.
        for u in [.25,.5,.75]:
            q={n:a['q'][n]*(1-u)+b['q'][n]*u for n in a['q']};lid=a['lid_m']*(1-u)+b['lid_m']*u
            actual=base@fk(q)['right_palm_force_sensor'];desired=target(lid)
            position=float(np.linalg.norm(actual[:3,3]-desired[:3,3]));angle=float(np.linalg.norm(Rotation.from_matrix(desired[:3,:3].T@actual[:3,:3]).as_rotvec()));largest=max(largest,position)
            scene.set_access(lid=lid,cover=cover);failure=scene.check(base,q)
            if position>2e-5 or angle>2e-4 or failure:valid=False;break
        if valid:
            maximum_error=max(maximum_error,largest);accepted.append(dict(from_lid_m=a['lid_m'],to_lid_m=b['lid_m'],maximum_sampled_palm_error_m=largest));return [b]
        if depth>=12:raise RuntimeError('Lid contact interpolation did not converge')
        lid=(a['lid_m']+b['lid_m'])/2;seed={n:(a['q'][n]+b['q'][n])/2 for n in a['q']};q,position,angle=solve_palm(base,target(lid),seed,waist=True)
        scene.set_access(lid=lid,cover=cover);failure=scene.check(base,q)
        if position>1e-7 or angle>1e-6 or failure:raise RuntimeError(str(dict(lid=lid,position=position,angle=angle,failure=failure)))
        middle=dict(stage='slide',q=q,lid_m=lid,error_m=position,rotation_error_rad=angle,failure=failure);count+=1
        return edge(a,middle,depth+1)+edge(middle,b,depth+1)
    result=[]
    for row in original['contact']:
        if result and row['stage']==result[-1]['stage']=='slide':result.extend(edge(result[-1],row))
        else:result.append(row)
    original.update(contact=result,contact_interpolation_refinement=dict(inserted_knots=count,maximum_sampled_palm_error_m=maximum_error,accepted_edges=accepted),source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(data).hexdigest() for n,data in sources.items()})
    (HERE/args.output).write_text(json.dumps(original,indent=2)+'\n');print(json.dumps(dict(inserted_knots=count,contact_knots=len(result),maximum_sampled_palm_error_m=maximum_error)),flush=True)


if __name__=='__main__':main()
