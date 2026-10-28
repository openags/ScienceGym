"""Inspect actual closest points and collision causes before a new hand search."""
import json,itertools
import numpy as np,trimesh,fcl
from source_geometry import ROOT,ASSETS,hand_manager,set_hand,fk
from optical_choreography import HERE,load_json


def main():
    setup=load_json('optical_setup.json');obstacles=trimesh.collision.CollisionManager();center=None
    for identity in ['cary','dra']:
        asset=ASSETS[identity];source=trimesh.load(ROOT/asset['geometry'],force='scene',process=False);group=np.eye(4);group[:3,3]=asset['position_m']
        for name in source.graph.nodes_geometry:
            node,key=source.graph[name];placed=group@np.array(setup['parts'].get(identity,{}).get(name,{}).get('matrix',np.eye(4)))@node
            obstacles.add_object(identity+'::'+name,source.geometry[key],placed)
    a=ASSETS['cary'];base=np.eye(4);base[:3,3]=a['position_m'];center=(base@np.array(a['normalization_matrix'])@np.r_[.185,-.29125,.370,1])[:3];target=obstacles._objs['cary::sample_lid_pull']['obj']
    hand=hand_manager('right');rows=[];counts={}
    for index,thumb,tilt,sign,up in itertools.product([.3,.5,.7,.9],[.1,.3,.5],[-.6,0,.6],[1,-1],[-.005,0,.005,.01,.015]):
        q={f'right_{f}_1_joint':1.1 for f in ['middle','ring','little']};q.update(right_index_1_joint=index,right_thumb_1_joint=1.1641,right_thumb_2_joint=thumb)
        world=fk(q);inv=np.linalg.inv(world['right_palm_force_sensor']);i=(inv@world['right_index_force_sensor_3'])[:3,3];th=(inv@world['right_thumb_force_sensor_4'])[:3,3];middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap);forward=middle-gap*(middle@gap);forward/=np.linalg.norm(forward);local=np.column_stack([gap,forward,np.cross(gap,forward)])
        normal=np.array([0,sign,0]);direction=np.array([np.sin(tilt),0,-np.cos(tilt)]);rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
        palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=center-rotation@middle+[0,0,up];set_hand(hand,'right',q,palm)
        _,pairs,contacts=hand.in_collision_other(obstacles,return_names=True,return_data=True)
        for pair in pairs:
            key=' | '.join(sorted(pair));counts[key]=counts.get(key,0)+1
        def near(n):
            r=fcl.DistanceResult();fcl.distance(hand._objs[n]['obj'],target,fcl.DistanceRequest(enable_nearest_points=True),r);return float(r.min_distance),np.array(r.nearest_points[1]).tolist()
        a=min([(n,*near(n)) for n in hand._objs if 'index' in n],key=lambda row:row[1]);b=min([(n,*near(n)) for n in hand._objs if 'thumb' in n],key=lambda row:row[1]);depth=max((abs(float(c.depth)) for c in contacts),default=0.)
        row=dict(index=index,thumb=thumb,tilt=tilt,sign=sign,up=up,pairs=sorted(pairs),depth_m=depth,index_nearest=a,thumb_nearest=b,palm=palm.tolist(),q=q)
        row['score']=10*depth+max(max(a[1],0),max(b[1],0))+.001*len(pairs);rows.append(row)
    rows.sort(key=lambda r:r['score']);output=dict(center=center.tolist(),tested=len(rows),clear_count=sum(not r['pairs'] for r in rows),collision_counts=sorted(counts.items(),key=lambda p:-p[1]),best=rows[:20])
    (HERE/'previews/cary_grasp_diagnosis.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(output),flush=True)


if __name__=='__main__':main()
