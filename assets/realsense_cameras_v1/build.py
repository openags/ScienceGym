"""Convert pinned manufacturer meshes to SI/Z-up; do not invent an installation."""
import json
from pathlib import Path
import sys
import numpy as np
import trimesh
from trimesh.visual.material import PBRMaterial

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'assets/cooling_lab_v1'))
from geometry_tools import Geometry,sha,write_json


def linear_color(rgb):
    c=np.asarray(rgb,dtype=float)/255
    return np.r_[np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4),1.]


def build():
    sources=json.loads((HERE/'sources.json').read_text())
    for item in sources['vendor_files']:
        if sha(HERE/item['path'])!=item['sha256']:raise ValueError('Changed manufacturer input: '+item['path'])
    (HERE/'geometry').mkdir(exist_ok=True)
    records=[]
    for key in ['d455','d405']:
        mesh=trimesh.load(HERE/'vendor'/f'{key}.stl',force='mesh')
        c=mesh.triangles_center
        # Source vertices and faces are retained. Colour boundaries are authored
        # from inspected product photographs, not material assignments from CAD.
        if key=='d455':
            capsule=np.maximum(np.abs(c[:,0])-47.5,0)**2+c[:,1]**2<11.8**2
            front=(c[:,2]>-.8)&capsule
            lenses=np.min([(c[:,0]-x)**2+c[:,1]**2 for x in [-47.5,-10,11.5,47.5]],axis=0)<5.5**2
        else:
            inset=np.maximum(np.abs(c[:,:2])-15,0)
            front=(c[:,2]>-.8)&(np.sum(inset**2,axis=1)<4.7**2)
            lenses=np.minimum((c[:,0]-9)**2+c[:,1]**2,(c[:,0]+9)**2+c[:,1]**2)<4.6**2
        lens_region=lenses&(c[:,2]>-8)
        masks={'shell':~(front|lens_region),'front_panel':front&~lens_region,'optical_recesses':lens_region}
        colors={'shell':([172,177,183],.75,.30),'front_panel':([20,23,26],.12,.20),'optical_recesses':([34,39,45],.15,.16)}
        rotation=trimesh.transformations.rotation_matrix(np.pi/2,[1,0,0])
        conversion=rotation@np.diag([.001,.001,.001,1.])
        scene=trimesh.Scene();parts=[]
        for name,mask in masks.items():
            if not mask.any():continue
            part=mesh.submesh([np.flatnonzero(mask)],append=True,repair=False)
            part.apply_transform(conversion)
            rgb,metal,rough=colors[name]
            part.visual=trimesh.visual.TextureVisuals(material=PBRMaterial(name=name,baseColorFactor=linear_color(rgb),metallicFactor=metal,roughnessFactor=rough))
            scene.add_geometry(part,node_name=name,geom_name=name)
            parts.append(dict(id=name,face_count=len(part.faces),provenance='manufacturer_mesh'))
        # Manufacturer STLs omit optical appearance (D405) or contain overlapping
        # front surfaces (D455). Add explicitly authored appearance-only surfaces
        # in a separate layer; retain all source mechanical geometry underneath.
        visual=Geometry();wide,tall,radius=(.118,.023,.0115) if key=='d455' else (.039,.039,.005)
        visual.rounded_panel('appearance_front_glass',wide,tall,.00002,[0,-.00002,0],radius,[15,17,20],'inferred_visual_overlay')
        positions=[-.0475,-.010,.0115,.0475] if key=='d455' else [-.009,.009]
        for i,x in enumerate(positions):
            visual.ring('appearance_lens_ring_'+str(i),.0028,.0047,.00001,[x,-.00004,0],[42,44,48],axis=(0,-1,0),role='inferred_visual_overlay')
            visual.ring('appearance_inner_ring_'+str(i),.0023,.0031,.00001,[x,-.00005,0],[22,25,31],axis=(0,-1,0),role='inferred_visual_overlay')
            visual.cylinder('appearance_lens_glass_'+str(i),.0023,.00001,[x,-.00006,0],[25,33,43],axis=(0,-1,0),role='inferred_visual_overlay',metal=.4)
        for node in visual.scene.graph.nodes_geometry:
            matrix,name=visual.scene.graph[node];part=visual.scene.geometry[name].copy();part.apply_transform(matrix)
            part.visual.material.baseColorFactor=linear_color(part.visual.material.baseColorFactor[:3])
            part.visual.material.roughnessFactor=.20
            scene.add_geometry(part,node_name=node,geom_name=node)
            parts.append(dict(id=node,face_count=len(part.faces),provenance='authored_appearance_overlay'))
        path=HERE/'geometry'/f'{key}.glb';path.write_bytes(scene.export(file_type='glb'))
        records.append(dict(id=key,manufacturer='RealSense',model=key.upper(),
            geometry=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),bounds_m=scene.bounds.tolist(),parts=parts),
            manufacturer_mesh=dict(path=f'vendor/{key}.stl',sha256=sha(HERE/'vendor'/f'{key}.stl'),triangle_count=len(mesh.faces),watertight=bool(mesh.is_watertight)),
            unit_and_axis_conversion=conversion.tolist(),geometric_rescaling=False,
            geometry_scope='Original manufacturer STL mechanically unchanged; SI unit conversion and rigid orientation only. Separately named appearance overlays add inferred front glass and optical rings.',
            appearance_scope='Author-assigned materials and shallow appearance overlays from product photos and documented optical spacing. Lens diameters, panel inset and 65 micrometre overlay relief are inferred; not optical or collision geometry.',
            installation=dict(status='unmounted_review_candidate',robot_frame=None,extrinsic_matrix=None,mount_geometry=None,cable_route=None),
            observations=dict(enabled=False,intrinsics=None,distortion=None,noise_model=None,timestamp_sync=None),
            dynamics_qualified=False,appearance_accepted=False))
    out=dict(schema_version=1,status='manufacturer_mesh_candidates_not_installed',
        builder_sha256=sha(__file__),source_ledger_sha256=sha(HERE/'sources.json'),items=records,
        selected_roles=[dict(resource_id='robot:HEAD_RGBD',model='native_g1_d435i',channels=['RGB','depth']),
                        dict(resource_id='robot:WRIST_RGB_LEFT',model='d405',channels=['RGB']),
                        dict(resource_id='robot:WRIST_RGB_RIGHT',model='d405',channels=['RGB'])],
        selection_basis='Authored camera selection under the owner-approved head RGB-D / wrist RGB plan; native G1 D435i head camera; D455 is an optional staged reference.',
        limitations=['Three independent USB links, mechanical mounting, strain relief and full-arm cable clearance remain unmodeled.',
                    'Manufacturer nominal optical frames are not measured G1 extrinsics or calibrated camera intrinsics.',
                    'D405 depth capability does not add wrist depth to the selected actor channels.',
                    'D455 source STL has open edges; it remains a visual mesh, not a qualified closed collision or inertial model.'])
    write_json(HERE/'model.json',out)
    print(json.dumps({'camera_types':len(records),'instances_selected':3,'installed':0}))


if __name__=='__main__':build()
