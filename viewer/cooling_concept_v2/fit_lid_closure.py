"""Search a complete pinch approach/release, not just the final contact pose."""
import itertools,json,time
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from source_geometry import hand_manager,asset_manager,set_hand

HERE=Path(__file__).resolve().parent;profile=json.loads((HERE/'grasp_profile.json').read_text())['lid']
hand=hand_manager('right');obstacles=asset_manager('cooler_white');pose=np.array(profile['palm_matrix']);pose[2,3]+=.101006
lid=trimesh.creation.cylinder(radius=.037,height=.002,sections=48);lid.apply_translation([0,0,.101006]);obstacles.add_object('cover',lid)
tab=trimesh.creation.box(extents=[.014,.002,.040]);rotation=np.eye(4);rotation[:3,:3]=Rotation.from_euler('z',profile['tab_normal_angle_rad']-np.pi/2).as_matrix();rotation[:3,3]=[0,-.026,.122006];obstacles.add_object('tab',tab,rotation)
# Also require a grasp that can be used when the same cover rests on a table.
table=trimesh.creation.box(extents=[2,2,.05]);table.apply_translation([0,0,.075006]);obstacles.add_object('resting_plane',table)
valid=[];tested=0;start=time.monotonic()
for dx,dy,dz,power in itertools.product([-.03,0,.03],[-.10,-.06,0,.04],[.04,.08,.12],[.5,1,2]):
    collisions=0;gap=1
    for fraction in np.linspace(0,1,81):
        q={**profile['q'],'right_index_1_joint':profile['q']['right_index_1_joint']*fraction,'right_thumb_2_joint':profile['q']['right_thumb_2_joint']*fraction}
        palm=pose.copy();palm[:3,3]+=np.array([dx,dy,dz])*(1-fraction)**power;set_hand(hand,'right',q,palm)
        if hand.in_collision_other(obstacles):collisions+=1;break
        gap=min(gap,hand.min_distance_other(obstacles))
    tested+=1
    if not collisions:valid.append(dict(offset_m=[dx,dy,dz],power=power,minimum_gap_m=gap))
    if tested%24==0:print('tested',tested,'valid',len(valid),flush=True)
valid.sort(key=lambda c:np.linalg.norm(c['offset_m']))
(HERE/'previews/lid_closure_search.json').write_text(json.dumps(dict(tested=tested,candidates=valid,seconds=time.monotonic()-start,scope=__doc__),indent=2)+'\n')
print('valid',valid[:10],flush=True)
