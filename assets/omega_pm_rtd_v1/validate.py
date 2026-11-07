"""Measure the exported asset and its declared cable rest shape."""
from pathlib import Path
import hashlib
import json
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent


def main():
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    scene=trimesh.load(HERE/'geometry/omega_pm_rtd.glb',force='scene')
    meshes={}
    for node in scene.graph.nodes_geometry:
        matrix,geometry=scene.graph[node];mesh=scene.geometry[geometry].copy();mesh.apply_transform(matrix)
        # glTF +Y up back to Blender +Z up.
        mesh.vertices=np.asarray(mesh.vertices)@np.array([[1,0,0],[0,0,1],[0,-1,0]])
        meshes[node]=mesh
    rows=[]
    def check(name,passed,**values):rows.append(dict(name=name,passed=bool(passed),**values))
    declared={p['id'] for p in json.loads((HERE/'parts.json').read_text())}
    check('all_declared_parts_exported',declared==set(meshes),missing=sorted(declared-set(meshes)),unexpected=sorted(set(meshes)-declared))
    sheath=meshes['immersion_sheath'];extent=sheath.extents
    check('exported_probe_dimensions',np.max(np.abs(extent-[.0762,.00635,.00635]))<2e-6,measured_m=extent.tolist())
    check('tip_datum',abs(sheath.bounds[0,0])<1e-6,minimum_x_m=float(sheath.bounds[0,0]))
    interfaces=json.loads((HERE/'interfaces.json').read_text());cable=np.array(interfaces['cable']['rest_points_m'])
    length=float(np.linalg.norm(np.diff(cable,axis=0),axis=1).sum())+.08
    check('12_foot_cable_centerline',abs(length-3.6576)<.001,length_m=length)
    ends=np.array([p['position_m'] for p in interfaces['terminals']])
    distances=np.linalg.norm(ends[:,None,:]-ends[None,:,:],axis=-1);distances+=np.eye(4)
    check('four_distinct_stripped_leads',len([n for n in meshes if n.startswith('stripped_')])==4 and distances.min()>.005,
          minimum_tip_spacing_m=float(distances.min()))
    # Neighbouring turns are 4.5 mm apart for a selected 4 mm cable.
    points_per_turn=(len(cable)-2)/((3.5776-(.20-.1222))/np.hypot(2*np.pi*.065,.0045))
    interval=round(points_per_turn);turn_clearance=np.linalg.norm(cable[2+interval:]-cable[2:-interval],axis=1).min()
    check('coiled_jacket_turn_clearance',turn_clearance>.004,centerline_clearance_m=float(turn_clearance))
    receipt=json.loads((HERE/'build_receipt.json').read_text())
    check('builder_and_sources_pinned',receipt['builder_sha256']==sha(HERE/'build.py') and receipt['source_sha256']==sha(HERE/'sources.json'))
    check('geometry_hashes',all(sha(HERE/p)==s for p,s in receipt['artifacts_sha256'].items()))
    result=dict(passed=all(c['passed'] for c in rows),checks=rows,validator_sha256=sha(Path(__file__)),
                glb_sha256=sha(HERE/'geometry/omega_pm_rtd.glb'),contact_qualified=False,
                scope='Exported dimensions, cable rest-shape length and topology; fitting is inferred, no cable dynamics or threaded mating validation')
    (HERE/'geometry_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    return result['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
