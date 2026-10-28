"""Reconstruct open-bottom cover clearances around the retained hose barbs.

The source asset's solid front skirt intersects its two base hose fittings.
The manual describes a separately removable cover and retained base fittings.
The two U-shaped reliefs below are an explicitly inferred mechanical detail;
they do not change the 154 x 170 x 212 mm internal envelope or handle.
"""
import hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np,trimesh
from cary_clamp import solid_mesh
from source_geometry import ROOT,ASSETS

HERE=Path(__file__).resolve().parent
OUT=ROOT/'assets/cary_5000_v1/revisions/cover_clearance'


def main():
    OUT.mkdir(parents=True,exist_ok=True);asset=ASSETS['cary'];source=ROOT/asset['geometry']
    original=trimesh.load(source,force='scene',process=False)
    before={n:trimesh.transform_points(original.geometry[original.graph[n][1]].vertices,original.graph[n][0]) for n in original.graph.nodes_geometry}
    plate=cq.Workplane('XY').box(158,4,212).edges('|Z').fillet(.5).translate((0,-88,112)).val()
    for x in [-50,50]:
        rounded=cq.Solid.makeCylinder(4.6,20,cq.Vector(x,-98,15),cq.Vector(0,1,0))
        slot=cq.Workplane('XY').box(9.2,20,30).translate((x,-88,0)).val()
        plate=plate.cut(rounded.fuse(slot)).clean()
    mesh=solid_mesh(plate);assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0
    name='extension_cover_front';node,key=original.graph[name]
    mesh.visual=trimesh.visual.TextureVisuals(material=original.geometry[key].visual.material.copy())
    interfaces=json.loads((ROOT/'assets/cary_5000_v1/interfaces.json').read_text());datum=np.eye(4);datum[:3,3]=interfaces['extension']['presentation_origin_m']
    mesh.apply_transform(np.linalg.inv(node)@np.array(asset['normalization_matrix'])@datum)
    original.geometry[key]=mesh
    # The schematic shows an exposed grip above the cover. The previous
    # unmeasured reconstruction left only 4 mm below the bar, insufficient
    # for an ordinary finger wrap. Select 20 mm clear space; this is an
    # ergonomic reconstruction, not a manufacturer dimension or robot fixture.
    changed={name,'extension_pull_bar','extension_pull_post_-0.037','extension_pull_post_0.037'}
    normal=np.array(asset['normalization_matrix'])
    for n in changed-{name}:
        node,key=original.graph[n]
        if n=='extension_pull_bar':
            m=original.geometry[key].copy();up=np.eye(4);up[2,3]=.016
            m.apply_transform(np.linalg.inv(node)@normal@up@np.linalg.inv(normal)@node)
        else:
            x=float(n.split('_')[-1]);old=np.eye(4);old[:3,3]=[x,-.008,.226]
            new=np.eye(4);new[:3,3]=[x,-.008,.233];scale=np.diag([1,1,22/8,1])
            m=original.geometry[key].copy()
            m.apply_transform(np.linalg.inv(node)@normal@datum@new@scale@np.linalg.inv(old)@np.linalg.inv(datum)@np.linalg.inv(normal)@node)
        original.geometry[key]=m
    out=OUT/'prepared_cary_operable_cover.glb';out.write_bytes(original.export(file_type='glb'))
    reread=trimesh.load(out,force='scene',process=False);errors={}
    for n,a in before.items():
        if n in changed:continue
        m,k=reread.graph[n];b=trimesh.transform_points(reread.geometry[k].vertices,m);assert a.shape==b.shape;errors[n]=float(np.max(abs(a-b)))
    assert max(errors.values())<1e-6
    report=dict(scope=__doc__,status='candidate_not_integrated',manufacturer_CAD=False,source='https://mmrc.caltech.edu/Cary%20UV-Vis%20Int.Sphere/manuals/Cary%20manuals/4000_6000i_extended_sample_compartment.pdf',source_geometry=str(source.relative_to(ROOT)),source_geometry_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),geometry=str(out.relative_to(ROOT)),geometry_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),preserved_other_parts=len(errors),maximum_other_vertex_error_m=max(errors.values()),selected_relief_radius_m=.0046,retained_fitting_outer_radius_m=.004,relief_centers_relative_to_extension_origin_m=[[-.05,-.088,.015],[.05,-.088,.015]],source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['build_cary_cover_clearance.py','cary_clamp.py']},remaining=['Review complete cover-removal and return path','Robot support, release, grasp forces and repeated execution'])
    report['selected_handle_clearance_m']=.020
    report['handle_clearance_is_inferred']=True
    report['changed_parts']=sorted(changed)
    report['front_skirt_edge_treatment']='Preserve 0.5 mm vertical corner rounding; horizontal edge rounds omitted after tessellation of the reliefs.'
    (OUT/'operable_revision.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
