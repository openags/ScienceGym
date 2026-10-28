"""Build and inspect an inferred protective-cap support geometry, off-scene.

The manufacturer establishes the existence of the cap, not these internal fit
dimensions. This candidate is not installed in the laboratory or qualified for
forces/stability. It preserves the reference's non-optical shoulder as support
and keeps its optical face clear of the cap floor.
"""
import hashlib,json
from pathlib import Path
import numpy as np
import trimesh
from scipy.spatial.transform import Rotation
from source_geometry import ROOT,ASSETS,hand_manager,set_hand

HERE=Path(__file__).resolve().parent


def cap_mesh():
    n=96;vertices=[]
    for radius,z in [(.028,0),(.028,.024),(.025,.024),(.025,.003)]:
        vertices.extend((radius*np.cos(2*np.pi*i/n),radius*np.sin(2*np.pi*i/n),z) for i in range(n))
    vertices.extend([(0,0,0),(0,0,.003)]);faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(4*n,j,i),(i,j,n+j),(i,n+j,n+i),
                      (n+i,n+j,2*n+j),(n+i,2*n+j,2*n+i),
                      (2*n+i,2*n+j,3*n+j),(2*n+i,3*n+j,3*n+i),
                      (4*n+1,3*n+i,3*n+j)])
    return trimesh.Trimesh(vertices=vertices,faces=faces,process=False)


def main():
    asset=ASSETS['pike'];original=trimesh.load(ROOT/asset['geometry'],force='scene',process=False)
    cap=cap_mesh();assert cap.is_watertight and cap.is_winding_consistent and cap.volume>0
    _,key=original.graph['reference_protective_cap'];cap.visual=trimesh.visual.TextureVisuals(material=original.geometry[key].visual.material.copy())
    support=np.eye(4);support[:3,:3]=Rotation.from_euler('x',np.pi).as_matrix()
    support[:3,3]=np.array([0,0,.024])-support[:3,:3]@np.array([.145,-.06,.031])
    normal=np.array(asset['normalization_matrix']);reference=trimesh.collision.CollisionManager()
    cap_manager=trimesh.collision.CollisionManager();cap_manager.add_object('inferred_protective_cap',cap)
    scene=trimesh.Scene();scene.add_geometry(cap,node_name='inferred_protective_cap');meshes={}
    for name in ['gold_reference_holder','gold_reference_shoulder','diffuse_gold_reference_face']:
        transform,key=original.graph[name];correction=np.eye(4)
        if name=='diffuse_gold_reference_face':correction[2,3]=-.00055
        placed=support@correction@np.linalg.inv(normal)@transform
        mesh=original.geometry[key].copy();mesh.apply_transform(placed);meshes[name]=mesh
        reference.add_object(name,mesh);scene.add_geometry(mesh,node_name=name)
    _,pairs,contacts=reference.in_collision_other(cap_manager,return_names=True,return_data=True)
    face_clearance=float(meshes['diffuse_gold_reference_face'].bounds[0,2]-.003)
    setup=json.loads((HERE/'optical_setup.json').read_text());grasp=json.loads((HERE/'reference_lift_path.json').read_text())['grasp']
    world=np.eye(4);world[:3,3]=asset['position_m']
    current=world@np.array(setup['parts']['pike']['gold_reference_holder']['matrix'])@normal
    delta=support@np.linalg.inv(current)
    palm=np.array(grasp['palm_matrix']);palm[:3,3]+=setup['ports']['ftir_sample']['position_m'];palm=delta@palm
    hand=hand_manager('left');closure=[]
    for fraction in np.linspace(0,1,51):
        q=dict(grasp['q'])
        for name in ['left_index_1_joint','left_thumb_2_joint']:q[name]*=float(fraction)
        set_hand(hand,'left',q,palm)
        _,cap_pairs=hand.in_collision_other(cap_manager,return_names=True)
        _,reference_pairs=hand.in_collision_other(reference,return_names=True)
        if cap_pairs or reference_pairs:closure.append(dict(fraction=float(fraction),cap_intersections=sorted(cap_pairs),reference_intersections=sorted(reference_pairs)))
    out=HERE/'previews/reference_cap_support_candidate.glb';out.write_bytes(scene.export(file_type='glb'))
    # Preserve the parent asset and export a separate complete-asset candidate.
    # Only the cap mesh changes; every other source part and node is retained.
    variant=ROOT/'assets/pike_integratir_dtgs_v1/revisions/cap_support';variant.mkdir(parents=True,exist_ok=True)
    before={name:(original.graph[name][0].copy(),original.geometry[original.graph[name][1]].vertices.copy()) for name in original.graph.nodes_geometry}
    cap_transform,cap_key=original.graph['reference_protective_cap']
    datum=np.eye(4);datum[:3,3]=[.210,-.060,.004]
    replacement=cap.copy();replacement.apply_transform(np.linalg.inv(cap_transform)@normal@datum)
    original.geometry[cap_key]=replacement
    variant_file=variant/'prepared_pike_candidate.glb';variant_file.write_bytes(original.export(file_type='glb'))
    reread=trimesh.load(variant_file,force='scene',process=False)
    assert set(reread.graph.nodes_geometry)==set(before)
    maximum_unchanged_error=0.
    for name,(transform,vertices) in before.items():
        if name=='reference_protective_cap':continue
        after,key=reread.graph[name]
        a=trimesh.transform_points(vertices,transform);b=trimesh.transform_points(reread.geometry[key].vertices,after)
        assert a.shape==b.shape
        maximum_unchanged_error=max(maximum_unchanged_error,float(np.abs(a-b).max()))
    assert maximum_unchanged_error<1e-6
    result=dict(scope=__doc__,status='candidate_not_integrated',manufacturer_CAD=False,
                source_manual='https://www.piketech.com/files/user-manuals/MidIntegratIRwDTGSManual.pdf',
                source_geometry_sha256=asset['geometry_sha256'],generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                inferred_cap=dict(outer_radius_m=.028,inside_radius_m=.025,height_m=.024,floor_thickness_m=.003),
                reference_cap_pairs=sorted(pairs),maximum_reported_reference_cap_depth_m=max((float(c.depth) for c in contacts),default=0),
                optical_face_clearance_above_cap_floor_m=face_clearance,closure_sample_count=51,closure_collision_samples=closure,
                palm_relative_to_cap_floor=palm.tolist(),candidate_glb_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),
                complete_asset_candidate=str(variant_file.relative_to(ROOT)),complete_asset_candidate_sha256=hashlib.sha256(variant_file.read_bytes()).hexdigest(),
                unchanged_source_part_count=len(before)-1,maximum_unchanged_source_vertex_error_m=maximum_unchanged_error,
                remaining=['Manufacturer internal fit unreported; dimensions are inferred','Whole-body approach, carrying step, insertion, release and return','Support/load stability and contamination qualification'])
    (HERE/'previews/reference_cap_support_review.json').write_text(json.dumps(result,indent=2)+'\n')
    (variant/'revision.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['closure_collision_samples','palm_relative_to_cap_floor']}),flush=True)
    print('closure_collision_samples',len(closure),flush=True)


if __name__=='__main__':main()
