"""Reduce the selected lid grip's two clearances using actual hand meshes."""
import hashlib,json
import fcl,numpy as np
from scipy.optimize import minimize
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE,load_json
from source_geometry import hand_manager,set_hand


def main():
    source=load_json('previews/cary_lid_grasps.json');candidate=source['candidates'][16]
    scene=CaryAccessScene(local_only=True,cover_candidate=True);obstacles=scene.local_obstacles();target=obstacles._objs['cary::sample_lid_pull']['obj'];hand=hand_manager('right')
    initial=np.array([candidate['q']['right_index_1_joint'],candidate['q']['right_thumb_2_joint'],0.,0.]);bounds=[(initial[0]-.10,initial[0]+.10),(initial[1]-.10,initial[1]+.10),(-.003,.003),(-.003,.003)];records=[]
    def evaluate(values):
        q={**candidate['q'],'right_index_1_joint':float(values[0]),'right_thumb_2_joint':float(values[1])};palm=np.array(candidate['palm_matrix']);palm[:3,3]+=source['handle_center_m'];palm[:3,3]+=[0,values[2],values[3]];set_hand(hand,'right',q,palm)
        if hand.in_collision_other(obstacles):return 1e6,None
        _,pairs=hand.in_collision_internal(return_names=True)
        if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):return 1e6,None
        def gap(link):
            result=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),result);return float(result.min_distance),np.array(result.nearest_points[1]).tolist()
        a=min([(n,*gap(n)) for n in hand._objs if 'index' in n],key=lambda v:v[1]);b=min([(n,*gap(n)) for n in hand._objs if 'thumb' in n],key=lambda v:v[1]);palm[:3,3]-=source['handle_center_m']
        row={**candidate,'q':q,'palm_matrix':palm.tolist(),'finger_part':a[0],'thumb_part':b[0],'finger_gap_m':a[1],'thumb_gap_m':b[1],'contacts':[a[2],b[2]]}
        cost=1e6*((a[1]-.0001)**2+(b[1]-.0001)**2);records.append((cost,values.copy(),row));return cost,row
    result=minimize(lambda x:evaluate(x)[0],initial,method='Powell',bounds=bounds,options={'xtol':1e-8,'ftol':1e-10,'maxiter':60})
    if not records:raise RuntimeError('No clear lid grip')
    score,values,best=min(records,key=lambda r:r[0]);palm=np.array(best['palm_matrix']);initial_gap=max(candidate['finger_gap_m'],candidate['thumb_gap_m'])
    assert max(best['finger_gap_m'],best['thumb_gap_m'])<initial_gap
    source.update(scope=__doc__,candidates=[best],source_candidate=16,optimizer_success=bool(result.success),queries=int(result.nfev),source_candidates_sha256=hashlib.sha256((HERE/'previews/cary_lid_grasps.json').read_bytes()).hexdigest(),refiner_sha256=hashlib.sha256((HERE/'refine_cary_lid_grasp.py').read_bytes()).hexdigest())
    (HERE/'previews/cary_lid_grasps_refined.json').write_text(json.dumps(source,indent=2)+'\n');print(json.dumps(dict(finger_gap_m=best['finger_gap_m'],thumb_gap_m=best['thumb_gap_m'],queries=result.nfev)),flush=True)


if __name__=='__main__':main()
