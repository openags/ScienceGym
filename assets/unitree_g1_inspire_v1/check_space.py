"""G1-only static space evidence. No H2 poses or assumed wrist adapters."""
import json
import math
from pathlib import Path
import numpy as np
from kinematics import HERE,Robot
from audit import sha

ROOT=HERE.parents[1]


def build():
    robot=Robot();rng=np.random.default_rng(20261024)
    # Restricted transit-pose design range. This is not a learned walking set.
    intervals={side+'_'+joint:[-.15,.15] for side in ['left','right']
               for joint in ['shoulder_pitch_joint','shoulder_roll_joint','shoulder_yaw_joint','elbow_joint']}
    poses=[{}]+[{name:float(rng.uniform(*interval)) for name,interval in intervals.items()} for _ in range(128)]
    hand_bounds=[]
    for side in ['left','right']:
        wrist=side+'_wrist_yaw_link';lengths={wrist:0.}
        for j in robot.joints:
            if j['parent'] in lengths:lengths[j['id']]=lengths[j['parent']]+np.linalg.norm(np.asarray(j['origin_matrix'])[:3,3])
        radius=max(lengths[name]+np.linalg.norm(corners,axis=1).max() for name,corners in robot.corners.items() if name in lengths)
        hand_bounds.append(dict(side=side,wrist_link=wrist,all_joint_angles_radius_m=float(radius)))
    samples=[]
    for q in poses:
        transforms=robot.fk(q);bounds=robot.link_bounds(q)
        corners=np.concatenate([[[x,y,z] for x in b[:,0] for y in b[:,1] for z in b[:,2]] for b in bounds.values()])
        radius=float(np.linalg.norm(corners[:,:2],axis=1).max())
        wrist_radius=max(np.linalg.norm(transforms[h['wrist_link']][:2,3])+h['all_joint_angles_radius_m'] for h in hand_bounds)
        samples.append(dict(coordinates=q,visual_box_radius_m=radius,body_hand_bound_m=float(max(radius,wrist_radius)),height_m=float(corners[:,2].max())))
    selected=math.ceil(max(s['body_hand_bound_m'] for s in samples)*100)/100
    # Additional load is a declared reservation, not an executed carrying pose.
    tray_dimensions=[.30,.20,.05];tray_center=[.40,0,1.0]
    tray_radius=max(math.hypot(tray_center[0]+sx*tray_dimensions[0]/2,sy*tray_dimensions[1]/2) for sx in [-1,1] for sy in [-1,1])
    record=dict(schema_version=1,status='source_based_static_design_samples',body='Unitree G1 29DoF rev 1.0',hands='Inspire FTP',
      samples=len(samples),transit_pose_intervals_rad=intervals,pose_samples=samples,hand_bounds=hand_bounds,
      selected_body_hand_radius_m=selected,additional_route_margin_m=.10,minimum_required_half_width_m=selected+.10,
      transit_height_m=math.ceil(max(s['height_m'] for s in samples)*100)/100+.10,
      small_tray_reservation=dict(dimensions_m=tray_dimensions,center_from_pelvis_xy_and_floor_z_m=tray_center,radial_extent_m=tray_radius,
        covered_by_selected_radius=tray_radius<=selected,grasp_and_load_qualified=False,scope='Ordinary 300 x 200 mm tray geometry reservation only; no heavy instrument handling'),
      maximum_sampled=dict(radial_extent_m=max(s['visual_box_radius_m'] for s in samples)),
      source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [HERE/'SOURCE.json',HERE/'kinematics.json',HERE/'kinematics.py',Path(__file__)]],
      checker_sha256=sha(__file__),load_included=False,dynamic_motion_validated=False,full_spatial_acceptance=False,
      limitations=['129 static authored transit poses sample a restricted arm range; no continuous bound for those arm intervals',
        'Hand sphere uses official chain lengths and mesh boxes, valid for all finger/wrist rotations relative to each sampled wrist origin',
        'Feet and torso remain at zero angles; no gait, bending, stopping, fall, carried load or camera installation is qualified',
        'External camera mounts and cables must be added to the envelope after mechanical selection'])
    (HERE/'space.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(dict(samples=len(samples),radius_m=selected,height_m=record['transit_height_m'],hand_bounds=hand_bounds)))


if __name__=='__main__':build()
