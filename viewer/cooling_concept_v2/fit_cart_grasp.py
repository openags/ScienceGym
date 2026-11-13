"""Fit the original cart crossbar with source hand geometry, without resizing it."""
import itertools,json,time
from pathlib import Path
import numpy as np
import fcl
from source_geometry import hand_manager,asset_manager,set_hand,hand_orientation

HERE=Path(__file__).resolve().parent
hand=hand_manager('left');cart=asset_manager('utility_cart');rotation=hand_orientation('left',[-1,0,0],[0,0,-1])
candidates=[];tested=0;start=time.monotonic()
for x,z,angle,t2 in itertools.product(np.linspace(.54,.66,13),np.linspace(.9344,1.0044,8),np.linspace(.3,1.2,10),[.12,.3,.5]):
    q={f'left_{finger}_1_joint':float(angle) for finger in ['index','middle','ring','little']}
    q.update(left_thumb_1_joint=1.1641,left_thumb_2_joint=t2)
    palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=[x,-.13,z];set_hand(hand,'left',q,palm);tested+=1
    if hand.in_collision_other(cart):continue
    gap,names,data=hand.min_distance_other(cart,return_names=True,return_data=True)
    if gap>.004:continue
    candidates.append(dict(palm_x_m=float(x),palm_y_m=-.13,palm_z_m=float(z),finger_angle_rad=float(angle),thumb_1_rad=1.1641,thumb_2_rad=t2,minimum_gap_m=gap,nearest_pair=names))
    if len(candidates)%20==0:print('candidates',len(candidates),'tested',tested,flush=True)
report=dict(tested=tested,seconds=time.monotonic()-start,candidates=candidates,scope='Local static surface clearance only; opposition and approach remain to verify')
(HERE/'previews/cart_grasp_search.json').write_text(json.dumps(report,indent=2)+'\n')
print('tested',tested,'candidates',len(candidates),'seconds',report['seconds'],flush=True)
