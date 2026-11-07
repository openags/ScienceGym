"""Review the selected closure with both initial and adjusted reflector poses."""
import hashlib,json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from source_geometry import hand_manager,asset_manager,set_hand

HERE=Path(__file__).resolve().parent;source=HERE/'grasp_profile.json';profile=json.loads(source.read_text())['lid']
hand=hand_manager('right');pose=np.array(profile['palm_matrix']);pose[2,3]+=.101006;failures=[];minimum=1
for shift in [0,.025]:
    obstacles=asset_manager('cooler_white')
    for name,item in obstacles._objs.items():
        if 'solar_reflector' in name or 'frame_carriage' in name:
            item['obj'].setTranslation(item['obj'].getTranslation()+[shift,0,0]);obstacles._manager.update(item['obj'])
    lid=trimesh.creation.cylinder(radius=.037,height=.002,sections=48);lid.apply_translation([0,0,.101006]);obstacles.add_object('cover',lid)
    tab=trimesh.creation.box(extents=[.014,.002,.04]);transform=np.eye(4);transform[:3,:3]=Rotation.from_euler('z',profile['tab_normal_angle_rad']-np.pi/2).as_matrix();transform[:3,3]=[0,-.026,.122006];obstacles.add_object('tab',tab,transform)
    table=trimesh.creation.box(extents=[2,2,.05]);table.apply_translation([0,0,.075006]);obstacles.add_object('resting_plane',table)
    for fraction in np.linspace(0,1,101):
        q={**profile['q'],'right_index_1_joint':profile['q']['right_index_1_joint']*fraction,'right_thumb_2_joint':profile['q']['right_thumb_2_joint']*fraction}
        palm=pose.copy();palm[:3,3]+=np.asarray(profile['approach_offset_m'])*(1-fraction)**profile['approach_power'];set_hand(hand,'right',q,palm)
        collision,pairs=hand.in_collision_other(obstacles,return_names=True)
        if collision:failures.append(dict(reflector_shift_m=shift,fraction=float(fraction),pairs=sorted(pairs)))
        else:minimum=min(minimum,hand.min_distance_other(obstacles))
report=dict(passed=not failures,samples=202,minimum_gap_m=minimum,failures=failures,profile_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),scope=__doc__)
(HERE/'previews/lid_transfer_edges.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if failures:raise SystemExit(1)
