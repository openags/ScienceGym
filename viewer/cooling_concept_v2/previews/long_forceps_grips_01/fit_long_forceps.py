"""Find opposed Inspire finger contacts on the long forceps' actual mesh."""
import hashlib
import itertools
import json
import time
import fcl
import numpy as np
import trimesh
from scipy.optimize import least_squares
from long_forceps import meshes, OUT
from optical_choreography import HERE, JOINTS
from source_geometry import fk, hand_manager, set_hand


def main():
    output = HERE/'previews/long_forceps_grips_01'
    output.mkdir(exist_ok=False)
    source_pins = {}
    for name in ['fit_long_forceps.py','long_forceps.py','source_geometry.py']:
        data = (HERE/name).read_bytes()
        (output/name).write_bytes(data)
        source_pins[name] = hashlib.sha256(data).hexdigest()
    hand = hand_manager('right')
    tool = trimesh.collision.CollisionManager()
    for name, mesh in meshes(1.).items():
        tool.add_object(name, mesh)
    candidates = []
    started = time.monotonic()
    def contacts(q, palm):
        set_hand(hand,'right',q,palm)
        if hand.in_collision_other(tool):
            return None
        _, pairs = hand.in_collision_internal(return_names=True)
        if any('thumb' in a and any(f in b for f in ['index','middle','ring','little']) or
               'thumb' in b and any(f in a for f in ['index','middle','ring','little']) for a,b in pairs):
            return None
        found = []
        for finger in ['index','thumb']:
            near = []
            for link in hand._objs:
                if finger not in link:
                    continue
                for name in ['serrated_arm_1','serrated_arm_-1']:
                    d = fcl.DistanceResult()
                    fcl.distance(hand._objs[link]['obj'], tool._objs[name]['obj'],
                        fcl.DistanceRequest(enable_nearest_points=True), d)
                    near.append((float(d.min_distance),name,np.array(d.nearest_points[1]).tolist(),link))
            found.append(min(near))
        return found
    tested = 0
    for index, thumb in itertools.product(np.linspace(.35,1.05,11),np.linspace(.05,.65,13)):
        q = {f'right_{f}_1_joint':1.1 for f in ['middle','ring','little']}
        q.update(right_index_1_joint=float(index),right_thumb_1_joint=1.1641,right_thumb_2_joint=float(thumb))
        world = fk(q)
        inverse = np.linalg.inv(world['right_palm_force_sensor'])
        a = (inverse@world['right_index_force_sensor_3'])[:3,3]
        b = (inverse@world['right_thumb_force_sensor_4'])[:3,3]
        middle = (a+b)/2
        normal = b-a
        normal /= np.linalg.norm(normal)
        forward = middle-normal*(middle@normal)
        forward /= np.linalg.norm(forward)
        local = np.column_stack([normal,forward,np.cross(normal,forward)])
        for tilt, x, bias in itertools.product([-.9,-.6,-.3,0.,.3,.6,.9],[.110,.125,.140,.150],[-.002,0.,.002]):
            normal = np.array([0.,1.,0.])
            forward = np.array([-np.cos(tilt),0.,np.sin(tilt)])
            palm = np.eye(4)
            palm[:3,:3] = np.column_stack([normal,forward,np.cross(normal,forward)])@local.T
            palm[:3,3] = np.array([x-.100,bias,.006])-palm[:3,:3]@middle
            tested += 1
            near = contacts(q,palm)
            if near is None:
                continue
            a,b = near
            if max(a[0],b[0])>.001 or a[1]==b[1] or abs(a[2][0]-b[2][0])>.02:
                continue
            candidates.append(dict(q=dict(q),palm_matrix=palm.tolist(),index_contact=a,thumb_contact=b,
                                   tilt_rad=tilt,body_grasp_x_m=x,bias_m=bias))
    candidates.sort(key=lambda r:max(r['index_contact'][0],r['thumb_contact'][0]))
    print('searched',tested,'candidates',len(candidates),flush=True)
    names = ['right_index_1_joint','right_thumb_2_joint']
    bounds = np.array([[JOINTS[n]['limits']['lower'],JOINTS[n]['limits']['upper']] for n in names])
    refined = []
    for i,c in enumerate(candidates[:80]):
        q = dict(c['q'])
        palm = np.array(c['palm_matrix'])
        def residual(values):
            q.update(dict(zip(names,values)))
            set_hand(hand,'right',q,palm)
            gaps = []
            for contact in [c['index_contact'],c['thumb_contact']]:
                d = fcl.DistanceResult()
                fcl.distance(hand._objs[contact[3]]['obj'],tool._objs[contact[1]]['obj'],fcl.DistanceRequest(),d)
                gaps.append(float(d.min_distance))
            return np.array(gaps)-.000125
        values = np.clip([q[n] for n in names],bounds[:,0]+1e-8,bounds[:,1]-1e-8)
        fit = least_squares(residual,values,bounds=(bounds[:,0],bounds[:,1]),diff_step=1e-4,
                            max_nfev=80,ftol=1e-12,xtol=1e-12,gtol=1e-12)
        residual(fit.x)
        near = contacts(q,palm)
        if near is None or min(v[0] for v in near)<1e-6 or max(v[0] for v in near)>.00025 or near[0][1]==near[1][1]:
            continue
        refined.append(dict(source_candidate=i,q={n:float(v) for n,v in q.items()},palm_matrix=palm.tolist(),
            index_contact=near[0],thumb_contact=near[1],body_grasp_x_m=c['body_grasp_x_m'],tilt_rad=c['tilt_rad']))
    report = dict(scope=__doc__,tested=tested,candidates=refined,coarse_candidates=candidates,
        seconds=time.monotonic()-started,source_sha256=source_pins,
        asset_revision_sha256=hashlib.sha256((OUT/'revision.json').read_bytes()).hexdigest(),
        limitations=['Local mesh contact only; no approach, body reach, spring-force or actuation qualification.'])
    (output/'grasps.json').write_text(json.dumps(report,indent=2)+'\n')
    print('refined',len(refined),'seconds',report['seconds'],flush=True)


if __name__=='__main__':
    main()
