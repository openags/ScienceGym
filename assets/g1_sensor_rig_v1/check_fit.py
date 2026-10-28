"""Screen source triangle surfaces and report rejected attachment candidates.

FCL triangle intersections are not reliable volumetric penetration distances.
Retain their identities, never report their contact.depth as physical clearance.
"""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
import mujoco
import fcl

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot
from audit import sha
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from access_geometry import access_obstacles


def build():
    robot=Robot();rig=json.loads((HERE/'rig.json').read_text());checks=[]
    def check(name,value,**extra):
        checks.append(dict(name=name,passed=bool(value),**extra))
        if not value:raise AssertionError(name)
    for rec in rig['source_artifacts']:check('source_'+rec['path'],sha(ROOT/rec['path'])==rec['sha256'])
    attachments={a['id']:trimesh.load(ROOT/a['geometry_path'],force='scene').to_geometry() for a in rig['attachments']}
    for a in rig['attachments']:check('mesh_'+a['id'],sha(ROOT/a['geometry_path'])==a['geometry_sha256'])
    for item in json.loads((HERE/'mount_geometry.json').read_text())['items']:
        g=item['geometry'];check('solid_tessellation_'+item['id'],g['watertight'] and abs(g['mesh_volume_m3']/g['step_volume_m3']-1)<.001)
    for camera in rig['optics']:
        t=np.array(camera['parent_from_optical']);check('rigid_optical_'+camera['id'],np.allclose(t[3],[0,0,0,1]) and np.allclose(t[:3,:3].T@t[:3,:3],np.eye(3)) and np.isclose(np.linalg.det(t[:3,:3]),1))
    for fit in rig['camera_mount_fits']:
        t=np.array(fit['step_from_camera_geometry']);p=trimesh.transform_points([[-.01,.023,0],[.01,.023,0]],t)
        n=np.array(fit['rear_plane_normal']);axes=np.array(fit['step_bore_axis_origins_m']);delta=p[:,None,:]-axes[None,:,:];perpendicular=delta-np.einsum('ijk,k->ij',delta,n)[:,:,None]*n;axis_error=float(np.linalg.norm(perpendicular,axis=2).min(axis=1).max());check('camera_rear_bolt_axis_'+fit['side'],axis_error<1e-8,maximum_axis_error_m=axis_error)
        check('camera_rear_bolt_fit_'+fit['side'],np.allclose(p@n,fit['rear_plane_d_m'],atol=1e-9) and abs(np.linalg.norm(p[1]-p[0])-.02)<1e-9)
    manager=trimesh.collision.CollisionManager()
    for node in robot.preview.graph.nodes_geometry:
        t,key=robot.preview.graph[node];manager.add_object(node,robot.preview.geometry[key],t)
    records=[]
    for fraction in [0,.5,1]:
        world=robot.fk({name:fraction*q for name,q in robot.inspection().items()})
        for node in robot.preview.graph.nodes_geometry:
            parent=node.rsplit('_visual_',1)[0];bind,_=robot.preview.graph[node]
            manager.set_transform(node,world[parent]@np.linalg.inv(robot.bind[parent])@bind)
        for a in rig['attachments']:
            t=world[a['parent_link']]@np.array(a['parent_from_geometry'])
            hit,names=manager.in_collision_single(attachments[a['id']],t,return_names=True)
            other=[name for name in sorted(names) if name!=a['parent_link']+'_visual_0']
            records.append(dict(finger_inspection_fraction=fraction,attachment=a['id'],surface_intersections=sorted(names),other_link_intersections=other,candidate_clear=not hit))
    check('adapted_collar_has_no_robot_surface_intersections',not any(r['surface_intersections'] for r in records))
    check('revised_clocking_avoids_other_links_at_sampled_finger_poses',not any(r['other_link_intersections'] for r in records))
    fixture_path=HERE/'failed_mount_fixture.json';fixture=json.loads(fixture_path.read_text())
    old=next(a for a in fixture['attachments'] if a['id']=='left_bracket')
    original=trimesh.load(ROOT/old['geometry_path'],force='scene').to_geometry()
    _,bad_links=manager.in_collision_single(original,robot.bind[old['parent_link']]@old['parent_from_geometry'],return_names=True)
    check('reject_observed_side_mount_collision',fixture['expected_conflicting_link'] in bad_links)
    current=next(a for a in rig['attachments'] if a['id']=='left_bracket')
    _,old_contacts=manager.in_collision_single(original,robot.bind[current['parent_link']]@current['parent_from_geometry'],return_names=True)
    check('reject_original_undersized_collar',current['parent_link']+'_visual_0' in old_contacts)
    adapter=json.loads((HERE/'adapter.json').read_text());clearances=[];assembly_paths=[]
    # Clip the exact wrist triangle mesh to the collar's axial band. On each
    # clipped triangle the radial norm is convex: the maximum occurs at a
    # vertex. This gives a bound over the whole tessellated band, not a sample
    # of a few points. It remains a bound on this source mesh, not a tolerance
    # certificate for real hardware.
    for side in ['left','right']:
        parent=side+'_wrist_yaw_link';bind,key=robot.preview.graph[parent+'_visual_0']
        mesh=robot.preview.geometry[key].copy();mesh.apply_transform(np.linalg.inv(robot.bind[parent])@bind)
        band=mesh.slice_plane([.0315,0,0],[1,0,0]).slice_plane([.0415,0,0],[-1,0,0])
        radius=float(np.linalg.norm(band.vertices[:,1:],axis=1).max());clearance=adapter['design']['bore_radius_m']-radius
        check('positive_collar_radial_clearance_'+side,clearance>.00065,radial_clearance_m=clearance)
        clearances.append(dict(side=side,source_wrist_radial_bound_m=radius,rigid_bore_radial_clearance_m=clearance,liner_preload_qualified=False))
        for suffix,sign in [('bracket',1),('clamp',-1)]:
            a=next(a for a in rig['attachments'] if a['id']==side+'_'+suffix)
            # Inspect an unfastened assembly path. Screws and washers are
            # inserted separately; their full contact trajectories are pending.
            part=next(p for p in adapter['items'] if p['id']==a['id'])
            m=trimesh.load(ROOT/part['geometry']['path'],force='mesh');hits=[]
            for delta in np.linspace(0,.08,33):
                t=np.array(a['parent_from_geometry']);t[:3,3]+=t[:3,:3]@np.array([0,sign*delta,0])
                _,names=manager.in_collision_single(m,robot.bind[parent]@t,return_names=True)
                if names:hits.append(dict(offset_m=float(delta),links=sorted(names)))
            assembly_paths.append(dict(part=a['id'],sample_count=33,translation_step_m=.0025,collisions=hits))
    check('unfastened_collar_removal_paths',not any(p['collisions'] for p in assembly_paths))
    # Independently derive camera screw tips in the camera's own geometry frame.
    engagement=[]
    for side in ['left','right']:
        bracket=next(a for a in rig['attachments'] if a['id']==side+'_bracket')
        cam=next(a for a in rig['attachments'] if a['id']==side+'_d405')
        for h in bracket['hardware']:
            t=np.linalg.inv(cam['parent_from_geometry'])@bracket['parent_from_geometry']@np.array(h['step_from_hardware'])
            tip=trimesh.transform_points([[0,0,.006]],t)[0];depth=.023-tip[1]
            check('camera_fastener_'+h['id'],abs(abs(tip[0])-.01)<1e-8 and abs(tip[2])<1e-8 and 0<depth<=.004)
            engagement.append(dict(id=h['id'],engagement_m=float(depth),maximum_insertion_m=.004))
    # Positive fault control: a D405 moved into the source wrist is rejected.
    wrong=robot.bind['left_wrist_yaw_link'].copy();wrong[:3,3]+=wrong[:3,:3]@np.array([.025,-.01,0])
    check('reject_camera_inside_wrist',manager.in_collision_single(attachments['left_d405'],wrong))
    # Native imager transform agrees with independently compiled source MJCF.
    model=mujoco.MjModel.from_xml_path(str(ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml'));data=mujoco.MjData(model);mujoco.mj_kinematics(model,data)
    body=data.body('d435_link');check('native_camera_source_frame',np.allclose(body.xpos,robot.bind['d435_link'][:3,3]) and np.allclose(body.xmat.reshape(3,3),robot.bind['d435_link'][:3,:3]))
    workspace_path=ROOT/'assets/cooling_lab_v1/workspace_checks.json';workspace=json.loads(workspace_path.read_text());scene_path=ROOT/'assets/cooling_lab_v1/scene.json';scene=json.loads(scene_path.read_text())
    obstacles=access_obstacles(scene)
    obstacles += [(a['id'],np.array(a['normalized_bounds_m'])+a['position_m']) for a in scene['assets'] if a['id']!='g1']
    rows=[]
    # Optional candidate attachments are not covered by bare-robot reach counts.
    for target in workspace['targets']:
        q=target['result'];world=robot.fk(q['joint_coordinates']);root=trimesh.transformations.rotation_matrix(q['base_yaw_rad'],[0,0,1]);root[:3,3]=np.array(q['base_position_m'])-root[:3,:3]@robot.root_matrix[:3,3]
        for node in robot.preview.graph.nodes_geometry:
            parent=node.rsplit('_visual_',1)[0];bind,_=robot.preview.graph[node]
            manager.set_transform(node,world[parent]@np.linalg.inv(robot.bind[parent])@bind)
        overlaps=[];body_intersections=[];parent_intersections=[]
        for a in rig['attachments']:
            m=attachments[a['id']];lo,hi=m.bounds;corners=np.array([[x,y,z] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);p=trimesh.transform_points(corners,root@world[a['parent_link']]@a['parent_from_geometry']);bounds=np.array([p.min(axis=0),p.max(axis=0)])
            _,names=manager.in_collision_single(m,world[a['parent_link']]@a['parent_from_geometry'],return_names=True)
            body_intersections.extend([[a['id'],name] for name in sorted(names) if name!=a['parent_link']+'_visual_0'])
            parent_intersections.extend([[a['id'],name] for name in sorted(names) if name==a['parent_link']+'_visual_0'])
            for name,b in obstacles:
                if name==target['asset']:continue
                if np.all(np.minimum(bounds[1],b[1])-np.maximum(bounds[0],b[0])>.002):overlaps.append([a['id'],name])
        rows.append(dict(target=target['id'],external_box_overlaps=overlaps,other_robot_link_intersections=body_intersections,parent_wrist_intersections=parent_intersections,parent_wrist_liner_preload_unqualified=True))
    check('station_candidate_attachments_clear_of_other_links',not any(r['other_robot_link_intersections'] or r['external_box_overlaps'] for r in rows if next(t['result']['position_candidate'] for t in workspace['targets'] if t['id']==r['target'])))
    check('station_candidate_rigid_collars_clear_of_parent_wrist',not any(r['parent_wrist_intersections'] for r in rows if next(t['result']['position_candidate'] for t in workspace['targets'] if t['id']==r['target'])))
    out=dict(schema_version=1,status='adapted_collar_geometry_clear_liner_and_cable_pending',checks=checks,checks_passed=all(c['passed'] for c in checks),
      method=f'FCL exact tessellated source triangle intersection at three finger configurations and {len(rows)} arm postures; external conservative boxes at all recorded access poses',fcl_version=fcl.__version__,
      rig_sha256=sha(HERE/'rig.json'),source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [Path(__file__),fixture_path,HERE/'clocking_checks.json',workspace_path,scene_path,ROOT/'assets/cooling_lab_v1/access_geometry.py',ROOT/'assets/unitree_g1_inspire_v1/simulation/robot.xml']],
      static_surface_checks=records,collar_clearances=clearances,unfastened_collar_paths=assembly_paths,camera_screw_engagement=engagement,workspace_attachment_screen=rows,counts=dict(surface_checks=len(records),surface_checks_with_intersections=sum(not r['candidate_clear'] for r in records),workspace_poses=len(rows),workspace_poses_with_attachment_overlaps=sum(bool(r['external_box_overlaps']) for r in rows),workspace_poses_with_other_link_intersections=sum(bool(r['other_robot_link_intersections']) for r in rows)),
      mechanical_compatibility_qualified=False,active_installation=False,blocks=['Authored split collars remove rigid wrist interference. Positive clearance reserves a compliant liner; its preload and retention are not qualified.','Fastener envelopes and camera insertion depth are checked. Cable/connector clearance, strain relief, fastener insertion and dynamic swept volumes remain open.'],
      limitations=['Surface intersection includes intended clamp contact and touching; no penetration-depth or preload qualification is inferred.','Triangle intersection alone can miss full containment; this is an installation rejection screen, never proof of safe assembly.','The target instrument interior is excluded consistently with the bare-robot reach screen.','No motion, optical calibration or actor observation-stream qualification.'])
    (HERE/'fit_checks.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(checks=len(checks),passed=out['checks_passed'],installation_accepted=False,**out['counts'])))

if __name__=='__main__':build()
