"""Tighten clear cover-grasp candidates against the actual source handle."""
import hashlib,json
import numpy as np,fcl
from scipy.optimize import minimize
from cary_access_scene import CaryAccessScene
from optical_choreography import HERE,load_json
from source_geometry import hand_manager,set_hand


def main():
    source=load_json('previews/cary_cover_grasps.json');scene=CaryAccessScene(local_only=True,cover_candidate=True);scene.set_access(lid=.305)
    obstacles=scene.local_obstacles();target=obstacles._objs['cary::extension_pull_bar']['obj'];hand=hand_manager('right');results=[]
    for index,c in enumerate(source['candidates']):
        initial=np.array([c['q']['right_index_1_joint'],c['q']['right_thumb_2_joint'],0.,0.]);bounds=[(initial[0]-.055,initial[0]+.055),(initial[1]-.055,initial[1]+.055),(-.002,.002),(-.002,.002)]
        def evaluate(values):
            q={**c['q'],'right_index_1_joint':float(values[0]),'right_thumb_2_joint':float(values[1])};palm=np.array(c['palm_matrix']);palm[:3,3]+=source['handle_center_m'];palm[:3,3]+=[0,values[2],values[3]];set_hand(hand,'right',q,palm)
            if hand.in_collision_other(obstacles):return 1e6,None
            _,pairs=hand.in_collision_internal(return_names=True)
            if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):return 1e6,None
            def near(n):
                r=fcl.DistanceResult();fcl.distance(hand._objs[n]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),r);return float(r.min_distance),np.array(r.nearest_points[1]).tolist()
            a=min([(n,*near(n)) for n in hand._objs if 'index' in n],key=lambda r:r[1]);b=min([(n,*near(n)) for n in hand._objs if 'thumb' in n],key=lambda r:r[1])
            value=1e6*((a[1]-.000025)**2+(b[1]-.000025)**2)
            return value,dict(q=q,palm_matrix=palm.tolist(),finger_gap_m=a[1],thumb_gap_m=b[1],finger_part=a[0],thumb_part=b[0],contacts=[a[2],b[2]])
        best=minimize(lambda x:evaluate(x)[0],initial,method='Powell',bounds=bounds,options={'xtol':1e-7,'ftol':1e-10,'maxiter':60})
        choices=[(evaluate(x)[0],x) for x in [initial,best.x]];score,selected=min(choices,key=lambda r:r[0]);score,result=evaluate(selected)
        if result is None:continue
        # Centre the two unequal clearances without crossing a contact face.
        # Use the handle's radial plane, excluding tangential X separation.
        axis=np.array(result['contacts'][0])-result['contacts'][1];axis[0]=0.;axis/=np.linalg.norm(axis)
        balanced=selected.copy();delta=(result['thumb_gap_m']-result['finger_gap_m'])/2
        balanced[2]+=axis[1]*delta;balanced[3]+=axis[2]*delta
        _,other=evaluate(balanced)
        if other is not None and min(other['finger_gap_m'],other['thumb_gap_m'])>1e-6 and max(other['finger_gap_m'],other['thumb_gap_m'])<max(result['finger_gap_m'],result['thumb_gap_m']):result=other
        palm=np.array(result['palm_matrix']);palm[:3,3]-=source['handle_center_m'];result['palm_matrix']=palm.tolist();result.update(source_candidate=index,optimizer_success=bool(best.success),queries=int(best.nfev));results.append(result)
        print(index,'gaps',result['finger_gap_m'],result['thumb_gap_m'],'queries',best.nfev,flush=True)
    results.sort(key=lambda r:max(r['finger_gap_m'],r['thumb_gap_m']));source.update(scope=__doc__,candidates=results,source_candidates='previews/cary_cover_grasps.json',source_candidates_sha256=hashlib.sha256((HERE/'previews/cary_cover_grasps.json').read_bytes()).hexdigest(),refiner_sha256=hashlib.sha256((HERE/'refine_cary_grasps.py').read_bytes()).hexdigest())
    (HERE/'previews/cary_cover_grasps_refined.json').write_text(json.dumps(source,indent=2)+'\n');print('refined',len(results),flush=True)


if __name__=='__main__':main()
