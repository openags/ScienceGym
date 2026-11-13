"""Fit the actual Inspire fingertips around the Nicolet front lid handle."""
import itertools,json,time
from pathlib import Path
import fcl,numpy as np,trimesh
from source_geometry import ROOT,ASSETS,fk,hand_manager,set_hand

HERE=Path(__file__).resolve().parent

def search():
    setup=json.loads((HERE/'optical_setup.json').read_text());hand=hand_manager('right')
    obstacles=trimesh.collision.CollisionManager();target=None
    for identity in ['nicolet','pike']:
        asset=ASSETS[identity];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
        base=np.eye(4);base[:3,3]=asset['position_m']
        for name in source.graph.nodes_geometry:
            transform,key=source.graph[name];record=setup['parts'].get(identity,{}).get(name)
            if record:transform=np.asarray(record['matrix'])@transform
            obstacles.add_object(identity+'::'+name,source.geometry[key],base@transform)
            if name=='lid_handle_bar':target=obstacles._objs[identity+'::'+name]['obj']
    center=np.asarray(ASSETS['nicolet']['position_m'])+np.asarray(ASSETS['nicolet']['normalization_matrix'])[:3,3]+[-.011,-.306,.247]
    results=[];tested=0;start=time.monotonic()
    for index,thumb2 in itertools.product(np.linspace(.15,1.05,13),np.linspace(0,.6,16)):
        q={f'right_{f}_1_joint':1.1 for f in ['middle','ring','little']}
        q.update(right_index_1_joint=float(index),right_thumb_1_joint=1.1641,right_thumb_2_joint=float(thumb2))
        world=fk(q);inverse=np.linalg.inv(world['right_palm_force_sensor'])
        i=(inverse@world['right_index_force_sensor_3'])[:3,3];th=(inverse@world['right_thumb_force_sensor_4'])[:3,3]
        middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap)
        toward=middle-gap*(middle@gap);toward/=np.linalg.norm(toward);local=np.column_stack([gap,toward,np.cross(gap,toward)])
        for tilt,yaw,bias in itertools.product(np.linspace(-.6,.6,7),[1,-1],[-.002,0,.002]):
            normal=np.array([0,0,yaw]);direction=np.array([np.sin(tilt),np.cos(tilt),0])
            rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
            palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=center-rotation@middle+normal*bias
            set_hand(hand,'right',q,palm);tested+=1
            if hand.in_collision_other(obstacles):continue
            _,pairs=hand.in_collision_internal(return_names=True)
            if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):continue
            def nearest(link):
                result=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),result)
                return float(result.min_distance),np.asarray(result.nearest_points[1])
            a=min([(link,*nearest(link)) for link in hand._objs if 'index' in link],key=lambda x:x[1])
            b=min([(link,*nearest(link)) for link in hand._objs if 'thumb' in link],key=lambda x:x[1])
            if max(a[1],b[1])>.004:continue
            x=a[2][1:]-center[1:];y=b[2][1:]-center[1:]
            dot=float(x@y/max(1e-12,np.linalg.norm(x)*np.linalg.norm(y)))
            if dot>-.5:continue
            palm[:3,3]-=center
            results.append(dict(q=q,palm_matrix=palm.tolist(),finger_gap_m=a[1],thumb_gap_m=b[1],opposition_dot=dot,
                                tilt_rad=float(tilt),yaw_rad=float(yaw),bias_m=float(bias)))
    results.sort(key=lambda c:max(c['finger_gap_m'],c['thumb_gap_m']))
    report=dict(scope=__doc__,handle_center_m=center.tolist(),tested=tested,seconds=time.monotonic()-start,candidates=results)
    (HERE/'previews/optical_cover_search.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(tested=tested,candidates=len(results),best=results[:2],seconds=report['seconds'])),flush=True)

if __name__=='__main__':search()
