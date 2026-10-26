"""Search collision-free local approach curves against unchanged source meshes.

This is geometric development evidence, not force or grasp-stability evidence.
"""
import itertools,json,time
from pathlib import Path
import numpy as np
from source_geometry import hand_manager,asset_manager,set_hand,hand_orientation

HERE=Path(__file__).resolve().parent
profile=json.loads((HERE/'grasp_profile.json').read_text())['left']
results={};started=time.monotonic()
for side in ['left','right']:
    hand=hand_manager(side);obstacles=asset_manager('cooler_white');sign=-1 if side=='left' else 1
    rotation=hand_orientation(side,[0,1,0],[-sign,0,0]);valid=[]
    for power,thumb_early in itertools.product([.4,.7,1,1.5,2,3],[False,True]):
        collisions=[];minimum=1
        for progress in np.linspace(0,1,81):
            q={f'{side}_{finger}_1_joint':.02+(profile['finger_angle_rad']-.02)*progress for finger in ['index','middle','ring','little']}
            q[side+'_thumb_1_joint']=profile['thumb_1_rad']*(1 if thumb_early else progress)
            q[side+'_thumb_2_joint']=profile['thumb_2_rad']*progress
            palm=np.eye(4);palm[:3,:3]=rotation;palm[:3,3]=[sign*(abs(profile['palm_x_m'])+.1*(1-progress)**power),profile['palm_y_m'],.135]
            set_hand(hand,side,q,palm)
            if hand.in_collision_other(obstacles):collisions.append(float(progress))
            else:minimum=min(minimum,hand.min_distance_other(obstacles))
        item=dict(power=power,thumb_early=thumb_early,collision_samples=collisions,minimum_gap_m=minimum)
        if not collisions:valid.append(item)
        print(side,'curve',power,thumb_early,'collisions',len(collisions),flush=True)
    results[side]=valid
(HERE/'previews/closure_search.json').write_text(json.dumps(dict(results=results,seconds=time.monotonic()-started,scope=__doc__),indent=2)+'\n')
print('valid',results,flush=True)
