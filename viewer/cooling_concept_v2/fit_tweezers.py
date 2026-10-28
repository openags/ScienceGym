"""Fit opposed source-hand pads to ordinary tweezers, without a hidden attachment."""
import argparse,itertools,json,time
from pathlib import Path
import fcl,numpy as np,trimesh
from scipy.spatial.transform import Rotation
from source_geometry import fk,hand_manager,set_hand
from tweezers_geometry import meshes,provenance,RAW_X_OFFSET_M

HERE=Path(__file__).resolve().parent


def fit(side='right'):
    start=time.monotonic();hand=hand_manager(side);tool=trimesh.collision.CollisionManager()
    for name,mesh in meshes(0).items():tool.add_object(name,mesh)
    results=[];tested=0
    for index,thumb2 in itertools.product(np.linspace(.35,.75,9),np.linspace(.08,.38,13)):
        q={f'{side}_{f}_1_joint':1.1 for f in ['middle','ring','little']}
        q.update({f'{side}_index_1_joint':float(index),f'{side}_thumb_1_joint':1.1641,f'{side}_thumb_2_joint':float(thumb2)})
        world=fk(q);inverse=np.linalg.inv(world[side+'_palm_force_sensor'])
        i=(inverse@world[side+'_index_force_sensor_3'])[:3,3];th=(inverse@world[side+'_thumb_force_sensor_4'])[:3,3]
        middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap)
        toward=middle-gap*(middle@gap);toward/=np.linalg.norm(toward);local=np.column_stack([gap,toward,np.cross(gap,toward)])
        for tilt,x,bias in itertools.product(np.linspace(-.9,.9,7),[.06,.07,.08,.09],[-.002,0,.002]):
            normal=np.array([0,1.,0]);direction=np.array([-np.cos(tilt),0,np.sin(tilt)])
            rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
            center=np.array([x-RAW_X_OFFSET_M,bias,.00575]);palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=center-rotation@middle
            set_hand(hand,side,q,palm);tested+=1
            if hand.in_collision_other(tool):continue
            _,pairs=hand.in_collision_internal(return_names=True)
            if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):continue
            def nearest(finger):
                out=[]
                for link in hand._objs:
                    if finger not in link:continue
                    for name in ['ptfe_spring_arm_1','ptfe_spring_arm_-1']:
                        result=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],tool._objs[name]['obj'],fcl.DistanceRequest(enable_nearest_points=True),result)
                        out.append((float(result.min_distance),name,np.asarray(result.nearest_points[1]).tolist(),link))
                return min(out)
            a,b=nearest('index'),nearest('thumb')
            if max(a[0],b[0])>.0015 or a[1]==b[1]:continue
            if min(a[2][0],b[2][0])<.045-RAW_X_OFFSET_M:continue
            results.append(dict(q=q,palm_matrix=palm.tolist(),index_contact=a,thumb_contact=b,tilt_rad=float(tilt),body_grasp_x_m=x,bias_m=bias))
    results.sort(key=lambda r:max(r['index_contact'][0],r['thumb_contact'][0]))
    report=dict(scope=__doc__,side=side,source=provenance(),tested=tested,seconds=time.monotonic()-start,candidates=results)
    (HERE/'previews'/('tweezers_'+side+'_fit.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=tested,candidates=len(results),best=results[:2],seconds=report['seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--side',default='right');args=p.parse_args();fit(args.side)
