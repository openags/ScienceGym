"""Fit a hand to an ordinary folded pull tab on an inferred aluminum cover.

The paper does not specify this tab. It is an explicit handling detail for the
presentation, not a modification to a commercial apparatus or a physics result.
"""
import itertools,json,time
from pathlib import Path
import numpy as np
import trimesh,fcl
from scipy.spatial.transform import Rotation
from source_geometry import fk,hand_manager,asset_manager,set_hand

HERE=Path(__file__).resolve().parent
hand=hand_manager('right');obstacles=asset_manager('cooler_white')
lid=trimesh.creation.cylinder(radius=.037,height=.002,sections=48);lid.apply_translation([0,0,.101006])
tab=trimesh.creation.box(extents=[.014,.002,.040]);tab.apply_translation([0,-.026,.122006])
obstacles.add_object('aluminum_cover',lid);obstacles.add_object('folded_pull_tab',tab)
tab_object=obstacles._objs['folded_pull_tab']['obj'];results=[];tested=0;start=time.monotonic()
for index,thumb2 in itertools.product(np.linspace(.55,1.05,11),np.linspace(.15,.5,15)):
    q={f'right_{finger}_1_joint':1.1 for finger in ['middle','ring','little']}
    q.update(right_index_1_joint=float(index),right_thumb_1_joint=1.1641,right_thumb_2_joint=float(thumb2))
    world=fk(q);inverse=np.linalg.inv(world['right_palm_force_sensor']);i=(inverse@world['right_index_force_sensor_3'])[:3,3];th=(inverse@world['right_thumb_force_sensor_4'])[:3,3]
    middle=(i+th)/2;gap=th-i;gap/=np.linalg.norm(gap);toward=middle-gap*(middle@gap);toward/=np.linalg.norm(toward);local=np.column_stack([gap,toward,np.cross(gap,toward)])
    for angle,normal_angle in itertools.product(np.linspace(-np.pi/2,np.pi/2,13),[0,np.pi/2,np.pi,3*np.pi/2]):
        normal=np.array([np.cos(normal_angle),np.sin(normal_angle),0]);direction=np.array([normal[1]*np.sin(angle),-normal[0]*np.sin(angle),-np.cos(angle)])
        rotation=np.column_stack([normal,direction,np.cross(normal,direction)])@local.T
        tab_transform=np.eye(4);tab_transform[:3,:3]=Rotation.from_euler('z',normal_angle-np.pi/2).as_matrix();center=np.array([0,-.026,.122006]);tab_transform[:3,3]=center-tab_transform[:3,:3]@center;obstacles.set_transform('folded_pull_tab',tab_transform)
        palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=[0,-.026,.135006]-rotation@middle;set_hand(hand,'right',q,palm);tested+=1
        if hand.in_collision_other(obstacles):continue
        collision,pairs=hand.in_collision_internal(return_names=True)
        if any(('thumb' in a and any(f in b for f in ['index','middle','ring','little'])) or ('thumb' in b and any(f in a for f in ['index','middle','ring','little'])) for a,b in pairs):continue
        def nearest(link):
            r=fcl.DistanceResult();fcl.distance(hand._objs[link]['obj'],tab_object,fcl.DistanceRequest(enable_nearest_points=True),r);return float(r.min_distance),np.asarray(r.nearest_points[1])
        fingers=[(l,*nearest(l)) for l in hand._objs if 'index' in l];thumbs=[(l,*nearest(l)) for l in hand._objs if 'thumb' in l]
        a=min(fingers,key=lambda x:x[1]);b=min(thumbs,key=lambda x:x[1])
        if max(a[1],b[1])>.008:continue
        opposed=((a[2]-center)@normal)*((b[2]-center)@normal)<0
        results.append(dict(q=q,palm_matrix=palm.tolist(),angle_rad=float(angle),tab_normal_angle_rad=float(normal_angle),finger_gap_m=a[1],thumb_gap_m=b[1],finger_link=a[0],thumb_link=b[0],opposed=bool(opposed)))
results.sort(key=lambda x:(not x['opposed'],x['finger_gap_m']+x['thumb_gap_m']))
report=dict(candidates=results,tested=tested,seconds=time.monotonic()-start,scope=__doc__,inferred_cover=dict(radius_m=.037,thickness_m=.002,pull_tab_size_m=[.014,.002,.040],pull_tab_center_m=[0,-.026,.021]))
(HERE/'previews/lid_grasp_search.json').write_text(json.dumps(report,indent=2)+'\n')
print('tested',tested,'candidates',len(results),'best',results[:1],flush=True)
