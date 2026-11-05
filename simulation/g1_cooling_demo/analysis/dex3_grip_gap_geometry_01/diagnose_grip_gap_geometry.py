"""Measure source-geometry separation around recorded missing finger contacts.

Offline attribution only. Restored states and triangle distances cannot qualify
a new grasp, policy, or continuous episode.
"""
import argparse
import json
from pathlib import Path
import shutil

import mujoco
import numpy as np

from diagnose_optical_tray_clearance import source_mesh, compare_meshes
from frozen_collision_plugins import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('diagnostic',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();run,diagnostic,out=[v.resolve() for v in [a.run,a.diagnostic,a.output]]
    contract=json.loads((run/'contract.json').read_text());result=json.loads((run/'result.json').read_text())
    review=json.loads((diagnostic/'review.json').read_text())
    assert review['complete'] and review['baseline_matches_recording']
    assert sha(run/'contract.json')==result['contract_sha256']==review['source_contract_sha256']
    assert sha(run/'world.xml')==contract['model_sha256']
    assert sha(run/'trace.npz')==result['trace_sha256']
    losses=review['cases'][0]['lost_steps'];selected=[]
    for finger in range(3):
        selected.append(next(r['time_s'] for r in losses if r['force_n'][finger]==0))
    with np.load(run/'trace.npz') as z:
        times=z['time'];indices=[]
        for t in selected:
            i=int(np.argmin(abs(times-t)));indices.extend([i-1,i,i+1])
        qpos=z['qpos'][indices].copy();sample_times=times[indices].copy()
    m=mujoco.MjModel.from_xml_path(str(run/'world.xml'));d=mujoco.MjData(m)
    tool={m.body('tweezer').id}
    for b in range(m.nbody):
        if m.body_parentid[b] in tool:tool.add(b)
    tool_geoms=[g for g in range(m.ngeom) if m.geom_bodyid[g] in tool and (m.geom_contype[g] or m.geom_conaffinity[g])]
    allowed=[m.body(n).id for n in contract['allowed_tool_contact_bodies']]
    rows=[]
    for ordinal,(q,t) in enumerate(zip(qpos,sample_times)):
        finger=ordinal//3;d.qpos[:]=q;mujoco.mj_forward(m,d)
        body=allowed[finger]
        own=[g for g in range(m.ngeom) if m.geom_bodyid[g]==body and (m.geom_contype[g] or m.geom_conaffinity[g])]
        pairs=[]
        for first in own:
            mesh=source_mesh(m,d,first)
            for second in tool_geoms:
                other=source_mesh(m,d,second)
                # An AABB lower bound safely discards only distant tool parts.
                gap=np.maximum(np.maximum(mesh.bounds[0]-other.bounds[1],other.bounds[0]-mesh.bounds[1]),0.)
                if np.linalg.norm(gap)>.001:continue
                source=compare_meshes(mesh,other)
                hull=compare_meshes(mesh.convex_hull,other.convex_hull)
                pairs.append(dict(parts=[m.geom(first).name,m.geom(second).name],source=source,hull=hull))
        row=dict(time_s=float(t),finger=contract['allowed_tool_contact_bodies'][finger],
            offset_from_loss_sample=ordinal%3-1,pairs=pairs)
        rows.append(row)
        print(json.dumps(dict(time_s=float(t),finger=row['finger'],offset=row['offset_from_loss_sample'],
            closest_source_m=min(v['source']['distance_m'] for v in pairs),
            closest_hull_m=min(v['hull']['distance_m'] for v in pairs),
            source_intersection=any(v['source']['intersects'] for v in pairs),
            hull_intersection=any(v['hull']['intersects'] for v in pairs))),flush=True)
    out.mkdir(parents=True,exist_ok=False)
    for name in [Path(__file__).name,'diagnose_optical_tray_clearance.py','frozen_collision_plugins.py']:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    report=dict(scope=__doc__,source_result_sha256=sha(run/'result.json'),
        collision_diagnostic_sha256=sha(diagnostic/'review.json'),rows=rows,
        source_sha256={p.name:sha(p) for p in out.glob('*.py')},qualified_carry=False)
    (out/'review.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
