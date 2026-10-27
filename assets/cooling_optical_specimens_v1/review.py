"""Review exported witness assembly surfaces and explicitly intended contacts."""
import hashlib,json
from pathlib import Path
import cadquery as cq
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent


def review():
    records=[];solids={p.stem:cq.importers.importStep(str(p)) for p in sorted((HERE/'design').glob('*.step'))};cad_review=[]
    for i,a in enumerate(solids):
        for b in list(solids)[i+1:]:
            overlap=solids[a].intersect(solids[b]);volume=sum(s.Volume() for s in overlap.solids().vals())*1e-9
            cad_review.append(dict(pair=[a,b],intersection_volume_m3=volume,passed=volume<1e-15))
    assert len(cad_review)==55
    for kind in ['white','black']:
        path=HERE/('witness_'+kind+'.glb');scene=trimesh.load(path,force='scene',process=False)
        manager=trimesh.collision.CollisionManager();bounds={}
        for name in scene.graph.nodes_geometry:
            transform,key=scene.graph[name];mesh=scene.geometry[key].copy();mesh.apply_transform(transform)
            manager.add_object(name,mesh);bounds[name]=mesh.bounds.tolist()
        _,pairs,contacts=manager.in_collision_internal(return_names=True,return_data=True)
        expected={frozenset(['annular_carrier','copper_witness']),frozenset(['copper_witness','paint_coat_3']),frozenset(['paint_coat_1','paint_coat_2']),frozenset(['paint_coat_2','paint_coat_3'])}
        for angle in [0,120,240]:
            expected.update([frozenset(['spring_clip_'+str(angle),'copper_witness']),frozenset(['spring_clip_'+str(angle),'annular_carrier']),frozenset(['retainer_screw_'+str(angle),'spring_clip_'+str(angle)])])
        checked=[]
        for a,b in sorted(pairs):
            matches=[c for c in contacts if c.names=={a,b}];depth=max(float(c.depth) for c in matches)
            exact=next(r for r in cad_review if set(r['pair'])=={a,b})
            # FCL triangle contact depths at coplanar clip/carrier surfaces can
            # span the full triangle. Use independently reloaded STEP solids
            # to distinguish intended tangency from positive-volume overlap.
            checked.append(dict(pair=[a,b],fcl_reported_depth_m=depth,exact_intersection_volume_m3=exact['intersection_volume_m3'],intended_surface_contact=frozenset([a,b]) in expected and exact['passed'],mesh_depth_is_not_a_solid_penetration_measure=depth>=1e-7))
        records.append(dict(id=kind,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bounds_m=bounds,contacts=checked,passed=all(c['intended_surface_contact'] for c in checked)))
    output=dict(scope=__doc__,passed=all(r['passed'] for r in records) and all(r['passed'] for r in cad_review),records=records,design_solid_pairs=cad_review,design_solid_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'design').glob('*.step'))},intersection_volume_tolerance_m3=1e-15,reviewer_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits='Assembly geometry only; no force, tolerancing, optical performance, manufacturability or fastener qualification. STEP solids distinguish CAD tangency from ambiguous FCL triangle depths.')
    (HERE/'assembly_review.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output))


if __name__=='__main__':review()
