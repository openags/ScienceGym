"""Source-constrained sensor assembly for review, not calibrated installation."""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/unitree_g1_inspire_v1'))
from kinematics import Robot
from audit import sha


def matrix(rotation=None,position=None):
    t=np.eye(4)
    if rotation is not None:t[:3,:3]=rotation
    if position is not None:t[:3,3]=position
    return t


def build():
    robot=Robot();source=json.loads((HERE/'SOURCE.json').read_text())
    source_geometry=json.loads((HERE/'mount_geometry.json').read_text())
    adapter=json.loads((HERE/'adapter.json').read_text())
    for rec in adapter['source_artifacts']:assert sha(ROOT/rec['path'])==rec['sha256']
    assert source_geometry['source_sha256']==sha(HERE/'SOURCE.json')
    meshes={}
    for item in source_geometry['items']:
        path=HERE/item['geometry']['path'];assert sha(path)==item['geometry']['sha256']
        meshes[item['id']]=trimesh.load(path,force='mesh')
    camera_path=ROOT/'assets/realsense_cameras_v1/geometry/d405.glb'
    camera_scene=trimesh.load(camera_path,force='scene')
    attachments=[];optics=[];assembly=trimesh.Scene();camera_fits=[]
    # Ring seating coordinates are authored from the source flange geometry,
    # not a calibrated Unitree or Inspire installation transform.
    for side in ['left','right']:
        left=side=='left';key='right_wrist_D405_camera_mount' if left else 'wrist_ring_mount'
        item=next(i for i in source_geometry['items'] if i['id']==key)
        center=np.array([0.,0.,-.020 if left else .020])
        r=np.array([[0,0,-1],[0,1,0],[1,0,0]]) if left else np.array([[0,0,1],[0,-1,0],[1,0,0]])
        mount=matrix(r,np.array([source['authored_mount_candidate']['ring_center_wrist_x_m'],0,0])-r@center)
        mount=trimesh.transformations.rotation_matrix(np.radians(source['authored_mount_candidate']['clocking_deg'][side]),[1,0,0])@mount
        clamp=matrix(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0])[:3,:3])
        clamp[:3,3]=center-clamp[:3,:3]@np.array([0,.11800023853648482,0])
        # Two 3.5 mm bores (20 mm pitch) and the camera-side backplate plane
        # constrain the D405 rear M3 mounting holes in the source mesh.
        bores=[c for c in item['cylindrical_faces'] if abs(c['radius_m']-.00175)<1e-8 and c['axis_origin_m'][1]>.08]
        bores=list({tuple(np.round(c['axis_origin_m'],10)):c for c in bores}.values())
        assert len(bores)==2
        p=np.array([c['axis_origin_m'] for c in bores]);p=p[np.argsort(p[:,1])[::-1]]
        normal=np.array(bores[0]['axis']);normal*=1 if normal[1]<0 else -1
        planes=[f for f in item['planar_faces'] if abs(np.dot(f['normal'],normal))>.999 and f['area_m2']>.001]
        plane=max(planes,key=lambda f:np.dot(normal,f['origin_m']))
        d=np.dot(normal,plane['origin_m']);mid=p.mean(axis=0);rear_center=mid+normal*(d-np.dot(normal,mid))
        x=(p[1]-p[0]);x-=normal*np.dot(normal,x);pitch=float(np.linalg.norm(x));x/=pitch
        if left:x=-x # Keep image up toward the robot's local wrist +Z.
        y=-normal;z=np.cross(x,y);rotation=np.column_stack([x,y,z])
        camera=matrix(rotation,rear_center-rotation@np.array([0,.023,0]))
        assert abs(pitch-.020)<1e-8 and abs(np.linalg.det(rotation)-1)<1e-8
        camera_fits.append(dict(side=side,back_hole_pitch_m=pitch,rear_plane_normal=normal.tolist(),rear_plane_d_m=float(d),rear_center_in_step_m=rear_center.tolist(),step_from_camera_geometry=camera.tolist(),step_bore_axis_origins_m=p.tolist(),method='STEP cylindrical bore axes and inner backplate plane; manufacturer D405 rear holes at (+/-10,23,0) mm in converted mesh frame',camera_roll_choice='Authored upright image; not a vendor assembly instruction'))
        parent=side+'_wrist_yaw_link'
        for suffix,key2,t in [('bracket',key,mount),('clamp','left_wrist_D405_camera_mount',mount@clamp)]:
            mesh=meshes[key2].copy();mesh.visual=trimesh.visual.TextureVisuals(material=PBRMaterial(name='printed_polymer_inferred',baseColorFactor=[.045,.05,.055,1],roughnessFactor=.72))
            filename='geometry/'+side+'_'+suffix+'.glb';sc=trimesh.Scene();sc.add_geometry(mesh,node_name=side+'_'+suffix);(HERE/filename).write_bytes(sc.export(file_type='glb'))
            # Keep the unmodified source GLBs for the rejected historical
            # assembly. Both new collar halves share the bracket STEP frame.
            item2=next(v for v in adapter['items'] if v['id']==side+'_'+suffix)
            mesh=trimesh.load(ROOT/item2['geometry']['path'],force='mesh')
            assert sha(ROOT/item2['geometry']['path'])==item2['geometry']['sha256']
            mesh.visual=trimesh.visual.TextureVisuals(material=PBRMaterial(name='authored_pa12',baseColorFactor=[.065,.07,.075,1],roughnessFactor=.72))
            sc=trimesh.Scene();sc.add_geometry(mesh,node_name=side+'_'+suffix)
            hardware=[]
            def add_hardware(name,kind,rotation,position):
                rec=adapter['hardware'][kind];assert sha(ROOT/rec['path'])==rec['sha256']
                hm=trimesh.load(ROOT/rec['path'],force='mesh')
                hm.visual=trimesh.visual.TextureVisuals(material=PBRMaterial(name='stainless_hardware',baseColorFactor=[.42,.45,.49,1],metallicFactor=.9,roughnessFactor=.3))
                local=matrix(rotation,position);sc.add_geometry(hm,node_name=name,transform=local)
                hardware.append(dict(id=name,kind=kind,step_from_hardware=local.tolist(),mass_kg=rec['mass_kg']))
            if suffix=='bracket':
                for j,point in enumerate(trimesh.transform_points([[-.01,.023,0],[.01,.023,0]],camera)):
                    add_hardware(side+'_camera_screw_'+str(j),'m3x6',trimesh.geometry.align_vectors([0,0,1],normal)[:3,:3],point-normal*.003)
            else:
                axis=trimesh.geometry.align_vectors([0,0,1],[0,1,0])[:3,:3]
                for j,xbolt in enumerate([-.04,.04]):
                    for kind,ypos in [('m3x20',-.0075),('washer_m3',-.0075),('washer_m3',.007),('nut_m3',.0075)]:
                        add_hardware(side+'_'+str(j)+'_'+kind+'_'+str(ypos),kind,axis,[xbolt,ypos,center[2]])
            filename='geometry/adapted_'+side+'_'+suffix+'.glb';(HERE/filename).write_bytes(sc.export(file_type='glb'))
            attachments.append(dict(id=side+'_'+suffix,parent_link=parent,geometry_path=str((HERE/filename).relative_to(ROOT)),geometry_sha256=sha(HERE/filename),parent_from_geometry=mount.tolist(),source_role='authored_G1_collar_derivative',source_step=item2['source']['path'],hardware=hardware))
            for node in sc.graph.nodes_geometry:
                local,geom=sc.graph[node];assembly.add_geometry(sc.geometry[geom],node_name=node,transform=robot.bind[parent]@mount@local)
        t=mount@camera
        attachments.append(dict(id=side+'_d405',parent_link=parent,geometry_path=str(camera_path.relative_to(ROOT)),geometry_sha256=sha(camera_path),parent_from_geometry=t.tolist(),source_role='manufacturer_camera',source_step=None))
        for node in camera_scene.graph.nodes_geometry:
            transform,geom=camera_scene.graph[node];assembly.add_geometry(camera_scene.geometry[geom],node_name=side+'_d405_'+node,transform=robot.bind[parent]@t@transform)
        # Exact nominal ROS-to-optical convention: +Z forward, +X image right,
        # +Y image down. D405 color shares the left depth imager frame.
        optical=matrix()
        optical[:3,:3]=np.array([[-1,0,0],[0,0,-1],[0,-1,0]])
        optical[:3,3]=[.009,.0038,0]
        optics.append(dict(id=side+'_wrist_rgb',label=('左' if left else '右')+'腕 D405 RGB',parent_link=parent,parent_from_optical=(t@optical).tolist(),frame_basis='Source D405 xacro nominal color/depth link and optical rotation; source-constrained authored mount transform',profile=dict(width=1280,height=720,horizontal_fov_deg=84,vertical_fov_deg=58,near_m=.01,far_m=8),channels=['RGB'],calibrated=False))
    optical=matrix(trimesh.transformations.euler_matrix(-np.pi/2,0,-np.pi/2)[:3,:3])
    optics.insert(0,dict(id='head_depth',label='G1 原生 D435i 深度',parent_link='d435_link',parent_from_optical=optical.tolist(),frame_basis='Official G1 d435_link, interpreted as ROS camera link; source nominal optical rotation. Link-to-physical-imager alignment uncalibrated.',profile=dict(width=1280,height=720,horizontal_fov_deg=87,vertical_fov_deg=58,near_m=.05,far_m=10),channels=['depth'],calibrated=False))
    color=optical.copy();color[1,3]=.015
    optics.insert(0,dict(id='head_rgb',label='G1 原生 D435i RGB',parent_link='d435_link',parent_from_optical=color.tolist(),frame_basis='Official G1 d435_link and nominal D435 color offset +15 mm ROS Y; not calibrated factory extrinsics.',profile=dict(width=1280,height=720,horizontal_fov_deg=69,vertical_fov_deg=42,near_m=.01,far_m=50),channels=['RGB'],calibrated=False))
    # Both horizontal and vertical catalogue FOV are approximate. Use an
    # off-axis matrix with independent fx/fy instead of silently cropping.
    for o in optics:
        p=o['profile'];p['fx_px']=p['width']/(2*np.tan(np.radians(p['horizontal_fov_deg'])/2));p['fy_px']=p['height']/(2*np.tan(np.radians(p['vertical_fov_deg'])/2));p['cx_px']=p['width']/2;p['cy_px']=p['height']/2
        p['basis']='Nominal manufacturer HD FOV; ideal pinhole preview, no measured intrinsics or distortion'
    path=HERE/'geometry/assembly_zero.glb';path.write_bytes(assembly.export(file_type='glb'))
    evidence=[HERE/'SOURCE.json',HERE/'mount_geometry.json',HERE/'convert_mounts.py',HERE/'adapter.json',Path(__file__),ROOT/'assets/realsense_cameras_v1/model.json',ROOT/'assets/unitree_g1_inspire_v1/kinematics.json']
    report=dict(schema_version=1,status='adapted_collar_candidate_pending_liner_and_cable_qualification',source_artifacts=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in evidence],attachments=attachments,optics=optics,camera_mount_fits=camera_fits,geometry=dict(path=str(path.relative_to(ROOT)),sha256=sha(path)),
      mechanical_compatibility_qualified=False,sensor_runtime_qualified=False,owner_acceptance=None,
      assumptions=['Wrist ring center at +36.5 mm in source wrist_yaw_link, clocked +90 degrees left / -90 degrees right. New 31.2 mm bore collar retains the source camera arm; original parts are archived and no robot or camera geometry is rescaled.',
      'The official D405 wrist installation reference uses Dex3 M4010; its applicability to Inspire FTP is independently screened, not assumed.',
      'The native camera housing is already part of the official G1 head mesh; no duplicate D435 housing is added.',
      'D455 remains an optional staged reference; the head review now uses the native G1 D435i.',
      'Standard M3 screw/nut/washer envelopes and stack lengths are modeled. Liner preload, stiffness, cable retention and dynamic strain remain unqualified.',
      'Nominal camera matrices render inspection views only; noise, distortion, exposure, synchronization, rolling shutter and actor process isolation are absent.'])
    (HERE/'rig.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(attachments=len(attachments),optical_views=len(optics),qualified=False)))

if __name__=='__main__':build()
