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
    original.geometry[key]=mesh;out=OUT/'prepared_cary_candidate.glb';out.write_bytes(original.export(file_type='glb'))
    reread=trimesh.load(out,force='scene',process=False);errors={}
    for n,a in before.items():
        if n==name:continue
        m,k=reread.graph[n];b=trimesh.transform_points(reread.geometry[k].vertices,m);assert a.shape==b.shape;errors[n]=float(np.max(abs(a-b)))
    assert max(errors.values())<1e-6
    report=dict(scope=__doc__,status='candidate_not_integrated',manufacturer_CAD=False,source='https://mmrc.caltech.edu/Cary%20UV-Vis%20Int.Sphere/manuals/Cary%20manuals/4000_6000i_extended_sample_compartment.pdf',source_geometry=str(source.relative_to(ROOT)),source_geometry_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),geometry=str(out.relative_to(ROOT)),geometry_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),preserved_other_parts=len(errors),maximum_other_vertex_error_m=max(errors.values()),selected_relief_radius_m=.0046,retained_fitting_outer_radius_m=.004,relief_centers_relative_to_extension_origin_m=[[-.05,-.088,.015],[.05,-.088,.015]],source_sha256={n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ['build_cary_cover_clearance.py','cary_clamp.py']},remaining=['Review complete cover-removal and return path','Robot support, release, grasp forces and repeated execution'])
    (OUT/'revision.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':main()
