"""Find a lower ordinary-tweezer carrying posture in the free optical aisle.

The annular carrier stays horizontal. Preference for a palm below shoulder
height and an elbow below the shoulder is a presentation/handling inference,
not a manufacturer ergonomic rule or a dynamic stability qualification.
"""
import hashlib,itertools,json
import numpy as np
from scipy.spatial.transform import Rotation
from optical_choreography import HERE,canonical,load_json,solve_palm
from optical_delivery import DeliveryScene
from plan_optical_tool_pickup import seed_targets
from source_geometry import fk


def main():
    scene=DeliveryScene();walk=load_json('previews/optical_white_delivery_walk.json');base=np.array(walk['waypoints'][1]);carry=walk['rows'][0]['q'];rest=load_json('previews/optical_tool_pickup_path.json')['entry'][0]['q'];requests=[]
    for x,y,z,yaw in itertools.product([.25,.32],[-.16,-.08],[.94],[0.,-.8,-1.4,.8]):
        holder=np.eye(4);holder[:3,:3]=Rotation.from_euler('z',yaw).as_matrix();holder[:3,3]=[x,y,z];target=base@holder@scene.holder_T_tool@scene.tool_T_palm
        for seed in [carry,{**rest,'right_elbow_joint':.8,'waist_pitch_joint':.1}]:requests.append(dict(base=base.tolist(),target=target.tolist(),q={**canonical(seed),**scene.hand_q(scene.fit['carrier_grip_closure'])},holder_local=holder.tolist()))
    candidates=[]
    for i,request in enumerate(seed_targets(requests)):
        q,error,angular=solve_palm(base,np.array(request['target']),request['q'],waist=True);world={n:base@m for n,m in fk(q).items()}
        palm=world['right_palm_force_sensor'][2,3];shoulder=world['right_shoulder_pitch_link'][2,3];elbow=world['right_elbow_link'][2,3]
        failure=scene.check(base,q,tool_held=True,closure=scene.fit['carrier_grip_closure'],held_specimen='white')
        low=bool(palm<=shoulder+.03 and elbow<=shoulder+.03)
        row=dict(q=q,root=base.tolist(),holder_local=request['holder_local'],error_m=error,rotation_error_rad=angular,palm_z_m=float(palm),shoulder_z_m=float(shoulder),elbow_z_m=float(elbow),failure=failure,passed=error<1e-7 and angular<1e-6 and not failure and low);candidates.append(row);print('carry',i,row['passed'],'heights',palm,elbow,shoulder,'error',error,'failure',failure,flush=True)
    passed=[r for r in candidates if r['passed']];passed.sort(key=lambda r:r['elbow_z_m']+abs(r['q']['waist_yaw_joint'])*.1+r['q']['waist_pitch_joint']*.1)
    result=dict(scope=__doc__,candidates=candidates,selected=passed[0] if passed else None,source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['fit_delivery_carry.py','optical_delivery.py','previews/optical_white_delivery_walk.json']})
    (HERE/'previews/optical_delivery_carry.json').write_text(json.dumps(result,indent=2)+'\n');print('lower carrying candidates',len(passed),flush=True)


if __name__=='__main__':main()
