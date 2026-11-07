"""Inspect exported geometry, including bore rays and manufacturer envelope."""
import json
import hashlib
from pathlib import Path
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent


def ray(triangles,origin,direction):
    e1=triangles[:,1]-triangles[:,0];e2=triangles[:,2]-triangles[:,0]
    h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
    valid=np.abs(det)>1e-12;f=np.zeros_like(det);f[valid]=1/det[valid]
    s=origin-triangles[:,0];u=f*np.einsum('ij,ij->i',s,h)
    q=np.cross(s,e1);v=f*(q@direction);t=f*np.einsum('ij,ij->i',e2,q)
    hit=valid&(u>=0)&(v>=0)&(u+v<=1)&(t>1e-7)
    return float(t[hit].min()) if hit.any() else None


def gltf(v):return np.array([v[0],v[2],-v[1]])


def main():
    scene=trimesh.load(HERE/'geometry/keithley_2425.glb',force='scene')
    mesh=scene.to_geometry();tri=mesh.triangles
    extents=scene.extents[[0,2,1]]
    expected=np.array([.238,.370,.104]);error=np.abs(extents-expected)
    checks=[dict(case='published_bench_envelope',passed=bool(np.all(error<.001)),
                 observed_WDH_m=extents.tolist(),expected_WDH_m=expected.tolist(),tolerance_m=.001)]
    declared={p['id'] for p in json.loads((HERE/'parts.json').read_text())}
    exported=set(scene.graph.nodes_geometry)
    checks.append(dict(case='all_declared_parts_exported',passed=declared==exported,
                       missing=sorted(declared-exported),unexpected=sorted(exported-declared)))
    interfaces=json.loads((HERE/'interfaces.json').read_text())['interfaces']
    sockets=[x for x in interfaces if x['kind']=='banana_socket']
    checks.append(dict(case='ten_distinct_banana_sockets',passed=len(sockets)==10 and len({x['id'] for x in sockets})==10))
    for socket in sockets:
        axis=gltf(socket['axis']);origin=gltf(socket['entry_m'])-axis*.001
        center=ray(tri,origin,axis);wall=ray(tri,origin+[.004,0,0],axis)
        checks.append(dict(case=socket['id']+'_open_bore_and_rim',passed=bool((center is None or center>.013) and wall is not None and wall<.004),
                           center_first_hit_m=center,rim_first_hit_m=wall))
    receipt=json.loads((HERE/'build_receipt.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    checks.append(dict(case='built_from_current_source',passed=receipt['builder_sha256']==sha(HERE/'build.py')))
    report=dict(passed=all(x['passed'] for x in checks),checks=checks,
                input_sha256={str(p.relative_to(HERE)):sha(p) for p in [HERE/'build.py',HERE/'interfaces.json',HERE/'sources.json',HERE/'geometry/keithley_2425.glb']},
                scope='Exported envelope, identity count and open-bore topology; not connector tolerance, surface damage, electrical or robot execution qualification',whole_equipment_qualified=False)
    (HERE/'geometry_checks.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return report['passed']


if __name__=='__main__':raise SystemExit(0 if main() else 1)
