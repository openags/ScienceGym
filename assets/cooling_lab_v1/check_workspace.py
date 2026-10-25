"""Static G1 station access screening, not motion planning or task success.

Solve position-only palm-reference IK under source joint limits. Then reject
poses intersecting conservative room/furniture and other-device boxes. The
target instrument's internal geometry, grasp orientation, balance and routes
to the pose are deliberately not claimed by this screen.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import mujoco
from scipy.optimize import least_squares
import trimesh
from geometry_tools import HERE,ROOT,sha,write_json
from access_geometry import access_obstacles

sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot


def overlap(a,b,tolerance=.002):
    return bool(np.all(np.minimum(a[1],b[1])-np.maximum(a[0],b[0])>tolerance))


def build(target_ids=None, output_path=None):
    scene=json.loads((HERE/'scene.json').read_text());robot=Robot()
    model_path=ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml'
    model=mujoco.MjModel.from_xml_path(str(model_path));data=mujoco.MjData(model)
    assets={a['id']:a for a in scene['assets']};surfaces={s['id']:s for s in scene['support_surfaces']}
    rig_path=ROOT/'assets/g1_sensor_rig_v1/rig.json';rig=json.loads(rig_path.read_text())
    robot_manager=trimesh.collision.CollisionManager();rig_manager=trimesh.collision.CollisionManager();visual_frames={};rig_corners={}
    for name in robot.preview.graph.nodes_geometry:
        bind,key=robot.preview.graph[name];parent=name.rsplit('_visual_',1)[0]
        visual_frames[name]=(parent,np.linalg.inv(robot.bind[parent])@bind)
        robot_manager.add_object(name,robot.preview.geometry[key],bind)
    for a in rig['attachments']:
        assert sha(ROOT/a['geometry_path'])==a['geometry_sha256']
        mesh=trimesh.load(ROOT/a['geometry_path'],force='scene').to_geometry();rig_manager.add_object(a['id'],mesh)
        lo,hi=mesh.bounds;rig_corners[a['id']]=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]])
    rig_by_id={a['id']:a for a in rig['attachments']}
    def body_matrix(name):
        body=data.body(name);t=np.eye(4);t[:3,:3]=body.xmat.reshape(3,3);t[:3,3]=body.xpos;return t
    targets=[]
    for key in ['cary','nicolet','harrick_hrs','spectratech_500','bath','dmm','rtd','smu_white','smu_black','daq','heater','heater_white','cooler_white','cooler_black','cooler_fixed','tracker','hobo_u30','waterjet','caliper','driver','tray_white','tray_black']:
        a=assets[key];bounds=np.array(a['normalized_bounds_m'])+a['position_m'];center=bounds.mean(axis=0)
        surface=surfaces.get(a['station']);front=surface['xy_bounds_m'][1] if surface else bounds[0,1]
        target=[float(center[0]),float(bounds[0,1]-.05),1.05 if key=='waterjet' else float(min(bounds[1,2]+.04,bounds[0,2]+.18))]
        basis='Authored front-envelope access point; not a measured button or grasp frame'
        if key in ['heater','heater_white']:
            target[2]=float(bounds[1,2]+.10)
            basis='Authored palm approach 100 mm above the loose thin heater; reserves hand clearance from the bench. Not a grasp/contact point or a verified pickup'
        targets.append(dict(id=key+'_front',asset=key,station=a['station'],point_m=target,front_y_m=front,
          basis=basis,source=None))
    for key in ['wire_stripper','terminal_driver','tweezers_white','tweezers_black','fill_jug','ambient_rtd',
                'tc_transition_kit','nano_pe_stock','ldpe_stock','mylar_stock','masking_tape','calibration_block_stock','utility_cart','oily_waste_can',
                'fine_cutter','meter_leads_white','meter_leads_black','workholding_kit','deburring_tool',
                'g1_spare_battery','g1_disconnected_charger','coating_white_stock','coating_black_stock','silver_paste_stock',
                'copper_sheet_stock','aluminum_sheet_stock','foam_stock','acrylic_stock','pe_tube_stock','aluminum_tube_stock','lab_jack_white','lab_jack_black','lift_mount_hardware','frame_profile_stock','frame_machining_stock','frame_mount_hardware','cover_angle_stock','cover_mount_hardware','cover_adhesive_stock']:
        a=assets[key];bounds=np.array(a['normalized_bounds_m'])+a['position_m'];surface=surfaces[a['station']]
        reverse=key!='oily_waste_can';point=[float(bounds[:,0].mean()),float(bounds[1,1]+.04 if reverse else bounds[0,1]-.04),float(bounds[1,2]+.04)]
        basis='Authored upper-edge palm approach from the accessible aisle; not a grasp frame'
        if key in ['nano_pe_stock','ldpe_stock','mylar_stock','copper_sheet_stock','aluminum_sheet_stock','foam_stock','acrylic_stock','pe_tube_stock','aluminum_tube_stock','lab_jack_white','lab_jack_black','lift_mount_hardware','frame_profile_stock','frame_machining_stock','frame_mount_hardware','cover_angle_stock','cover_mount_hardware','cover_adhesive_stock']:
            point[2]=float(bounds[1,2]+.10)
            basis='Authored 100 mm upper palm approach above stock, reserving hand clearance from the shelf; gripping, separation and material contact remain unqualified'
        if key=='utility_cart':
            point=(trimesh.transform_points([[.67348,0,.8964]],a['normalization_matrix'])[0]+a['position_m']+[0,0,.04]).tolist()
            basis='Authored 40 mm upper approach to the reconstructed cart handle centre; grip orientation and pushing are unqualified'
        if key=='oily_waste_can':
            point=[float(bounds[:,0].mean()),float(bounds[:,1].mean()),float(bounds[1,2]+.30)]
            basis='Authored release approach 300 mm above the closed-lid envelope; requires later lid opening and controlled disposal. Not rim grasp, pedal actuation or a verified drop'
        source_path=a['sources'] if key in ['lab_jack_white','lab_jack_black','lift_mount_hardware','frame_profile_stock','frame_machining_stock','frame_mount_hardware','cover_angle_stock','cover_mount_hardware','cover_adhesive_stock'] else 'assets/cooling_lab_v1/supplies.json'
        targets.append(dict(id=key+'_access',asset=key,station=a['station'],point_m=point,
            front_y_m=surface['xy_bounds_m'][3 if reverse else 1],approach='rear' if reverse else 'front',
            basis=basis,source=dict(path=source_path,sha256=sha(ROOT/source_path),source_record=a.get('source_record',key),dimensions_inferred=not key.startswith('lab_jack_'))))
    for key,filename in [('cary','assets/cary_5000_v1/interfaces.json'),('nicolet','assets/nicolet_6700_v1/interfaces.json'),('bath','assets/thermo_a25_ac150_v1/interfaces.json')]:
        source=json.loads((ROOT/filename).read_text());a=assets[key];norm=np.array(a['normalization_matrix'])
        for entry in source.get('interfaces',[]):
            point=entry.get('center_m') or entry.get('grasp_center_m')
            if point is None:continue
            axis=np.array(entry.get('axis',[0,1,0]),dtype=float)
            # A stated mechanical hinge axis is not a surface approach normal.
            if entry.get('kind') in ['hinge','slide']:axis=np.array([0,1,0])
            interface_point=trimesh.transform_points([point],norm)[0]+a['position_m']
            offset=-.04*axis
            offset_basis='Authored 40 mm approach offset; not a contact/grasp frame'
            if entry.get('kind')=='keyhole_mount':
                # A mounting datum on a plate 10 mm above the bench cannot be
                # used as a palm center. Keep the datum and reserve an upper
                # approach for fingers; no grasp or insertion is qualified.
                offset=np.array([0,0,.08])
                offset_basis='Authored 80 mm top approach above the keyhole mounting datum, reserved clearance only; finger contact and insertion remain unvalidated'
            point=interface_point+offset
            bounds=surfaces[a['station']]['xy_bounds_m']
            approach='rear' if axis[1]<-.5 else 'front'
            targets.append(dict(id=key+'_'+entry['id'],asset=key,station=a['station'],point_m=point.tolist(),
              front_y_m=bounds[3] if approach=='rear' else bounds[1],approach=approach,
              interface_point_m=interface_point.tolist(),approach_offset_m=offset.tolist(),
              basis=offset_basis+'; palm position only',
              source=dict(path=filename,sha256=sha(ROOT/filename),interface_id=entry['id'],dimensions_inferred=True)))
    if target_ids is not None:
        assert output_path is not None and Path(output_path).resolve()!=(HERE/'workspace_checks.json').resolve(), 'Targeted diagnostics require a separate output path'
        assert set(target_ids)<={t['id'] for t in targets}, 'Unknown target'
        targets=[t for t in targets if t['id'] in target_ids]
    arm_names={side:[side+'_'+name+'_joint' for name in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']] for side in ['left','right']}
    obstacles=access_obstacles(scene)
    asset_boxes={k:np.array(a['normalized_bounds_m'])+a['position_m'] for k,a in assets.items() if k!='g1'}
    results=[]
    rest={side+'_'+joint:angle for side in ['left','right'] for joint,angle in [('shoulder_pitch_joint',.1),('shoulder_roll_joint',.2 if side=='left' else -.2),('elbow_joint',1.6)]}
    for target in targets:
        goal=np.array(target['point_m']);best=None;attempts=0
        reverse=target.get('approach')=='rear';yaw=-np.pi/2 if reverse else np.pi/2
        # First retain the previous centered stance search, then align either
        # shoulder laterally. No instrument dimensions or target points change.
        placements=[(distance,offset) for offset in [0,-.15,.15,-.30,.30] for distance in [.18,.24,.34,.44,.16]]
        for stand_off,lateral_offset in placements:
            for side in ['left','right']:
                base=np.array([goal[0]+lateral_offset,target['front_y_m']+(stand_off if reverse else -stand_off),model.qpos0[2]])
                ids=[model.joint(n).id for n in arm_names[side]];qi=model.jnt_qposadr[ids];vi=model.jnt_dofadr[ids]
                low=model.jnt_range[ids,0];high=model.jnt_range[ids,1];site=model.site(side+'_palm_review').id
                def set_pose(q):
                    data.qpos[:]=model.qpos0;data.qpos[:3]=base;data.qpos[3:7]=[np.cos(yaw/2),0,0,np.sin(yaw/2)]
                    for name,value in rest.items():data.qpos[model.joint(name).qposadr[0]]=value
                    data.qpos[qi]=q
                    mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data)
                def residual(q):set_pose(q);return data.site_xpos[site]-goal
                def jac(q):
                    set_pose(q);jp=np.zeros((3,model.nv));jr=jp.copy();mujoco.mj_jacSite(model,data,jp,jr,site);return jp[:,vi]
                for initial in [np.zeros(7),np.array([-.5,.2 if side=='left' else -.2,0,.5,0,0,0]),np.array([-.3,0,0,.4,1.3 if side=='left' else -1.3,0,0])]:
                    attempts+=1
                    fit=least_squares(residual,np.clip(initial,low+1e-6,high-1e-6),jac=jac,bounds=(low,high),max_nfev=100,gtol=1e-8)
                    error=float(np.linalg.norm(residual(fit.x)));collisions=[];self_contacts=[];rig_contacts=[];clamp_contacts=[];rig_checked=False
                    if error<.01:
                        mujoco.mj_forward(model,data)
                        pair_depths={}
                        for contact in data.contact:
                            bodies=[int(model.geom_bodyid[g]) for g in contact.geom]
                            if contact.dist<-.0005 and all(bodies):
                                pair=tuple(sorted(model.body(b).name for b in bodies))
                                pair_depths[pair]=max(pair_depths.get(pair,0),float(-contact.dist))
                        self_contacts=[dict(links=list(pair),penetration_m=depth) for pair,depth in sorted(pair_depths.items())]
                        for name,corners in robot.corners.items():
                            body=data.body(name);points=corners@body.xmat.reshape(3,3).T+body.xpos
                            bounds=np.array([points.min(axis=0),points.max(axis=0)])
                            for identity,other in obstacles:
                                if identity==target['asset']:continue # Target-device internals are outside this screen for every instrument.
                                if overlap(bounds,other):collisions.append((name,identity))
                            for identity,other in asset_boxes.items():
                                if identity!=target['asset'] and overlap(bounds,other):collisions.append((name,identity))
                        if not collisions and not self_contacts:
                            rig_checked=True
                            for name,(parent,local) in visual_frames.items():robot_manager.set_transform(name,body_matrix(parent)@local)
                            for a in rig['attachments']:
                                t=body_matrix(a['parent_link'])@a['parent_from_geometry'];rig_manager.set_transform(a['id'],t)
                                points=trimesh.transform_points(rig_corners[a['id']],t);bounds=np.array([points.min(axis=0),points.max(axis=0)])
                                for identity,other in obstacles+list(asset_boxes.items()):
                                    if identity==target['asset']:continue
                                    if overlap(bounds,other):collisions.append((a['id'],identity))
                            _,pairs=rig_manager.in_collision_other(robot_manager,return_names=True)
                            for pair in sorted(pairs):
                                identity=next(p for p in pair if p in rig_by_id);other=next(p for p in pair if p!=identity)
                                if other==rig_by_id[identity]['parent_link']+'_visual_0':clamp_contacts.append([identity,other])
                                else:rig_contacts.append([identity,other])
                    row=dict(hand=side,base_position_m=base.tolist(),base_yaw_rad=float(yaw),joint_coordinates={**rest,**dict(zip(arm_names[side],fit.x.tolist()))},
                      position_error_m=error,external_overlaps=[list(p) for p in sorted(set(collisions))],
                      self_contacts_checked=error<.01,self_penetrations_over_0_5mm=self_contacts,
                      candidate_rig_checked=rig_checked,candidate_rig_other_link_intersections=rig_contacts,candidate_rig_parent_contacts_unqualified=clamp_contacts,
                      position_candidate=error<.01 and not collisions and not self_contacts and rig_checked and not rig_contacts and not clamp_contacts)
                    score=(not row['position_candidate'],error>=.01,len(collisions)+len(self_contacts)+len(rig_contacts)+len(clamp_contacts),error)
                    if best is None or score<best[0]:best=(score,row)
                    if row['position_candidate']:break
                if best[1]['position_candidate']:break
            if best[1]['position_candidate']:break
        results.append(dict(**target,attempts=attempts,result=best[1],status='position_candidate_only' if best[1]['position_candidate'] else 'needs_layout_or_access_revision'))
        print(json.dumps(dict(target=target['id'],status=results[-1]['status'],attempts=attempts)),flush=True)
    failures=[r['id'] for r in results if not r['result']['position_candidate']]
    report=dict(schema_version=1,status='static_access_screening_not_task_validation',scene_sha256=sha(HERE/'scene.json'),
      target_selection=dict(mode='selected_diagnostic' if target_ids is not None else 'all',requested_ids=target_ids),
      source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [model_path,ROOT/'assets/unitree_g1_inspire_v1/kinematics.py',rig_path,Path(__file__),HERE/'access_geometry.py']],
      counts=dict(targets=len(results),position_candidates=len(results)-len(failures),needs_revision=len(failures)),targets=results,
      unresolved_target_ids=failures,full_workspace_qualified=False,
      limitations=['Each target is tested separately; simultaneous two-hand coordination and carrying are not tested',
       'Position-only IK is necessary but not sufficient: palm orientation, finger contact, balance, loads, entry trajectory and instrument internals are not checked',
       'Conservative per-link visual mesh boxes screen room/furniture and other instruments; target-instrument internals are excluded and require a later contact review',
       'Open storage racks use separate shelf/upright boxes with staged stock retained; route screening still reserves the full rack envelope',
       'Robot self-contact is screened with the provisional MJCF at a 0.5 mm penetration threshold, including source convex hull approximations; no exact surface or continuous contact qualification',
       'Adapted camera collars and fasteners are screened against every robot link, including the parent wrist, and external boxes. Rigid parent-wrist intersections reject candidates; compliant-liner preload and cable models remain open',
       'Candidate base placements are test coordinates, not a walked path or accepted standing controller',
       'Failure after finite starts is an unresolved access issue, not a proof that no feasible whole-body posture exists'])
    write_json(Path(output_path) if output_path is not None else HERE/'workspace_checks.json',report);print(json.dumps(report['counts']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--targets',nargs='+');parser.add_argument('--output')
    a=parser.parse_args();build(a.targets,a.output)
