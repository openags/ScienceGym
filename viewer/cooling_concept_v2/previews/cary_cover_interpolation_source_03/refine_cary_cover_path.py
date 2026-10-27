"""Keep the held hood parallel to its close-fitting rails while lifting clear.

Refine interpolation of the first supported lift; a floating palm trajectory
can otherwise tilt the rigid hood between exact IK endpoints. This preserves
the source asset and checks the real robot and hood against the installed room.
"""
import hashlib,json
import numpy as np
from scipy.spatial.transform import Rotation
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE,load_json,solve_palm
from source_geometry import fk


def main():
    names=['refine_cary_cover_path.py','cary_access_scene.py','optical_choreography.py','previews/cary_cover_carry_02.json','previews/cary_cover_release_01.json'];sources={n:(HERE/n).read_bytes() for n in names}
    original=load_json(names[-2]);release=load_json(names[-1]);scene=CaryAccessScene(cover_candidate=True);grasp=np.array(release['grasp_palm_world']);inverse=np.linalg.inv(grasp);count=0;accepted=[]
    def palm(row):return np.array(row['root'])@fk(row['q'])['right_palm_force_sensor']
    def edge(a,b,depth=0):
        nonlocal count
        base=np.array(a['root']);assert np.max(abs(base-np.array(b['root'])))<1e-10
        pa,pb=palm(a),palm(b);valid=True;position_max=0.;angle_max=0.
        def target(u):
            desired=grasp.copy();desired[:3,3]=pa[:3,3]*(1-u)+pb[:3,3]*u;return desired
        for u in [.25,.5,.75]:
            q={n:a['q'][n]*(1-u)+b['q'][n]*u for n in a['q']};actual=base@fk(q)['right_palm_force_sensor'];desired=target(u)
            position=float(np.linalg.norm(actual[:3,3]-desired[:3,3]));angle=float(np.linalg.norm(Rotation.from_matrix(desired[:3,:3].T@actual[:3,:3]).as_rotvec()));position_max=max(position_max,position);angle_max=max(angle_max,angle)
            scene.set_access(lid=a['lid_m'],cover=actual@inverse);failure=scene.check(base,q);mechanism=scene.access_clearance('cover')
            if position>1e-7 or angle>1e-6 or failure or mechanism:valid=False;break
        if valid:
            accepted.append(dict(position_error_m=position_max,rotation_error_rad=angle_max));return [b]
        if depth>=12:raise RuntimeError('Hood lift interpolation did not converge')
        seed={n:(a['q'][n]+b['q'][n])/2 for n in a['q']};q,position,angle=solve_palm(base,target(.5),seed,waist=True);actual=base@fk(q)['right_palm_force_sensor'];cover=actual@inverse
        scene.set_access(lid=a['lid_m'],cover=cover);failure=scene.check(base,q);mechanism=scene.access_clearance('cover')
        if position>1e-8 or angle>1e-7 or failure or mechanism:raise RuntimeError(str(dict(position=position,angle=angle,failure=failure,mechanism=mechanism[:1])))
        middle={**a,'q':q,'cover_matrix':cover.tolist(),'error_m':position,'rotation_error_rad':angle,'failure':failure,'mechanism_failures':mechanism,'bounded_contacts':scene.last_bounded_contacts};count+=1
        return edge(a,middle,depth+1)+edge(middle,b,depth+1)
    rows=[]
    for row in original['rows']:
        if rows and row['stage']==rows[-1]['stage']=='lift_clear_for_steps':rows.extend(edge(rows[-1],row))
        else:rows.append(row)
    snapshot=HERE/'previews/cary_cover_interpolation_source_03';snapshot.mkdir(exist_ok=True)
    for n,data in sources.items():
        dest=snapshot/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    original.update(rows=rows,contact_interpolation_refinement=dict(inserted_knots=count,accepted_edges=accepted),source_snapshot=str(snapshot.relative_to(HERE)),source_sha256={n:hashlib.sha256(data).hexdigest() for n,data in sources.items()})
    (HERE/'previews/cary_cover_carry_03.json').write_text(json.dumps(original,separators=(',',':'))+'\n');print(json.dumps(dict(inserted_knots=count,rows=len(rows),maximum_position_error_m=max(r['position_error_m'] for r in accepted),maximum_rotation_error_rad=max(r['rotation_error_rad'] for r in accepted))),flush=True)


if __name__=='__main__':main()
