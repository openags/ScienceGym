"""Independent bounded source, mesh and kinematic-tree inspection.

These checks deliberately do not assert physical hand or grasp qualification.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    model=json.loads((HERE/'model.json').read_text());checks=[];measurements=[]
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
        if not passed:raise AssertionError(name)
    check('source_record_pinned',model['source_record_sha256']==sha(HERE/'sources.json'))
    check('builder_pinned',model['builder_sha256']==sha(HERE/'build.py'))
    check('no_physics_or_vendor_claim',not model['official_cad'] and not model['dynamics_qualified'] and not model['kinematics_qualified'] and model['h2_mount_transform'] is None)
    for hand in model['hands']:
        side=hand['id'];s=trimesh.load(ROOT/hand['path'],force='scene');k=json.loads((ROOT/hand['kinematics']).read_text())
        check(side+'_mesh_identity',sha(ROOT/hand['path'])==hand['sha256'])
        check(side+'_kinematics_identity',sha(ROOT/hand['kinematics'])==hand['kinematics_sha256'])
        check(side+'_dimensions',np.allclose(s.extents,[.102,.026,.187],atol=.0005))
        measurements.append(dict(side=side,extents_m=s.extents.tolist(),tolerance_m=.0005,meaning='Agreement with selected outer envelope only; local geometry remains inferred'))
        check(side+'_parts_complete',set(s.graph.nodes_geometry)==set(k['part_links']))
        check(side+'_finite_meshes',all(np.isfinite(m.vertices).all() and len(m.faces)>0 for m in s.geometry.values()))
        check(side+'_closed_surface_parts',all(m.is_watertight for m in s.geometry.values()))
        seen={'palm'}
        for j in k['joints']:
            check(side+'_tree_'+j['id'],j['parent'] in seen and j['id'] not in seen and np.isclose(np.linalg.norm(j['axis']),1))
            seen.add(j['id'])
        check(side+'_all_links_resolved',set(k['part_links'].values())<=seen)
        check(side+'_per_finger_count',all(sum(j['id'].startswith(f+'_') for j in k['joints'])==count for f,count in [('thumb',5),('index',4),('middle',4),('ring',4),('pinky',5)]))
        check(side+'_unknown_limits_remain_unknown',all(j['measured_limits_rad'] is None and j['effort_limit_Nm'] is None for j in k['joints']))
        # Check independently accumulated rest origins, not just JSON counts.
        origins={'palm':np.zeros(3)}
        for j in k['joints']:
            origins[j['id']]=origins[j['parent']]+j['origin_m']
            check(side+'_rest_origin_'+j['id'],np.allclose(np.array(k['bind_world'][j['id']])[:3,3],origins[j['id']]))
    record=dict(passed=True,checks=checks,measurements=measurements,model_sha256=sha(HERE/'model.json'),validator_sha256=sha(Path(__file__)),
      scope='Outer envelope, finite closed part meshes, declared topology and provenance only; no local-fidelity, self-contact, dynamics or integration acceptance')
    (HERE/'VERIFICATION.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(checks),'measurements':measurements}))

if __name__=='__main__':main()
