"""Static G1/FTP palm-allowance screen against the actual installed station.

Includes both complete hands, proposed wrist cameras, the selected complete
tool and all target geometry. No target instrument is excluded. Separate
candidate poses do not establish grasp orientation, walking, balance, forces,
simultaneous two-hand operation or any executed manipulation.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np
import mujoco
import trimesh
from scipy.optimize import least_squares
from geometry_tools import HERE,ROOT,sha,write_json
from check_weather_assets import load_parts
from access_geometry import access_obstacles
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot


def build(preparation=False):
    robot=Robot();model_path=ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml'
    model=mujoco.MjModel.from_xml_path(str(model_path));data=mujoco.MjData(model)
    names=['weather_station_assets','weather_storage_assets','weather_service_checks','scene']
    if preparation:names+=['weather_preparation_assets','weather_preparation_checks','weather_workspace_posture_candidates']
    r={n:json.loads((HERE/(n+'.json')).read_text()) for n in names};station=r['weather_station_assets'];site=np.asarray(station['station_origin_world_m'])
    rig_path=ROOT/'assets/g1_sensor_rig_v1/rig.json';rig=json.loads(rig_path.read_text())
    environment=trimesh.collision.CollisionManager();bodies=trimesh.collision.CollisionManager();cameras=trimesh.collision.CollisionManager();frames={};camera_meshes={}
    context=r['weather_preparation_assets'] if preparation else station
    if preparation:assert r['weather_preparation_checks']['passed']
    for n,m in load_parts(context['geometry']).items():
        if n.endswith('_text'):continue
        if not preparation:m.apply_translation(-site)
        environment.add_object('station__'+n,m)
    if not preparation:
        for n,m in load_parts(r['weather_storage_assets']['geometry']).items():
            if not n.endswith('_text'):environment.add_object('storage__'+n,m)
    # Other room/furniture geometry stays conservatively occupied. Existing
    # cart/logger instances are replaced only in this alternative inspection.
    obstacles=access_obstacles(r['scene'])
    obstacles += [(a['id'],np.asarray(a['normalized_bounds_m'])+a['position_m']) for a in r['scene']['assets'] if a['id'] not in ['g1','hobo_u30','utility_cart']]
    for n,bounds in obstacles:
        if n in ['g1','hobo_u30','utility_cart']:continue
        bounds=np.asarray(bounds);box=trimesh.creation.box(bounds[1]-bounds[0]);box.apply_translation(bounds.mean(axis=0)-site)
        environment.add_object('lab__'+n,box)
    for n in robot.preview.graph.nodes_geometry:
        bind,key=robot.preview.graph[n];parent=n.rsplit('_visual_',1)[0]
        frames[n]=(parent,np.linalg.inv(robot.bind[parent])@bind);bodies.add_object(n,robot.preview.geometry[key],bind)
    for a in rig['attachments']:
        assert sha(ROOT/a['geometry_path'])==a['geometry_sha256']
        mesh=trimesh.load(ROOT/a['geometry_path'],force='scene').to_geometry();camera_meshes[a['id']]=mesh
        cameras.add_object(a['id'],mesh)
    def body_matrix(name):
        b=data.body(name);t=np.eye(4);t[:3,:3]=b.xmat.reshape(3,3);t[:3,3]=b.xpos;return t
    targets=[]
    for pose in r['weather_service_checks']['tool_poses']:
        t=np.asarray(pose['tool_to_station']);goal=trimesh.transform_points([[.190,0,0]],t)[0]+[0,0,.100]
        targets.append(dict(id='tool_'+pose['id'],point_m=goal.tolist(),outward_xy=t[:2,0].tolist(),tool_pose=pose,
            basis='Authored palm point 100 mm above the handle axis, 190 mm from socket entry. Complete tool remains an obstacle; no grip or tool contact is asserted.'))
    targets.append(dict(id='logger_front',point_m=[0,-.267,1.200],outward_xy=[0,-1],basis='Authored palm allowance 120 mm in front of the closed logger.'))
    for i,z in enumerate([1.1503,1.2453],1):
        targets.append(dict(id='logger_clasp_'+str(i),point_m=[.2043,-.1345,z],outward_xy=[1,0],basis='Authored 120 mm outboard palm allowance from the clasp pivot; no finger-contact or release motion.'))
    for tie in station['retention_ties']:
        if tie['id'] not in ['temperature_coil_upper','wind_coil_upper']:continue
        t=np.asarray(tie['plane_to_station']);outward=t[:3,1];point=trimesh.transform_points([[*tie['head_origin_plane_m'],0]],t)[0]+outward*.100
        targets.append(dict(id=tie['id'],point_m=point.tolist(),outward_xy=outward[:2].tolist(),basis='Authored 100 mm outward palm allowance from the actual upper tie head, along its recorded feed/head plane.'))
    targets.append(dict(id='wind_mount',point_m=[.120,.0255,1.650],outward_xy=[1,0],basis='Authored palm allowance beside the wind mounting block, not a grasp or fastener datum.'))
    storage=r['weather_storage_assets']
    for kind,origin in storage['tray_origins_m'].items():
        targets.append(dict(id=kind+'_tray',point_m=(np.asarray(origin)+[0,0,.150]).tolist(),outward_xy=[0,-1],basis='Authored palm point 100 mm above the catalog tray rim; actual contents and cart remain obstacles.'))
    targets.append(dict(id='cart_handle',point_m=(np.asarray(storage['cart_origin_m'])+[.67348,0,.9964]).tolist(),outward_xy=[1,0],basis='Authored 100 mm upper palm allowance over the existing cart handle; not a grip or push.'))
    if preparation:
        targets=[t for t in targets if t['id'] in ['temperature_coil_upper','wind_coil_upper','wind_mount']]
        stage=np.asarray(context['upper_cluster_to_preparation'])
        for target in targets:
            target['point_m']=trimesh.transform_points([target['point_m']],stage)[0].tolist()
            target['outward_xy']=(stage[:2,:2]@target['outward_xy']).tolist()
            target['basis']+=' Same allowance transformed into the manual-supported low-mast inspection.'
        for tie in context['temporary_ties']:
            matrix=np.asarray(tie['plane_to_preparation']);outward=-matrix[:3,0] if tie['id']=='temporary_brace' else matrix[:3,1]
            point=trimesh.transform_points([[*tie['head_origin_plane_m'],0]],matrix)[0]+outward*.100
            targets.append(dict(id=tie['id'],point_m=point.tolist(),outward_xy=outward[:2].tolist(),basis='Authored 100 mm palm allowance beside the brace head or beyond the leg head. The original axial brace allowance interfered with the uncut tail; that failed witness is retained. This is not a grip.'))
        targets.append(dict(id='free_plug_tray',point_m=(np.asarray(context['tray_origin_m'])+[0,0,.150]).tolist(),outward_xy=[0,-1],basis='Authored palm allowance 100 mm above the ordinary tray rim; restricted nominal standing search, not a grasp or crouching proof.'))
    rest={side+'_'+n:angle for side in ['left','right'] for n,angle in [('shoulder_pitch_joint',.1),('shoulder_roll_joint',.2 if side=='left' else -.2),('elbow_joint',1.6)]}
    postures=[dict(id='nominal_standing',joint_coordinates={},base_height_m=float(model.qpos0[2]))]
    if preparation:
        # These are static asset-space alternatives, not standing or squatting
        # controllers. Opposed hip/ankle pitch preserves the source sole angle;
        # root height is solved from actual foot vertices, not a floor offset.
        for candidate in r['weather_workspace_posture_candidates']['postures']:
            angles={name:candidate[name+'_rad'] for name in ['hip_pitch','knee','ankle_pitch']}
            assert abs(sum(angles.values()))<1e-10
            joints={side+'_'+name+'_joint':value for side in ['left','right'] for name,value in angles.items()}
            joints.update({side+'_'+name+'_joint':value for side in ['left','right'] for name,value in candidate.get('unused_arm_angles',{}).items()})
            data.qpos[:]=model.qpos0
            for n,v in joints.items():
                joint=model.joint(n);assert joint.range[0]<=v<=joint.range[1],(n,v,joint.range.tolist());data.qpos[joint.qposadr[0]]=v
            mujoco.mj_kinematics(model,data)
            floors={}
            for side in ['left','right']:
                n=side+'_ankle_roll_link_visual_0';parent,local=frames[n];matrix=body_matrix(parent)@local
                key=robot.preview.graph[n][1];vertices=robot.preview.geometry[key].vertices
                floors[side]=float(np.min(vertices@matrix[2,:3]+matrix[2,3]))
            assert abs(floors['left']-floors['right'])<1e-7,floors
            postures.append(dict(id=candidate['id'],joint_coordinates=joints,
                base_height_m=float(model.qpos0[2]-min(floors.values())),source_foot_floor_heights_m=floors))
    results=[]
    for target in targets:
        goal=np.asarray(target['point_m'],dtype=float);outward=np.asarray(target['outward_xy'],dtype=float);outward/=np.linalg.norm(outward)
        tool=trimesh.collision.CollisionManager()
        if 'tool_pose' in target:
            p=target['tool_pose']
            for n,m in load_parts(p['tool_geometry']).items():
                if not n.endswith('_text'):tool.add_object(n,m,np.asarray(p['tool_to_station']))
        best=None;attempts=0;found=False
        posture_history=[]
        for posture in postures:
            first_attempt=attempts;posture_best=None
            for angle in [0,-30,30,-60,60,180]:
                a=np.deg2rad(angle);direction=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])@outward
                yaw=math.atan2(-direction[1],-direction[0]);lateral_axis=np.array([-direction[1],direction[0]])
                for distance in [.28,.38,.48,.58]:
                    for lateral in [0,-.15,.15,-.30,.30]:
                        for side in ['left','right']:
                            arm_names=[side+'_'+n+'_joint' for n in ['shoulder_pitch','shoulder_roll','shoulder_yaw','elbow','wrist_roll','wrist_pitch','wrist_yaw']]
                            ids=[model.joint(n).id for n in arm_names];qi=model.jnt_qposadr[ids];vi=model.jnt_dofadr[ids]
                            low=model.jnt_range[ids,0];high=model.jnt_range[ids,1];si=model.site(side+'_palm_review').id
                            base=np.r_[goal[:2]+direction*distance+lateral_axis*lateral,posture['base_height_m']]
                            def set_pose(q):
                                data.qpos[:]=model.qpos0;data.qpos[:3]=base;data.qpos[3:7]=[math.cos(yaw/2),0,0,math.sin(yaw/2)]
                                for n,v in {**rest,**posture['joint_coordinates']}.items():data.qpos[model.joint(n).qposadr[0]]=v
                                data.qpos[qi]=q;mujoco.mj_kinematics(model,data);mujoco.mj_comPos(model,data)
                            def residual(q):set_pose(q);return data.site_xpos[si]-goal
                            def jac(q):
                                set_pose(q);jp=np.zeros((3,model.nv));jr=jp.copy();mujoco.mj_jacSite(model,data,jp,jr,si);return jp[:,vi]
                            for initial in [np.zeros(7),np.array([-.5,.2 if side=='left' else -.2,0,.5,0,0,0]),np.array([-.3,0,0,.4,1.3 if side=='left' else -1.3,0,0])]:
                                attempts+=1;fit=least_squares(residual,np.clip(initial,low+1e-6,high-1e-6),jac=jac,bounds=(low,high),max_nfev=100,gtol=1e-8)
                                error=float(np.linalg.norm(residual(fit.x)));self_hits=[];external=[];tool_hits=[];rig_external=[];rig_robot=[];rig_tool=[];transforms={};rig_transforms={};below_floor=[]
                                if error<.005:
                                    mujoco.mj_forward(model,data)
                                    self_hits=[dict(links=[model.body(int(model.geom_bodyid[g])).name for g in c.geom],depth_m=float(-c.dist)) for c in data.contact if c.dist<-.0005 and all(model.geom_bodyid[g] for g in c.geom)]
                                    for n,(parent,local) in frames.items():
                                        matrix=body_matrix(parent)@local;bodies.set_transform(n,matrix);transforms[n]=matrix.tolist()
                                        vertices=robot.preview.geometry[robot.preview.graph[n][1]].vertices
                                        minimum=float(np.min(vertices@matrix[2,:3]+matrix[2,3]))
                                        if minimum<-.00001:below_floor.append(dict(part=n,minimum_z_m=minimum))
                                    for attachment in rig['attachments']:
                                        matrix=body_matrix(attachment['parent_link'])@attachment['parent_from_geometry'];cameras.set_transform(attachment['id'],matrix);rig_transforms[attachment['id']]=matrix.tolist()
                                        minimum=float(np.min(camera_meshes[attachment['id']].vertices@matrix[2,:3]+matrix[2,3]))
                                        if minimum<-.00001:below_floor.append(dict(part=attachment['id'],minimum_z_m=minimum))
                                    external=sorted(bodies.in_collision_other(environment,return_names=True)[1])
                                    tool_hits=sorted(bodies.in_collision_other(tool,return_names=True)[1]) if 'tool_pose' in target else []
                                    rig_external=sorted(cameras.in_collision_other(environment,return_names=True)[1])
                                    rig_robot=sorted(cameras.in_collision_other(bodies,return_names=True)[1])
                                    rig_tool=sorted(cameras.in_collision_other(tool,return_names=True)[1]) if 'tool_pose' in target else []
                                conflicts=len(below_floor)+len(self_hits)+len(external)+len(tool_hits)+len(rig_external)+len(rig_robot)+len(rig_tool)
                                score=(error>=.005,conflicts,error)
                                row=dict(posture_id=posture['id'],hand=side,base_position_m=base.tolist(),base_yaw_rad=float(yaw),joint_coordinates={**rest,**posture['joint_coordinates'],**dict(zip(arm_names,fit.x.tolist()))},
                                    position_error_m=error,below_ground_surfaces=below_floor,self_penetrations_over_0_5mm=self_hits,exact_robot_environment_intersections=external,exact_robot_tool_intersections=tool_hits,
                                    exact_candidate_rig_environment_intersections=rig_external,exact_candidate_rig_robot_intersections=rig_robot,exact_candidate_rig_tool_intersections=rig_tool,
                                    full_geometry_checked=error<.005,position_candidate=error<.005 and conflicts==0,visual_transforms=transforms,rig_transforms=rig_transforms)
                                if best is None or score<best[0]:best=(score,row)
                                if posture_best is None or score<posture_best[0]:posture_best=(score,row)
                                if row['position_candidate']:found=True;break
                            if found:break
                        if found:break
                    if found:break
                if found:break
            posture_history.append(dict(posture=posture,attempts=attempts-first_attempt,
                position_candidate=found,best_result={k:v for k,v in posture_best[1].items() if k not in ['visual_transforms','rig_transforms']}))
            if found:break
        results.append(dict(**target,attempts=attempts,posture_searches=posture_history,result=best[1],status='position_candidate_only' if found else 'needs_access_revision'))
        print(json.dumps(dict(target=target['id'],found=found,attempts=attempts,best_error_m=best[1]['position_error_m'])),flush=True)
    unresolved=[x['id'] for x in results if not x['result']['position_candidate']]
    refs=[Path(__file__),HERE/'check_weather_assets.py',HERE/'access_geometry.py',model_path,ROOT/'assets/unitree_g1_inspire_v1/kinematics.py',ROOT/'assets/unitree_g1_inspire_v1/SOURCE.json',ROOT/'assets/unitree_g1_inspire_v1/VERIFICATION.json',rig_path]+[HERE/(n+'.json') for n in names]
    geometry=ROOT/'assets/unitree_g1_inspire_v1/geometry/g1_inspire_ftp_zero.glb'
    record=dict(schema_version=1,status='static_position_allowance_screen_not_manipulation',source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in refs],
        robot_geometry=dict(path=str(geometry.relative_to(ROOT)),sha256=sha(geometry),parts=len(frames)),station_origin_world_m=site.tolist(),targets=results,
        inspection_context='partial_low_mast' if preparation else 'installed_station',context_geometry=context['geometry'],
        counts=dict(targets=len(results),position_candidates=len(results)-len(unresolved),needs_revision=len(unresolved)),unresolved_target_ids=unresolved,
        scope=('All geometry in the explicitly partial low-mast context is retained. ' if preparation else 'All actual station/tool/cart geometry is retained. ')+ 'Exact triangle intersections include the complete humanoid and proposed wrist attachments; other lab objects use conservative boxes. Independently solved palm-position allowances, not grasp poses, assembly plans or executed actions.',
        limitations=['Palm orientation, finger contact, two-hand coordination, payload, balance, friction, dynamic stability and entry paths are unqualified.',
            'Self-contact uses provisional MJCF geometry with a 0.5 mm threshold; external intersections use source visual triangles.',
            'Zero-angle fingers and finite standing/crouched posture alternatives are restricted static inspections. Actual source foot vertices set crouch height; no balance, support force or transition controller is qualified.',
            'Candidate wrist camera brackets remain unaccepted; including their geometry does not qualify attachment or sensing.',
            'A failed finite search is an unresolved access issue, not a proof that no feasible whole-body posture exists.'],
        full_workspace_qualified=False,robot_use_qualified=False,owner_acceptance=None)
    output='weather_preparation_workspace_checks.json' if preparation else 'weather_workspace_checks.json'
    write_json(HERE/output,record);print(json.dumps(record['counts']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preparation',action='store_true');args=parser.parse_args();build(args.preparation)
